"""不可变推演会话数据模型。

铁律：DivinationSnapshot 一旦冻结（frozen=True），其 raw_plate / module_results
等原始盘面数据永久不可修改。后续交互只能追加 InteractionRecord，
解读视角调整记录在 system_response 中，与原始盘面分离。
"""

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.common.hashing import canonical_hash


# 会话状态机：draft → casting → casted → interacting → reviewed
SESSION_STATUSES = ("draft", "casting", "casted", "interacting", "reviewed")

# 交互类型（对应模块A-G）。只登记 /v1/sessions/{id}/interact 实际分派处理的类型，
# 未实现的交互不再列入，避免出现「声明了但永远走不到」的枚举值。
INTERACTION_TYPES = (
    "info_completion",   # 模块A：起盘前信息补全
    "reality_check",     # 模块B：排盘后现实校验
    "multi_party",       # 模块E：多方人物取象
    "multi_choice",      # 模块F：多抉择分支推演
    "review",            # 模块G：事后复盘
    "deep_question",     # 深度追问（模块D②）
    "angle_shift",       # 换角度解读（模块D③）
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _canonical_hash(value: Any) -> str:
    return canonical_hash(value)


@dataclass
class DivinationSnapshot:
    """不可变排盘快照。写入即冻结，原始盘面数据永久不可修改。"""

    snapshot_id: str
    frozen: bool = True
    raw_plate: Dict[str, Any] = field(default_factory=dict)
    module_results: List[Dict[str, Any]] = field(default_factory=list)
    input_hash: str = ""
    rule_version: str = ""
    systems_used: List[str] = field(default_factory=list)
    casting_method: str = ""
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DivinationSnapshot":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class InteractionRecord:
    """交互记录。只追加，不修改历史记录。"""

    interaction_id: str
    type: str
    user_input: Dict[str, Any] = field(default_factory=dict)
    system_response: Dict[str, Any] = field(default_factory=dict)
    interpretation_shift: Optional[Dict[str, Any]] = None  # 解读视角调整（不改快照）
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DivinationSnapshot":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class DivinationSession:
    """推演会话。承载一次完整的求测→排盘→交互→复盘流程。"""

    session_id: str
    question: str = ""
    category: str = "other"
    system: str = "auto"  # auto / meihua / liuyao / qimen / daliuren
    casting_method: str = "auto"  # auto / time / numbers / manual / coins
    casting_source: Dict[str, Any] = field(default_factory=dict)
    user_profile: Dict[str, Any] = field(default_factory=dict)  # 性别/年龄/现状等
    # 会话归属（审计 22）：客户端 id 的哈希，空值表示迁移前的老会话，由首个访问者认领
    owner_hash: str = ""
    status: str = "draft"
    snapshot: Optional[DivinationSnapshot] = None
    interactions: List[InteractionRecord] = field(default_factory=list)
    workflow_result: Optional[Dict[str, Any]] = None  # 7步工作流输出
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.snapshot:
            data["snapshot"] = self.snapshot.to_dict()
        data["interactions"] = [i.to_dict() for i in self.interactions]
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DivinationSession":
        snapshot_data = data.get("snapshot")
        snapshot = DivinationSnapshot.from_dict(snapshot_data) if snapshot_data else None
        interactions = [
            InteractionRecord.from_dict(i) for i in data.get("interactions", [])
        ]
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        fields["snapshot"] = snapshot
        fields["interactions"] = interactions
        return cls(**fields)


def create_session(
    question: str,
    category: str = "other",
    system: str = "auto",
    casting_method: str = "auto",
    casting_source: Optional[Dict[str, Any]] = None,
    user_profile: Optional[Dict[str, Any]] = None,
    owner_hash: str = "",
) -> DivinationSession:
    """创建新的推演会话（draft 状态）。"""
    return DivinationSession(
        session_id="sess_" + uuid.uuid4().hex[:24],
        question=question,
        category=category,
        system=system,
        casting_method=casting_method,
        casting_source=casting_source or {},
        user_profile=user_profile or {},
        owner_hash=owner_hash,
        status="draft",
    )


def freeze_snapshot(
    session: DivinationSession,
    raw_plate: Dict[str, Any],
    module_results: List[Dict[str, Any]],
    input_payload: Dict[str, Any],
    rule_version: str = "",
    systems_used: Optional[List[str]] = None,
) -> DivinationSession:
    """冻结排盘快照。调用后 session.snapshot 永久不可修改。

    铁律：此函数是唯一可以设置 snapshot 的入口。一旦冻结，
    任何后续交互不得修改 raw_plate / module_results。
    """
    if session.snapshot is not None and session.snapshot.frozen:
        raise RuntimeError(
            "盘面已冻结，不可重新排盘。如需重起，请创建新会话或更换术数门派。"
        )
    input_hash = "sha256:" + _canonical_hash(input_payload)
    snapshot = DivinationSnapshot(
        snapshot_id="snap_" + _canonical_hash({
            "raw_plate": raw_plate,
            "input_hash": input_hash,
            "created_at": _now_iso(),
        })[:24],
        frozen=True,
        raw_plate=raw_plate,
        module_results=module_results,
        input_hash=input_hash,
        rule_version=rule_version,
        systems_used=systems_used or [],
        casting_method=session.casting_method,
    )
    session.snapshot = snapshot
    session.status = "casted"
    session.updated_at = _now_iso()
    return session


def append_interaction(
    session: DivinationSession,
    interaction_type: str,
    user_input: Dict[str, Any],
    system_response: Dict[str, Any],
    interpretation_shift: Optional[Dict[str, Any]] = None,
) -> DivinationSession:
    """追加交互记录。只追加，不修改历史。

    interpretation_shift 用于记录解读视角调整（模块B部分符合/不符合时），
    明确与原始快照分离，绝不修改 snapshot。
    """
    if interaction_type not in INTERACTION_TYPES:
        raise ValueError(f"unsupported interaction type: {interaction_type}")
    record = InteractionRecord(
        interaction_id="int_" + uuid.uuid4().hex[:16],
        type=interaction_type,
        user_input=user_input,
        system_response=system_response,
        interpretation_shift=interpretation_shift,
    )
    session.interactions.append(record)
    if session.status == "casted":
        session.status = "interacting"
    session.updated_at = _now_iso()
    return session
