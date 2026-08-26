"""不可变推演会话模块。

铁律：原始排盘、卦盘、干支、用神、动爻一经生成永久固定，
绝不因用户反馈、主观修改或现实不符而改动。仅可调整事理翻译与解读视角。
"""

from .models import (
    DivinationSession,
    DivinationSnapshot,
    InteractionRecord,
    SESSION_STATUSES,
    INTERACTION_TYPES,
    create_session,
    freeze_snapshot,
    append_interaction,
)
from .store import SessionStore, get_store

__all__ = [
    "DivinationSession",
    "DivinationSnapshot",
    "InteractionRecord",
    "SESSION_STATUSES",
    "INTERACTION_TYPES",
    "create_session",
    "freeze_snapshot",
    "append_interaction",
    "SessionStore",
    "get_store",
]
