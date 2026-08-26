"""固定输出格式渲染器。

将7步工作流结果渲染为角色规范定义的固定输出格式。
"""

from typing import Any, Dict, List


def render_plate_text(plate_data: Dict[str, Any]) -> str:
    """渲染完整排盘结果为文本。"""
    lines = []
    calendar = plate_data.get("calendar") or {}
    if calendar:
        ganzhi = calendar.get("ganzhi", {})
        lines.append("【历法基线】")
        lines.append(f"  年柱：{ganzhi.get('year', {}).get('stem', '')}{ganzhi.get('year', {}).get('branch', '')}")
        lines.append(f"  月柱：{ganzhi.get('month', {}).get('stem', '')}{ganzhi.get('month', {}).get('branch', '')}")
        lines.append(f"  日柱：{ganzhi.get('day', {}).get('stem', '')}{ganzhi.get('day', {}).get('branch', '')}")
        lines.append(f"  时柱：{ganzhi.get('hour', {}).get('stem', '')}{ganzhi.get('hour', {}).get('branch', '')}")
        lunar = calendar.get("lunar", {})
        if lunar:
            lines.append(f"  农历：{lunar.get('year', '')}年{lunar.get('month_name', '')}{lunar.get('day_name', '')}")

    plates = plate_data.get("plates", {})
    for module, plate in plates.items():
        label = plate.get("system_label", module)
        facts = plate.get("facts", {})
        lines.append(f"\n【{label}】")
        # 卦名
        original = facts.get("original") or facts.get("original_hexagram")
        changed = facts.get("changed") or facts.get("changed_hexagram")
        if original:
            if isinstance(original, dict):
                lines.append(f"  本卦：{original.get('name', '')}（{original.get('ordinal', '')}）")
            else:
                lines.append(f"  本卦：{original}")
        if changed:
            if isinstance(changed, dict):
                lines.append(f"  变卦：{changed.get('name', '')}（{changed.get('ordinal', '')}）")
            else:
                lines.append(f"  变卦：{changed}")
        # 体用
        body = facts.get("body_trigram") or facts.get("ti_trigram")
        use = facts.get("use_trigram") or facts.get("yong_trigram")
        if body and isinstance(body, dict):
            lines.append(f"  体卦：{body.get('name', '')}（{body.get('element', '')}）")
        if use and isinstance(use, dict):
            lines.append(f"  用卦：{use.get('name', '')}（{use.get('element', '')}）")
        # 动爻
        moving = facts.get("moving_line") or facts.get("dongyao")
        if moving:
            lines.append(f"  动爻：第{moving}爻")
        # 计算轨迹
        trace = plate.get("calculation_trace", [])
        if trace:
            lines.append("  推演轨迹：")
            for t in trace[:5]:
                lines.append(f"    - {t}")
        # 警告
        warnings = plate.get("warnings", [])
        for w in warnings:
            lines.append(f"  ⚠ {w}")

    return "\n".join(lines)


