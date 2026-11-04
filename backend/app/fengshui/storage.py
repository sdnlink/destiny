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
import threading
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_FILE_ROOT = Path(__file__).resolve().parents[3] / "data" / "fengshui" / "buildings"

TENANT_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
BUILDING_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

REQUIRED_FIELDS = ("name", "measurements", "owner_consent")

DDL = """
CREATE TABLE IF NOT EXISTS fengshui_building_profiles (
    tenant_id      VARCHAR(64)  NOT NULL,
    building_id    VARCHAR(64)  NOT NULL,
    name           VARCHAR(128) NOT NULL,
    profile        JSONB        NOT NULL,
    owner_consent  BOOLEAN      NOT NULL DEFAULT FALSE,
    data_classification VARCHAR(32) NOT NULL DEFAULT 'residential',
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, building_id)
);
CREATE INDEX IF NOT EXISTS idx_fengshui_profiles_tenant
    ON fengshui_building_profiles (tenant_id, updated_at DESC);
"""


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def validate_identifier(value, kind):
    pattern = TENANT_PATTERN if kind == "tenant" else BUILDING_PATTERN
    if not isinstance(value, str) or not pattern.match(value):
        raise ValueError("{} must match ^[A-Za-z0-9_-]{{1,64}}$".format(kind))
    return value


def validate_profile(payload):
    if not isinstance(payload, dict):
        raise ValueError("profile must be an object")
    for field in REQUIRED_FIELDS:
        if field not in payload:
            raise ValueError("profile missing required field: {}".format(field))
    if not payload.get("owner_consent"):
        raise ValueError("owner_consent is required: 档案采集须记录屋主知情同意")
    measurements = payload["measurements"]
    if not isinstance(measurements, list) or not measurements:
        raise ValueError("measurements must be a non-empty list")
    for row in measurements:
        if not isinstance(row, dict) or "facing_degree" not in row:
            raise ValueError("each measurement needs facing_degree")
    return payload


class FileBackend:
    """文件后端：data/fengshui/buildings/<tenant>/<building>.json。"""

    def __init__(self, root=None):
        self.root = Path(root or os.environ.get("FENGSHUI_FILE_ROOT", DEFAULT_FILE_ROOT))

    def _path(self, tenant_id, building_id):
        return self.root / tenant_id / "{}.json".format(building_id)

    def upsert(self, tenant_id, building_id, profile):
        path = self._path(tenant_id, building_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
        record = {
            "schema_version": "1.0",
            "tenant_id": tenant_id,
            "building_id": building_id,
            "created_at": existing.get("created_at", utc_now()),
            "updated_at": utc_now(),
            "profile": profile,
        }
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
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
        with self._connection() as connection:
            with connection.cursor(cursor_factory=self._extras.RealDictCursor) as cursor:
                cursor.execute(statement, parameters)
                return cursor.fetchall() if fetch else None

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
            RETURNING to_jsonb(fengshui_building_profiles) AS record
            """,
            {"tenant": tenant_id, "building": building_id, "name": str(profile.get("name", "")),
             "profile": json.dumps(profile, ensure_ascii=False), "consent": bool(profile.get("owner_consent"))},
            fetch=True,
        )
        return json.loads(rows[0]["record"]) if rows else None

    def get(self, tenant_id, building_id):
        rows = self._execute(
            "SELECT profile FROM fengshui_building_profiles WHERE tenant_id=%s AND building_id=%s",
            (tenant_id, building_id), fetch=True,
        )
        return rows[0]["profile"] if rows else None

    def list(self, tenant_id):
        rows = self._execute(
            "SELECT profile FROM fengshui_building_profiles WHERE tenant_id=%s ORDER BY updated_at DESC",
            (tenant_id,), fetch=True,
        )
        return [row["profile"] for row in rows]

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
    tenant_id = validate_identifier(tenant_id, "tenant")
    building_id = validate_identifier(building_id, "building")
    payload = validate_profile(payload)
    return get_backend().upsert(tenant_id, building_id, payload)


def get_profile(tenant_id, building_id):
    tenant_id = validate_identifier(tenant_id, "tenant")
    building_id = validate_identifier(building_id, "building")
    return get_backend().get(tenant_id, building_id)


def list_profiles(tenant_id):
    tenant_id = validate_identifier(tenant_id, "tenant")
    return get_backend().list(tenant_id)


def delete_profile(tenant_id, building_id):
    tenant_id = validate_identifier(tenant_id, "tenant")
    building_id = validate_identifier(building_id, "building")
    return get_backend().delete(tenant_id, building_id)
