"""模块B：排盘后现实校验交互。

完整7步流程输出完毕后输出现状核对条目。
用户回复"符合/部分符合/不符合"，仅调整事理解读视角，绝不修改原始卦盘。

铁律：原始盘面数据（snapshot）永久不可修改。
解读视角调整记录在 interaction.interpretation_shift 中，与原始盘面分离。
"""

from typing import Any, Dict, Optional


# 否定表达：紧邻关键词前的单字否定词，以及常见否定短语。
# 只做「关键词前窗口」判断，避免把「未来符合预期」里的「未」误当否定。
NEGATION_CHARS = "不未非没否"
NEGATION_PHRASES = ("不太", "不完全", "不够", "不是很", "并不", "不是", "没有", "未能", "未曾", "无法", "说不上")

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
        # 模糊匹配：关键词按长度降序，"符合"是"不符合"/"部分符合"的子串，
        # 先匹配短词会把否定回答整体反转。
        matched = None
        for key in sorted(REALITY_RESPONSES, key=len, reverse=True):
            index = normalized.find(key)
            if index == -1:
                continue
            if key in ("符合", "部分符合") and _is_negated_before(normalized, index):
                # "不太符合""并不完全符合"：命中的是正向表述，但前面紧邻否定词
                matched = "不符合"
            else:
                matched = key
            break
        if matched:
            normalized = matched
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


def _is_negated_before(text: str, index: int) -> bool:
    """判断 text[index:] 这个正向关键词前面是否是否定表达。

    "不太符合" / "不是完全符合" / "没有符合" 都要判为否定；
    而 "未来符合预期" 里的"未"离关键词隔着"来"，不算否定。
    单字否定词只在紧邻位置生效，否定短语允许出现在整段前缀里
    （"不是完全符合"的"不是"离关键词隔着"完全"）。
    """
    prefix = text[:index]
    if prefix.endswith(tuple(NEGATION_CHARS)):
        return True
    return any(phrase in prefix for phrase in NEGATION_PHRASES)


def _suggest_angles(session, response: str) -> list:
    """根据不符情况建议换角度解读的方向。"""
    workflow = getattr(session, "workflow_result", None) or {}
    framework = (workflow.get("step4") or {}).get("yongshen_framework") \
        or (workflow.get("step3") or {}).get("yongshen_framework") or ""
    if framework and framework != "卦象体系":
        # 没有卦爻的盘面，不能让人「更换动爻取象」或「重新评估旺衰」
        angles = [
            f"重新审视{framework}的取用口径：确认用神/用事宫是否对应所求之事",
            "更换解读视角：从盘面其他关键符号（宫位、星曜、门星神、三传）重新取象",
            "结合起局时间重新评估：同一符号在不同时点分量不同，可能是阶段转换期",
        ]
        return angles[:2] if response == "部分符合" else angles
    angles = [
        "更换用神取向：重新审视事项核心要素对应的用神是否准确",
        "更换体用视角：从不同角色/立场重新解读体用生克关系",
        "更换动爻取象：动爻所象之事可能映射到事项的不同侧面",
        "结合月令日辰重新评估旺衰：用神旺衰随时间变化，当前阶段可能处于转换期",
    ]
    if response == "部分符合":
        return angles[:2]
    return angles
