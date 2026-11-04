"""风水房屋档案存储层：租户隔离、可插拔后端（文件 / PostgreSQL）。

合规要点：
- 档案只存坐向测量事实与屋宅描述，不收集身份证明类个人信息；
- tenant_id 必填，所有读写按租户分域（文件后端按租户子目录，PostgreSQL 后端按行级 tenant_id 过滤）；
- 采集须记录 owner_consent（屋主知情同意）与 source（测量方式），缺失即拒绝写入；
- PostgreSQL DDL 见 scripts/sql/fengshui_building_profiles.sql，通过 FENGSHUI_STORAGE=postgres
  与 FENGSHUI_PG_DSN 启用；默认文件后端，无需数据库即可运行。
"""

import json
import os
import re
import tempfile
import threading
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_FILE_ROOT = Path(__file__).resolve().parents[3] / "data" / "fengshui" / "buildings"

TENANT_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
BUILDING_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

REQUIRED_FIELDS = ("name", "measurements", "owner_consent", "source")
MAX_PROFILE_BYTES = 64 * 1024
# 所有后端统一返回 make_record 生成的 DTO，切换 FENGSHUI_STORAGE 不改变 API 契约。

_write_lock = threading.Lock()


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_identifier(value, kind):
    pattern = TENANT_PATTERN if kind == "tenant" else BUILDING_PATTERN
    if not isinstance(value, str) or not pattern.match(value):
        raise ValueError("{} must match ^[A-Za-z0-9_-]{{1,64}}$".format(kind))
    return value


def resolve_tenant(tenant_id):
    """解析租户：部署了 FENGSHUI_TENANT_ID 时强制绑定，忽略客户端声明。

    单 token 部署下客户端可自行声明 tenant_id，无法据此做身份隔离；
    设置该环境变量后所有读写都锁定到服务端租户，关闭跨租户越权窗口。
    """
    bound = os.environ.get("FENGSHUI_TENANT_ID")
    if bound:
        return validate_identifier(bound, "tenant")
    return validate_identifier(tenant_id, "tenant")


def validate_profile(payload):
    if not isinstance(payload, dict):
        raise ValueError("profile must be an object")
    for field in REQUIRED_FIELDS:
        if field not in payload:
            raise ValueError("profile missing required field: {}".format(field))
    if payload["owner_consent"] is not True:
        raise ValueError("owner_consent is required: 档案采集须记录屋主知情同意（布尔真值）")
    if not isinstance(payload["source"], str) or not payload["source"].strip():
        raise ValueError("source is required: 档案采集须记录测量方式")
    if len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > MAX_PROFILE_BYTES:
        raise ValueError("profile exceeds {} bytes".format(MAX_PROFILE_BYTES))
    measurements = payload["measurements"]
    if not isinstance(measurements, list) or not measurements:
        raise ValueError("measurements must be a non-empty list")
    for row in measurements:
        if not isinstance(row, dict) or "facing_degree" not in row:
            raise ValueError("each measurement needs facing_degree")
        degree = row["facing_degree"]
        if isinstance(degree, bool) or not isinstance(degree, (int, float)) or not 0 <= degree <= 360:
            raise ValueError("facing_degree must be a number between 0 and 360")
    return payload


def make_record(tenant_id, building_id, profile, created_at=None, updated_at=None):
    """构造统一返回结构（两个后端共用）。"""
    now = utc_now()
    return {
        "schema_version": "1.0",
        "tenant_id": tenant_id,
        "building_id": building_id,
        "created_at": created_at or now,
        "updated_at": updated_at or now,
        "profile": profile,
    }


