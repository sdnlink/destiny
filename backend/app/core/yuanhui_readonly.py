"""皇极经世（元会运世）独立只读查询。

仅包装 `app.core.yuanhui.cycle_position` 的公历年粒度定位，原样保留
`epoch.status = "pending_expert_review"` 与既有 warnings；不新增卦配运世、
不映射个人吉凶、事件概率或应期。

原典依据：《皇極經世》卷一「以元經會」表（如「日甲一月丑二星甲三十一
辰子三百六十一」，即第 2 会第 1 运第 361 世），印证元=129600 年、
会=10800 年、运=360 年、世=30 年的换算层级；纪元锚点（公元前 67017 年）
仍未由专家定位具体卷/版本原文，故保持待审核。
"""
from typing import Any, Dict

from app.common.classics import get_library

from .yuanhui import (
    ENGINE_VERSION, RULE_VERSION, YEARS_PER_HUI, YEARS_PER_SHI,
    YEARS_PER_YUAN, YEARS_PER_YUN, cycle_position,
)

RULE_ID = "YHYS-READONLY-001"


def cycle_cast(year: int) -> Dict[str, Any]:
    """按公历年返回元会运世定位（工程基线，纪元待专家审核）。"""
    year = int(year)
    if not 1900 <= year <= 2100:
        raise ValueError("year must be between 1900 and 2100")
    position = cycle_position(year)
    library = get_library()
    evidence = []
    try:
        if library.available:
            evidence = library.evidence(
                ("以元經會", "元會運世", "經星", "辰子"), category="xiangshu",
                per_query=1, limit=4,
            )
    except Exception:
        evidence = []
    return {
        "schema_version": "1.0",
        "rule_id": RULE_ID,
        "system": "yuanhui",
        "school": "shaoyong-yuanhui-engineering-baseline",
        "rule_version": RULE_VERSION,
        "engine_version": ENGINE_VERSION,
        "status": "engineering_cycle_context_pending_expert_review",
        "facts": position,
        "cycle_units": {
            "years_per_yuan": YEARS_PER_YUAN, "years_per_hui": YEARS_PER_HUI,
            "years_per_yun": YEARS_PER_YUN, "years_per_shi": YEARS_PER_SHI,
            "note": "《皇極經世》卷一以元經會表的换算层级，仅公历年粒度",
        },
        "evidence": evidence,
        "judgements": [],
        "warnings": [
            "元会运世纪元采用待专家审核的工程基线（公元前67017年），当前只计算到公历年粒度。",
            "宏观周期五行关系不直接表示个人吉凶、事件概率或应期。",
            "运世配卦、声音唱和等卷中内容未工程化，不纳入本端点。",
        ],
    }


__all__ = ("cycle_cast", "RULE_ID")