def render_fixed_format(
    session,
    step1: Dict[str, Any],
    step2: Dict[str, Any],
    step3: Dict[str, Any],
    step4: Dict[str, Any],
    step5: Dict[str, Any],
    step6: Dict[str, Any],
    step7: Dict[str, Any],
    reference_library: Dict[str, Any],
    reality_check: Dict[str, Any],
    followup_menu: Dict[str, Any],
) -> Dict[str, Any]:
    """渲染为固定输出格式（结构化 + 文本）。

    Returns:
        {
            "text": 完整文本输出,
            "structured": 结构化数据（供前端渲染）,
        }
    """
    parts = []

    # 求测事由 & 起盘方式
    parts.append(f"【求测事由】：{session.question}")
    parts.append(f"【起盘方式】：{session.casting_method}（{step1.get('casting_source', {})}）")
    parts.append("")

    # 完整排盘结果
    parts.append("====完整排盘结果====")
    parts.append(render_plate_text(step2))
    parts.append("")

    # 用神定位
    parts.append("====用神定位====")
    parts.append(f"用神：{step3.get('primary_yongshen', '')}，取用理由：{step3.get('logic', '')}")
    if step3.get("secondary_yongshen"):
        parts.append(f"辅助用神：{step3.get('secondary_yongshen', '')}")
    if step3.get("party_yongshen"):
        parts.append("多方人物用神：")
        for p in step3["party_yongshen"]:
            parts.append(f"  {p['party']}：{p['yongshen']}（{p['role']}）")
    parts.append("")

    # 旺衰与生克分析
    parts.append("====旺衰与生克分析====")
    ys = step4.get("yongshen_wangshuai", {})
    parts.append(f"用神{ys.get('yongshen', '')}（{ys.get('element', '')}）：{ys.get('level', '')}")
    parts.append(f"判定：{ys.get('reason', '')}")
    tiyong = step4.get("tiyong_relation")
    if tiyong:
        parts.append(f"体用关系：{tiyong.get('type', '')}——{tiyong.get('meaning', '')}")
    parts.append("生克链条：")
    for chain in step4.get("analysis_chain", []):
        parts.append(f"  - {chain}")
    parts.append("")

    # 卦象符号事理解读
    parts.append("====卦象符号事理解读====")
    for mapping in step5.get("symbol_mappings", []):
        parts.append(f"【{mapping['symbol']}】")
        parts.append(f"  原始象义：{mapping['original_meaning']}")
        parts.append(f"  事理映射：{mapping['event_mapping']}")
    if not step5.get("symbol_mappings"):
        parts.append("（符号象义待结合具体卦爻进一步拆解）")
    parts.append("")

    # 事态综合推演
    parts.append("====事态综合推演====")
    parts.append(f"现状：{step6.get('current_status', '')}")
    parts.append("有利点：")
    for f in step6.get("favorable", []):
        parts.append(f"  - {f}")
    parts.append("阻碍点：")
    for o in step6.get("obstacles", []):
        parts.append(f"  - {o}")
    parts.append(f"趋势与参考应期：{step6.get('trend', '')} {step6.get('timing', '')}")
    parts.append(f"吉凶定性：{step6.get('fortune_level', '')}")
    parts.append(f"判定依据：{'；'.join(step6.get('fortune_basis', []))}")
    parts.append("")

    # 趋吉避凶建议
    parts.append("====趋吉避凶建议====")
    for i, advice in enumerate(step7.get("advice", []), 1):
        parts.append(f"{i}. {advice}")
    parts.append("")
    parts.append(f"【文化提示】：{step7.get('disclaimer', '')}")
    parts.append("")

    # 拓展参考资料库
    parts.append("====拓展参考资料库====")
    parts.append(f"1.核心符号原始象义：{reference_library.get('core_symbols', '')}")
    parts.append(f"2.本卦重点风险隐患：{reference_library.get('risks', '')}")
    parts.append(f"3.参考时间窗口：{reference_library.get('time_window', '')}")
    parts.append(f"4.事件多发展可能性以及对应触发条件：{reference_library.get('possibilities', '')}")
    parts.append(f"5.本卦常见误读误区提醒：{reference_library.get('misreadings', '')}")
    parts.append("")

    # 卦象现状核对
    parts.append("📌卦象现状核对（请对照现实看是否符合，回复\"符合/部分符合/不符合\"，仅调整事理解读视角，绝不修改原始卦盘）")
    for i, item in enumerate(reality_check.get("items", []), 1):
        parts.append(f"{i}、卦局显示：{item}")
    parts.append("")

    # 后续交互入口
    parts.append("✨你可以选择下面任意一种方式继续沟通：")
    for item in followup_menu.get("options", []):
        parts.append(f"{item}")

    text = "\n".join(parts)

    return {
        "text": text,
        "structured": {
            "question": session.question,
            "casting_method": session.casting_method,
            "step1": step1,
            "step2": step2,
            "step3": step3,
            "step4": step4,
            "step5": step5,
            "step6": step6,
            "step7": step7,
            "reference_library": reference_library,
            "reality_check": reality_check,
            "followup_menu": followup_menu,
        },
    }