class FileBackend:
    """文件后端：data/fengshui/buildings/<tenant>/<building>.json。"""

    def __init__(self, root=None):
        self.root = Path(root or os.environ.get("FENGSHUI_FILE_ROOT", DEFAULT_FILE_ROOT))

    def _path(self, tenant_id, building_id):
        return self.root / tenant_id / "{}.json".format(building_id)

    def upsert(self, tenant_id, building_id, profile):
        path = self._path(tenant_id, building_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with _write_lock:
            existing = {}
            if path.exists():
                existing = json.loads(path.read_text(encoding="utf-8"))
            record = make_record(tenant_id, building_id, profile,
                                 created_at=existing.get("created_at"))
            handle, tmp_name = tempfile.mkstemp(prefix=".building-", suffix=".tmp", dir=str(path.parent))
            try:
                with os.fdopen(handle, "w", encoding="utf-8") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False, indent=2))
                os.replace(tmp_name, path)
            except BaseException:
                if os.path.exists(tmp_name):
                    os.unlink(tmp_name)
                raise
        return record

    def get(self, tenant_id, building_id):
        path = self._path(tenant_id, building_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def list(self, tenant_id):
        directory = self.root / tenant_id
        if not directory.exists():
            return []
        rows = []
        for path in sorted(directory.glob("*.json")):
            rows.append(json.loads(path.read_text(encoding="utf-8")))
        return rows

    def delete(self, tenant_id, building_id):
        path = self._path(tenant_id, building_id)
        if path.exists():
            path.unlink()
            return True
        return False


class PostgresBackend:
    """PostgreSQL 后端：需要 FENGSHUI_PG_DSN；行级 tenant_id 过滤。"""

    def __init__(self, dsn):
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError as exc:
            raise RuntimeError("postgres backend requires psycopg2: pip install psycopg2-binary") from exc
        self._psycopg2 = psycopg2
        self._extras = psycopg2.extras
        self._dsn = dsn

    def _connection(self):
        return self._psycopg2.connect(self._dsn)

    def _execute(self, statement, parameters, fetch=False):
        # psycopg2 的 `with connection` 只管事务，不关闭连接；必须显式 closing
        with closing(self._connection()) as connection:
            with connection:
                with connection.cursor(cursor_factory=self._extras.RealDictCursor) as cursor:
                    cursor.execute(statement, parameters)
                    return cursor.fetchall() if fetch else None

    @staticmethod
    def _timestamp(value):
        return value.isoformat() if hasattr(value, "isoformat") else str(value)

    def _record_from_row(self, tenant_id, building_id, profile, row):
        if isinstance(profile, str):
            profile = json.loads(profile)
        return make_record(tenant_id, building_id, profile,
                           created_at=self._timestamp(row["created_at"]),
                           updated_at=self._timestamp(row["updated_at"]))

    def upsert(self, tenant_id, building_id, profile):
        rows = self._execute(
            """
            INSERT INTO fengshui_building_profiles
                (tenant_id, building_id, name, profile, owner_consent, updated_at)
            VALUES (%(tenant)s, %(building)s, %(name)s, %(profile)s, %(consent)s, NOW())
            ON CONFLICT (tenant_id, building_id) DO UPDATE SET
                name = EXCLUDED.name,
                profile = EXCLUDED.profile,
                owner_consent = EXCLUDED.owner_consent,
                updated_at = NOW()
            RETURNING created_at, updated_at
            """,
            {"tenant": tenant_id, "building": building_id, "name": str(profile.get("name", "")),
             "profile": json.dumps(profile, ensure_ascii=False), "consent": bool(profile.get("owner_consent"))},
            fetch=True,
        )
        return self._record_from_row(tenant_id, building_id, profile, rows[0]) if rows else None

    def get(self, tenant_id, building_id):
        rows = self._execute(
            """SELECT profile, created_at, updated_at FROM fengshui_building_profiles
               WHERE tenant_id=%s AND building_id=%s""",
            (tenant_id, building_id), fetch=True,
        )
        return self._record_from_row(tenant_id, building_id, rows[0]["profile"], rows[0]) if rows else None

    def list(self, tenant_id):
        rows = self._execute(
            """SELECT building_id, profile, created_at, updated_at FROM fengshui_building_profiles
               WHERE tenant_id=%s ORDER BY updated_at DESC""",
            (tenant_id,), fetch=True,
        )
        return [self._record_from_row(tenant_id, row["building_id"], row["profile"], row) for row in rows]

    def delete(self, tenant_id, building_id):
        rows = self._execute(
            "DELETE FROM fengshui_building_profiles WHERE tenant_id=%s AND building_id=%s RETURNING 1",
            (tenant_id, building_id), fetch=True,
        )
        return bool(rows)


_lock = threading.Lock()
_backend = None


def get_backend():
    global _backend
    with _lock:
        if _backend is not None:
            return _backend
        if os.environ.get("FENGSHUI_STORAGE", "file") == "postgres":
            dsn = os.environ.get("FENGSHUI_PG_DSN")
            if not dsn:
                raise RuntimeError("FENGSHUI_PG_DSN is required when FENGSHUI_STORAGE=postgres")
            _backend = PostgresBackend(dsn)
        else:
            _backend = FileBackend()
        return _backend


def reset_backend():
    global _backend
    with _lock:
        _backend = None


def upsert_profile(tenant_id, building_id, payload):
    tenant_id = resolve_tenant(tenant_id)
    building_id = validate_identifier(building_id, "building")
    payload = validate_profile(payload)
    return get_backend().upsert(tenant_id, building_id, payload)


def get_profile(tenant_id, building_id):
    tenant_id = resolve_tenant(tenant_id)
    building_id = validate_identifier(building_id, "building")
    return get_backend().get(tenant_id, building_id)


def list_profiles(tenant_id):
    tenant_id = resolve_tenant(tenant_id)
    return get_backend().list(tenant_id)


def delete_profile(tenant_id, building_id):
    tenant_id = resolve_tenant(tenant_id)
    building_id = validate_identifier(building_id, "building")
    return get_backend().delete(tenant_id, building_id)
