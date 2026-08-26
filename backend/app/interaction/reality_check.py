"""模块B：排盘后现实校验交互。

完整7步流程输出完毕后输出现状核对条目。
用户回复"符合/部分符合/不符合"，仅调整事理解读视角，绝不修改原始卦盘。

铁律：原始盘面数据（snapshot）永久不可修改。
解读视角调整记录在 interaction.interpretation_shift 中，与原始盘面分离。
"""

from typing import Any, Dict, Optional


# 响应规则
REALITY_RESPONSES = {
    "符合": {
        "action": "enter_extended",
        "description": "卦象现状与现实吻合，进入拓展交互，可深入追问符号含义、发展趋势或行动建议。",
        "shift_needed": False,
    },
    "部分符合": {
        "action": "adjust_interpretation",
        "description": "卦盘原样保留，仅调整事理解读与象义映射。请告知哪些部分符合、哪些部分不符，以便重新取象解析。",
        "shift_needed": True,
    },
    "不符合": {
        "action": "offer_choice",
        "description": "二选一：①询问是否更换起盘方式重新起全新盘；②沿用本盘更换取象角度重新解析事态。原始盘面始终不动。",
        "shift_needed": True,
        "options": [
            "①更换起盘方式重新起全新盘（报数/时间/事件时间）",
            "②沿用本盘，更换取象角度重新解析事态",
        ],
    },
}


def process_reality_response(
    session,
    response: str,
    details: Optional[str] = None,
) -> Dict[str, Any]:
    """处理用户的现实校验回复。

    Args:
        session: 推演会话（snapshot 已冻结）
        response: "符合" / "部分符合" / "不符合"
        details: 用户补充的细节（哪些符合/哪些不符）

    Returns:
        {
            "response_type": 用户回复类型,
            "action": 建议动作,
            "description": 说明,
            "interpretation_shift": 解读视角调整（如有）,
            "options": 备选选项（如有）,
            "snapshot_unchanged": True,  # 铁律确认
        }

    Raises:
        RuntimeError: 如果尝试修改已冻结的 snapshot
    """
    # 铁律确认：snapshot 必须已冻结且不可修改
    if session.snapshot is None:
        raise RuntimeError("盘面尚未生成，无法进行现实校验。请先执行排盘。")
    if not session.snapshot.frozen:
        raise RuntimeError("盘面未冻结，状态异常。")

    # 归一化回复
    normalized = response.strip()
    if normalized not in REALITY_RESPONSES:
        # 模糊匹配
        for key in REALITY_RESPONSES:
            if key in normalized:
                normalized = key
                break
        else:
            return {
                "response_type": "unknown",
                "action": "retry",
                "description": "请明确回复\"符合\"、\"部分符合\"或\"不符合\"。",
                "snapshot_unchanged": True,
            }

    rule = REALITY_RESPONSES[normalized]
    result = {
        "response_type": normalized,
        "action": rule["action"],
        "description": rule["description"],
        "snapshot_unchanged": True,  # 铁律：原始盘面始终不动
    }

    if rule.get("options"):
        result["options"] = rule["options"]

    # 解读视角调整（部分符合/不符合时）
    if rule["shift_needed"]:
        interpretation_shift = {
            "shift_type": "reality_mismatch",
            "response": normalized,
            "details": details or "",
            "note": "原始卦盘（snapshot）保持不变，仅调整事理解读与象义映射视角。",
            "suggested_angles": _suggest_angles(session, normalized),
        }
        result["interpretation_shift"] = interpretation_shift

    return result


def _suggest_angles(session, response: str) -> list:
    """根据不符情况建议换角度解读的方向。"""
    angles = [
        "更换用神取向：重新审视事项核心要素对应的用神是否准确",
        "更换体用视角：从不同角色/立场重新解读体用生克关系",
        "更换动爻取象：动爻所象之事可能映射到事项的不同侧面",
        "结合月令日辰重新评估旺衰：用神旺衰随时间变化，当前阶段可能处于转换期",
    ]
    if response == "部分符合":
        return angles[:2]
    return angles
