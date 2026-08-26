"""推演会话持久化存储（JSON 文件-based，MVP 阶段）。

生产环境可替换为 PostgreSQL / ClickHouse，接口保持不变。
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from .models import DivinationSession


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

    def _path(self, session_id: str) -> Path:
        safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
        return self.storage_dir / f"{safe_id}.json"

    def save(self, session: DivinationSession) -> None:
        path = self._path(session.session_id)
        with path.open("w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, ensure_ascii=False, indent=2)

    def load(self, session_id: str) -> Optional[DivinationSession]:
        path = self._path(session_id)
        if not path.is_file():
            return None
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return DivinationSession.from_dict(data)

    def list_sessions(self, limit: int = 50) -> list:
        sessions = []
        for path in sorted(self.storage_dir.glob("sess_*.json"), reverse=True):
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append({
                    "session_id": data.get("session_id"),
                    "question": data.get("question"),
                    "category": data.get("category"),
                    "status": data.get("status"),
                    "system": data.get("system"),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                })
                if len(sessions) >= limit:
                    break
            except (json.JSONDecodeError, OSError):
                continue
        return sessions

    def delete(self, session_id: str) -> bool:
        path = self._path(session_id)
        if path.is_file():
            path.unlink()
            return True
        return False


# 全局单例
_store: Optional[SessionStore] = None


def get_store() -> SessionStore:
    global _store
    if _store is None:
        _store = SessionStore()
    return _store
