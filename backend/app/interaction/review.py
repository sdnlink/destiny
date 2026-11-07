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
    actual_direction = _classify_direction(actual_outcome)

    if predicted["fortune_level"] == "未评级":
        # 没有卦象就没有吉凶断语，拿「未评级」去比对方向会凭空造出「未应验」
        verified.append("本次未评级（未排卦象体系），不作吉凶应验判断，仅对照盘面事实与现实结果。")
    elif predicted["fortune_level"] == "平":
        # 「平」本来就不指向吉凶；再拿它去比对方向，中立结果也会被写成「方向相反」
        direction_text = {"favorable": "偏有利", "unfavorable": "偏阻滞", "neutral": "中性"}[actual_direction]
        verified.append(
            f"吉凶定性为「平」，不指向明确吉凶；实际结果{direction_text}，仅作盘面对照，不作应验/未应验判断。"
        )
    elif actual_direction == "neutral":
        verified.append(
            f"吉凶定性为「{predicted['fortune_level']}」，实际结果中性；方向无法核对，不作应验/未应验判断。"
        )
    elif (actual_direction == "favorable") == (predicted["fortune_level"] in ("大吉", "小吉")):
        verified.append(f"吉凶定性应验：卦象断为「{predicted['fortune_level']}」，实际结果{'偏有利' if actual_direction == 'favorable' else '偏阻滞'}，方向一致。")
    else:
        unverified.append(f"吉凶定性未应验：卦象断为「{predicted['fortune_level']}」，实际结果{'偏有利' if actual_direction == 'favorable' else '偏阻滞'}，方向相反。")

    # 有利/阻碍因素对比
    if outcome_details:
        key_factors = outcome_details.get("key_factors", [])
        for factor in key_factors:
            # 双向包含：预测侧是整句、用户侧是短语，单向匹配会让两条分支永远走不到
            if _matches_any(factor, predicted["favorable"]):
                verified.append(f"有利因素应验：{factor}")
            elif _matches_any(factor, predicted["obstacles"]):
                verified.append(f"阻碍因素应验：{factor}")
            else:
                unverified.append(f"未预见因素：{factor}")

    # 应期对比
    actual_timing = (outcome_details or {}).get("timing", "")
    if actual_timing and predicted["timing"]:
        verified.append(f"应期参考：实际发生于{actual_timing}，卦象参考应期为{predicted['timing']}。")

    # 多角度分析
    framework = _domain_framework(workflow)
    analysis = _multi_angle_analysis(session, actual_outcome, verified, unverified, outcome_details)

    # 经验教训
    lessons = _extract_lessons(verified, unverified, analysis, framework)

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


def _matches_any(factor: str, candidates) -> bool:
    """判断用户给出的因素是否命中预测量。

    预测量是完整句子，用户因素是短语，因此两个方向都要比较；空串直接忽略，
    否则 "" in factor 恒为真会把所有因素都算作应验。
    """
    text = (factor or "").strip()
    if not text:
        return False
    for candidate in candidates or []:
        phrase = (candidate or "").strip()
        if phrase and (phrase in text or text in phrase):
            return True
    return False


def _classify_direction(outcome: str) -> str:
    """三态判定：favorable / unfavorable / neutral。

    中立结果不能当成「偏有利」，否则预测为「平」时会被写成方向相反。
    """
    favorable_keywords = ["成功", "顺利", "达成", "通过", "录取", "盈利", "和好", "复合", "找到", "康复", "升职", "加薪"]
    unfavorable_keywords = ["失败", "受阻", "未通过", "落选", "亏损", "分手", "丢失", "病重", "降职", "破财", "拖延"]
    # 先判不利关键词："未通过"包含"通过"，顺序反了会把失败读成有利
    if any(kw in outcome for kw in unfavorable_keywords):
        return "unfavorable"
    if any(kw in outcome for kw in favorable_keywords):
        return "favorable"
    return "neutral"


def _classify_outcome(outcome: str) -> bool:
    """判断实际结果是偏有利还是偏阻滞（保留旧接口：中性按偏有利处理）。"""
    return _classify_direction(outcome) != "unfavorable"


def _domain_framework(workflow: Dict[str, Any]) -> str:
    """非卦象体系返回体系名，卦象体系返回空串。"""
    step3 = workflow.get("step3") or {}
    step4 = workflow.get("step4") or {}
    framework = step3.get("yongshen_framework") or step4.get("yongshen_framework") or ""
    return "" if framework in ("", "卦象体系") else framework


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

    framework = _domain_framework(workflow)
    yongshen = step3.get("primary_yongshen", "")

    if framework:
        # 没有卦爻，复盘只按本体系成立的口径说，不谈月令旺衰/动爻应期
        analysis["yongshen"] = (
            f"本盘未排卦象体系，复盘按{framework}口径：用神为「{yongshen}」。"
            f"需核对该用神（或用事宫）是否确实对应现实中的核心要素；取用偏差会带偏整段推演。"
        )
        analysis["wangshuai"] = (
            f"{framework}不以月令定卦象旺衰，旺衰项本次为「{step4.get('yongshen_wangshuai', {}).get('level', '不适用')}」。"
            "复盘应看本体系内的力量信号（如日主得令得地、宫位三方四正、门星神格局、三传生克）是否与现实一致。"
        )
        analysis["timing"] = (
            f"{framework}的应期按本体系时间信号核对（如节气/时辰、大运流年、大限流年、三传落宫）；"
            "实际发生时间与盘面时间窗口是否吻合，需以具体符号为准，而不是套用六爻动爻应期。"
        )
    else:
        analysis["yongshen"] = (
            f"用神为「{yongshen}」。复盘时需审视：用神所象之事是否与实际核心要素一致？"
            f"若用神取向偏差，可能导致推演方向偏离。实际结果中核心要素是否对应{yongshen}所象？"
        )
        analysis["wangshuai"] = (
            f"用神旺衰断为「{step4.get('yongshen_wangshuai', {}).get('level', '平')}」。"
            f"实际结果中用神所象要素的力量对比是否符合此判断？"
            f"若实际力量与卦象旺衰不符，可能是月令日辰转换或外部因素改变了力量对比。"
        )
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
    framework: str = "",
) -> List[str]:
    """提取经验教训。"""
    lessons = []
    if verified:
        lessons.append(f"应验方面：本次推演中有{len(verified)}项与实际吻合，说明相关取象与旺衰判断具有参考价值。")
    if unverified:
        lessons.append(f"未应验方面：有{len(unverified)}项与实际不符，需复盘用神取向、旺衰判断或应期推算是否存在偏差。")
    if framework:
        lessons.append(f"{framework}盘面反映的是起盘时刻的盘面结构，不是绝对预言；人为选择与外部事件可能改变走向。")
    else:
        lessons.append("卦象反映的是起盘时刻的趋势概率，非绝对预言；人为选择与外部事件可能改变走向。")
    lessons.append("建议在关键决策节点重新起盘，以获取最新趋势参考，而非依赖单次推演做长期决策。")
    return lessons
