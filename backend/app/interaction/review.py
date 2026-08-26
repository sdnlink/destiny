"""模块G：事后复盘。

用户反馈事后现实结果，保留原始卦盘完全不变；
对比现实结局，区分应验象、未应验象，
从用神、旺衰、应期、人为外部干扰角度做分析。
"""

from typing import Any, Dict, List, Optional


def review_outcome(
    session,
    actual_outcome: str,
    outcome_details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """事后复盘：对比现实结果与卦象推演。

    Args:
        session: 推演会话（snapshot 已冻结）
        actual_outcome: 现实结果描述
        outcome_details: 结果细节 {timing: 实际应期, key_factors: 关键因素, unexpected: 意外情况}

    Returns:
        {
            "actual_outcome": 现实结果,
            "predicted_outcome": 卦象推演结果,
            "verified": 应验象列表,
            "unverified": 未应验象列表,
            "analysis": 从用神/旺衰/应期/人为干扰角度分析,
            "lessons": 经验教训,
            "snapshot_unchanged": True,
        }
    """
    if session.snapshot is None:
        return {"error": "盘面尚未生成，无法进行事后复盘。"}

    workflow = session.workflow_result or {}
    step6 = workflow.get("step6", {})
    predicted = {
        "fortune_level": step6.get("fortune_level", "平"),
        "trend": step6.get("trend", ""),
        "timing": step6.get("timing", ""),
        "favorable": step6.get("favorable", []),
        "obstacles": step6.get("obstacles", []),
    }

    # 应验/未应验分析
    verified = []
    unverified = []

    # 吉凶定性对比
    actual_is_favorable = _classify_outcome(actual_outcome)
    predicted_is_favorable = predicted["fortune_level"] in ("大吉", "小吉")

    if actual_is_favorable == predicted_is_favorable:
        verified.append(f"吉凶定性应验：卦象断为「{predicted['fortune_level']}」，实际结果{'偏有利' if actual_is_favorable else '偏阻滞'}，方向一致。")
    else:
        unverified.append(f"吉凶定性未应验：卦象断为「{predicted['fortune_level']}」，实际结果{'偏有利' if actual_is_favorable else '偏阻滞'}，方向相反。")

    # 有利/阻碍因素对比
    if outcome_details:
        key_factors = outcome_details.get("key_factors", [])
        for factor in key_factors:
            if any(f in factor for f in predicted["favorable"]):
                verified.append(f"有利因素应验：{factor}")
            elif any(o in factor for o in predicted["obstacles"]):
                verified.append(f"阻碍因素应验：{factor}")
            else:
                unverified.append(f"未预见因素：{factor}")

    # 应期对比
    actual_timing = (outcome_details or {}).get("timing", "")
    if actual_timing and predicted["timing"]:
        verified.append(f"应期参考：实际发生于{actual_timing}，卦象参考应期为{predicted['timing']}。")

    # 多角度分析
    analysis = _multi_angle_analysis(session, actual_outcome, verified, unverified, outcome_details)

    # 经验教训
    lessons = _extract_lessons(verified, unverified, analysis)

    # 更新会话状态为 reviewed
    session.status = "reviewed"

    return {
        "actual_outcome": actual_outcome,
        "predicted_outcome": predicted,
        "verified": verified,
        "unverified": unverified,
        "analysis": analysis,
        "lessons": lessons,
        "snapshot_unchanged": True,  # 铁律：原始卦盘完全不变
    }


def _classify_outcome(outcome: str) -> bool:
    """判断实际结果是偏有利还是偏阻滞。"""
    favorable_keywords = ["成功", "顺利", "达成", "通过", "录取", "盈利", "和好", "复合", "找到", "康复", "升职", "加薪"]
    unfavorable_keywords = ["失败", "受阻", "未通过", "落选", "亏损", "分手", "丢失", "病重", "降职", "破财", "拖延"]
    if any(kw in outcome for kw in favorable_keywords):
        return True
    if any(kw in outcome for kw in unfavorable_keywords):
        return False
    return True  # 默认偏中性


def _multi_angle_analysis(
    session,
    actual_outcome: str,
    verified: List[str],
    unverified: List[str],
    outcome_details: Optional[Dict[str, Any]],
) -> Dict[str, str]:
    """从用神、旺衰、应期、人为外部干扰角度做分析。"""
    workflow = session.workflow_result or {}
    step3 = workflow.get("step3", {})
    step4 = workflow.get("step4", {})

    analysis = {}

    # 用神角度
    yongshen = step3.get("primary_yongshen", "")
    analysis["yongshen"] = (
        f"用神为「{yongshen}」。复盘时需审视：用神所象之事是否与实际核心要素一致？"
        f"若用神取向偏差，可能导致推演方向偏离。实际结果中核心要素是否对应{yongshen}所象？"
    )

    # 旺衰角度
    wangshuai = step4.get("yongshen_wangshuai", {})
    analysis["wangshuai"] = (
        f"用神旺衰断为「{wangshuai.get('level', '平')}」。"
        f"实际结果中用神所象要素的力量对比是否符合此判断？"
        f"若实际力量与卦象旺衰不符，可能是月令日辰转换或外部因素改变了力量对比。"
    )

    # 应期角度
    analysis["timing"] = (
        "应期判断需结合动爻地支、日辰冲合、月令节气。"
        "实际应期与卦象参考是否吻合？若偏差较大，可能是动爻取象不准或应期规则适用有误。"
    )

    # 人为外部干扰
    unexpected = (outcome_details or {}).get("unexpected", [])
    if unexpected:
        analysis["external_interference"] = (
            f"实际过程中出现意外因素：{'；'.join(unexpected)}。"
            "这些人为或外部干扰可能改变了卦象所反映的趋势。"
            "卦象反映的是起盘时刻的趋势概率，后续人为决策与外部突发事件可能改变走向。"
        )
    else:
        analysis["external_interference"] = (
            "实际过程中是否存在未预见的人为决策或外部事件？"
            "任何重大的人为选择或外部环境变化都可能影响卦象趋势的兑现。"
        )

    return analysis


def _extract_lessons(
    verified: List[str],
    unverified: List[str],
    analysis: Dict[str, str],
) -> List[str]:
    """提取经验教训。"""
    lessons = []
    if verified:
        lessons.append(f"应验方面：本次推演中有{len(verified)}项与实际吻合，说明相关取象与旺衰判断具有参考价值。")
    if unverified:
        lessons.append(f"未应验方面：有{len(unverified)}项与实际不符，需复盘用神取向、旺衰判断或应期推算是否存在偏差。")
    lessons.append("卦象反映的是起盘时刻的趋势概率，非绝对预言；人为选择与外部事件可能改变走向。")
    lessons.append("建议在关键决策节点重新起盘，以获取最新趋势参考，而非依赖单次推演做长期决策。")
    return lessons
