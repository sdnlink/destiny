"""模块F：多抉择分支推演。

二选一/多选择类问题，优先基于现有卦盘做分支推演，
输出各选择利弊、风险、趋势。原盘信息不足时如实告知，建议重新起卦分别测项。
"""

from typing import Any, Dict, List, Optional


def analyze_branches(
    session,
    choices: List[str],
) -> Dict[str, Any]:
    """基于现有卦盘做多抉择分支推演。

    Args:
        session: 推演会话（snapshot 已冻结）
        choices: 备选方案列表，如 ["选择A", "选择B"]

    Returns:
        {
            "choices": 各选择分析,
            "recommendation": 综合建议,
            "note": 注意事项,
            "snapshot_unchanged": True,
        }
    """
    if session.snapshot is None:
        return {"error": "盘面尚未生成，请先执行排盘。"}

    if not choices or len(choices) < 2:
        return {"error": "请提供至少2个备选方案进行分支推演。"}

    # 从卦象提取分支分析依据
    workflow = session.workflow_result or {}
    step6 = workflow.get("step6", {})
    fortune = step6.get("fortune_level", "平")
    favorable = step6.get("favorable", [])
    obstacles = step6.get("obstacles", [])

    choice_analyses = []
    for i, choice in enumerate(choices):
        analysis = _analyze_single_choice(session, choice, i, fortune, favorable, obstacles)
        choice_analyses.append(analysis)

    # 综合建议
    recommendation = _generate_recommendation(choice_analyses, fortune)

    return {
        "choices": choice_analyses,
        "recommendation": recommendation,
        "note": "本分支推演基于现有卦盘取象，原盘信息不足时建议重新起卦分别测项。原始盘面保持不变。",
        "snapshot_unchanged": True,  # 铁律
    }


def _analyze_single_choice(
    session,
    choice: str,
    index: int,
    fortune: str,
    favorable: List[str],
    obstacles: List[str],
) -> Dict[str, Any]:
    """分析单个选择的利弊风险趋势。"""
    # 基于选择序号对应卦中不同爻位/角度
    angle_map = [
        {"angle": "世爻视角", "focus": "自身能力与资源是否支撑该选择"},
        {"angle": "应爻视角", "focus": "外部环境与对方态度是否配合该选择"},
        {"angle": "动爻视角", "focus": "变化趋势是否有利于该选择"},
        {"angle": "用神视角", "focus": "核心要素旺衰是否支撑该选择"},
    ]
    angle = angle_map[index % len(angle_map)]

    # 利弊分析（基于卦象吉凶倾向）
    if fortune in ("大吉", "小吉"):
        pros = [
            f"从{angle['angle']}看，{angle['focus']}，卦象偏有利",
            "用神旺相或体用生克有利，推进阻力较小",
        ]
        cons = [
            "需注意顺境中可能忽略的细节风险",
            "动爻变化可能带来意料之外的转折",
        ]
        risk_level = "低"
        trend = "顺势推进，成功概率较高"
    elif fortune == "平":
        pros = [
            f"从{angle['angle']}看，{angle['focus']}，吉凶参半",
            "稳扎稳打可逐步推进",
        ]
        cons = [
            "存在不确定因素，不宜冒进",
            "需小范围验证后再扩大投入",
        ]
        risk_level = "中"
        trend = "平稳推进，需控制节奏"
    else:
        pros = [
            f"从{angle['angle']}看，{angle['focus']}，需谨慎",
            "可借此选择排查风险、积累经验",
        ]
        cons = [
            "用神休囚或体用相克，推进阻力较大",
            "可能出现拖延、反复或外部阻力",
        ]
        risk_level = "高"
        trend = "宜暂缓或调整策略，待条件转好"

    return {
        "choice": choice,
        "analysis_angle": angle["angle"],
        "focus": angle["focus"],
        "pros": pros,
        "cons": cons,
        "risk_level": risk_level,
        "trend": trend,
    }


def _generate_recommendation(choice_analyses: List[Dict[str, Any]], fortune: str) -> str:
    """生成综合建议。"""
    # 按风险等级排序
    risk_order = {"低": 0, "中": 1, "高": 2}
    sorted_choices = sorted(choice_analyses, key=lambda c: risk_order.get(c["risk_level"], 1))
    best = sorted_choices[0]

    if best["risk_level"] == "低":
        return f"综合卦象倾向，「{best['choice']}」风险较低、趋势较顺，可作为优先考虑方案。但仍需结合实际情况核实关键细节。"
    elif best["risk_level"] == "中":
        return f"各方案风险相近，「{best['choice']}」相对平稳。建议先小范围试点验证，确认可行后再扩大投入。"
    else:
        return f"当前卦象整体偏阻滞，各方案均有一定风险。「{best['choice']}」相对可控，但建议暂缓重大决策，待外部条件转好或用神得令时再行推进。"
