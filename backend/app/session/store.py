"""推演会话持久化存储（JSON 文件-based，MVP 阶段）。

生产环境可替换为 PostgreSQL / ClickHouse，接口保持不变。
"""

import json
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

from .models import DivinationSession


logger = logging.getLogger("destiny.session.store")

# 会话 ID 只允许固定前缀 + 安全字符，且必须完整匹配。
# 之前用字符过滤拼路径，`a/b` 与 `ab` 会落到同一个文件名，属于静默串号。
SESSION_ID_PATTERN = re.compile(r"^sess_[A-Za-z0-9_-]{1,64}$")


def _validate_session_id(session_id: str) -> str:
    if not isinstance(session_id, str) or not SESSION_ID_PATTERN.match(session_id):
        raise ValueError("invalid session_id")
    return session_id


class SessionStore:
    """会话存储。基于 JSON 文件，每个会话一个文件。"""

    def __init__(self, storage_dir: Optional[str] = None):
        if storage_dir is None:
            storage_dir = os.environ.get(
                "SESSION_STORAGE_DIR",
                str(Path(__file__).resolve().parents[3] / "data" / "sessions"),
            )
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._meta_cache = {}

    def _path(self, session_id: str) -> Path:
        return self.storage_dir / "{}.json".format(_validate_session_id(session_id))

    def save(self, session: DivinationSession) -> None:
        """原子写入：先写同目录临时文件再 rename，避免进程中断留下半个 JSON。"""
        path = self._path(session.session_id)
        payload = json.dumps(session.to_dict(), ensure_ascii=False, separators=(",", ":"))
        fd, temp_name = tempfile.mkstemp(dir=str(self.storage_dir), prefix=".tmp_", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
            os.replace(temp_name, path)
        except BaseException:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise

    def load(self, session_id: str) -> Optional[DivinationSession]:
        try:
            path = self._path(session_id)
        except ValueError:
            # 非法 ID 不可能对应真实会话，按「查无此会话」处理，避免路径穿越
            return None
        if not path.is_file():
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (json.JSONDecodeError, OSError) as exc:
            # 单个会话文件损坏不应让整条链路 500，也不应静默当成「不存在」
            logger.error("session file unreadable: %s (%s)", path.name, exc)
            return None
        return DivinationSession.from_dict(data)

    def list_sessions(self, limit: int = 50) -> list:
        """列出会话元信息。

        会话文件里含完整快照与工作流结果（单个可达数百 KB），每次请求全部
        `json.load` 是纯粹的浪费。这里按 (mtime, size) 缓存元数据，
        文件没变就直接复用，文件被改写才重新解析。
        """
        sessions = []
        for path in sorted(self.storage_dir.glob("sess_*.json"), reverse=True):
            try:
                stat = path.stat()
            except OSError as exc:
                logger.warning("skip unreadable session file: %s (%s)", path.name, exc)
                continue
            cache_key = (path.name, stat.st_mtime_ns, stat.st_size)
            meta = self._meta_cache.get(cache_key)
            if meta is None:
                try:
                    with path.open("r", encoding="utf-8") as handle:
                        data = json.load(handle)
                except (json.JSONDecodeError, OSError) as exc:
                    logger.warning("skip unreadable session file: %s (%s)", path.name, exc)
                    continue
                if not isinstance(data, dict):
                    logger.warning("skip non-object session file: %s", path.name)
                    continue
                meta = {
                    "session_id": data.get("session_id"),
                    "question": data.get("question"),
                    "category": data.get("category"),
                    "status": data.get("status"),
                    "system": data.get("system"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                }
                self._meta_cache[cache_key] = meta
                # 同一会话被改写后旧指纹失效，避免缓存无限增长
                for stale in [key for key in self._meta_cache if key[0] == path.name and key != cache_key]:
                    self._meta_cache.pop(stale, None)
            sessions.append(dict(meta))
            if len(sessions) >= limit:
                break
        return sessions

    def delete(self, session_id: str) -> bool:
        try:
            path = self._path(session_id)
        except ValueError:
            return False
        if path.is_file():
            path.unlink()
            for stale in [key for key in self._meta_cache if key[0] == path.name]:
                self._meta_cache.pop(stale, None)
            return True
        return False


# 全局单例
_store: Optional[SessionStore] = None


def get_store() -> SessionStore:
    global _store
    if _store is None:
        _store = SessionStore()
    return _store
