"""模块D③：换角度解读。

基于用户指定的新角度（如"从对方立场"、"从长期视角"、"从财务角度"），
重新映射卦象象义，输出调整后的解读视角。
原始卦盘（snapshot）保持不变，仅调整事理解读与象义映射。
"""

from typing import Any, Dict, List, Optional

from app.workflow.plate_facts import build_plate_view


# 预设解读角度及其象义调整方向
ANGLE_PRESETS = {
    "对方立场": {
        "description": "从对方/对手的立场重新解读卦象",
        "shift_focus": "将视角从世爻/体卦转向应爻/用卦，以对方的利益与诉求为出发点",
        "key_questions": [
            "对方在本卦中的状态如何？应爻旺衰反映对方力量对比",
            "对方的核心诉求是什么？应爻所临六亲六神揭示其动机",
            "世应生克关系中，对方是主动还是被动？",
            "对方可能采取什么行动？动爻与应爻的关系是关键",
        ],
    },
    "长期视角": {
        "description": "从长期发展的角度重新解读",
        "shift_focus": "将关注点从短期吉凶转向长期趋势，重视变卦与互卦所反映的演变方向",
        "key_questions": [
            "变卦代表的最终趋势是什么？这是长期走向的核心指向",
            "互卦反映的中间过程有哪些隐藏因素？",
            "当前吉凶是否会随时间推移而转化？旺衰随月令转换而变化",
            "长期来看，哪些因素是持续性的，哪些是阶段性的？",
        ],
    },
    "财务角度": {
        "description": "从财务/资金的角度重新解读",
        "shift_focus": "以妻财爻为核心用神，重点分析资金流向、盈利能力与财务风险",
        "key_questions": [
            "妻财爻旺衰如何？这直接反映资金充裕程度",
            "妻财爻是否临动爻？动则资金有变动（流入或流出）",
            "兄弟爻是否旺动？兄弟克妻财，主破财、竞争、分流",
            "子孙爻是否旺相？子孙生妻财，为财源、投资回报",
            "官鬼爻是否克世？官鬼主压力、成本、官非开支",
        ],
    },
    "感情角度": {
        "description": "从感情/关系的角度重新解读",
        "shift_focus": "以世应关系为核心，重视双方互动模式与感情走向",
        "key_questions": [
            "世应生克关系如何？世生应则我主动，应生世则对方主动，世应比和则双方均衡",
            "世爻与应爻的旺衰对比反映双方力量与投入程度",
            "是否有合局？三合六合主感情粘合、关系稳定",
            "是否有冲？冲主矛盾、分离、变动",
            "动爻是否冲合世应？动爻往往是感情变化的触发点",
        ],
    },
    "事业角度": {
        "description": "从事业/职业发展的角度重新解读",
        "shift_focus": "以官鬼爻为核心用神，重点分析事业发展、职位变动与职场关系",
        "key_questions": [
            "官鬼爻旺衰如何？官鬼主事业、职位、权力，旺则事业有成",
            "官鬼爻是否临动爻？动则职位有变动（升迁或调动）",
            "父母爻是否旺相？父母爻主文书、资质、单位，旺则有靠山",
            "子孙爻是否旺动？子孙克官鬼，主辞职、失业、与上级不和",
            "世爻与官鬼爻的生克关系反映你与事业/上级的互动",
        ],
    },
    "风险角度": {
        "description": "从风险/隐患的角度重新解读",
        "shift_focus": "重点排查卦中的凶象、隐患与不利因素，而非关注有利面",
        "key_questions": [
            "忌神是否旺动？忌神克用神，是最大的风险来源",
            "用神是否入墓绝？入墓绝则事停滞、难有作为",
            "是否有凶神临爻？白虎主刑伤血光，玄武主欺诈隐秘，螣蛇主惊恐怪异",
            "世爻是否被冲克？世爻受冲克则求测人自身受损",
            "动爻是否化凶？动爻变爻的关系是风险演变的关键",
        ],
    },
    "机会角度": {
        "description": "从机会/有利因素的角度重新解读",
        "shift_focus": "重点挖掘卦中的吉象、助力与有利时机，而非关注风险面",
        "key_questions": [
            "原神是否旺相？原神生用神，是核心助力来源",
            "用神是否得令得地？旺相则力量充足，事易成",
            "是否有吉神临爻？青龙主喜庆财帛，六合主和合顺利",
            "是否有合局生世？合局生世则多方助力汇聚",
            "动爻是否生扶世用？动爻生世用则变化带来机遇",
        ],
    },
}


def angle_shift(
    session,
    new_angle: str,
) -> Dict[str, Any]:
    """换角度解读：基于用户指定的新角度，重新映射卦象象义。

    Args:
        session: 推演会话（snapshot 已冻结）
        new_angle: 用户指定的新解读角度

    Returns:
        {
            "type": "angle_shift",
            "new_angle": 指定的新角度,
            "matched_preset": 匹配到的预设角度（如有）,
            "shift_description": 角度转换说明,
            "shift_focus": 象义调整方向,
            "key_questions": 该角度下需要关注的关键问题,
            "reinterpretation": 基于新角度的重新解读,
            "suggested_angles": 其他建议尝试的角度,
            "snapshot_unchanged": True,
        }
    """
    if session.snapshot is None:
        return {"error": "盘面尚未生成，无法换角度解读。请先执行排盘。"}

    # 匹配预设角度
    matched = _match_preset(new_angle)
    preset = ANGLE_PRESETS.get(matched) if matched else None

    # 生成基于新角度的重新解读
    reinterpretation = _generate_reinterpretation(session, new_angle, preset)

    # 建议其他角度
    suggested = _suggest_other_angles(new_angle)

    result = {
        "type": "angle_shift",
        "new_angle": new_angle,
        "matched_preset": matched,
        "shift_description": preset["description"] if preset else f"从「{new_angle}」的角度重新解读卦象",
        "shift_focus": preset["shift_focus"] if preset else f"将解读视角调整为「{new_angle}」，重新映射卦中符号的象义",
        "key_questions": preset["key_questions"] if preset else [
            f"从{new_angle}的角度，卦中哪些符号最值得关注？",
            "该角度下，世应关系与体用生克有何新的解读？",
            "该角度下，动爻与变卦反映了什么新的趋势？",
        ],
        "reinterpretation": reinterpretation,
        "suggested_angles": suggested,
        "snapshot_unchanged": True,  # 铁律：原始卦盘不变
    }

    return result


def _match_preset(new_angle: str) -> Optional[str]:
    """匹配预设角度。"""
    text = (new_angle or "").strip()
    if not text:
        # 空字符串是任何预设的子串，必须先短路，否则会谎称命中了第一个预设
        return None
    for preset_name in ANGLE_PRESETS:
        if preset_name in text or text in preset_name:
            return preset_name
    # 关键词模糊匹配
    keyword_map = {
        "对方": "对方立场", "对手": "对方立场", "别人": "对方立场", "他人": "对方立场",
        "长期": "长期视角", "长远": "长期视角", "未来": "长期视角", "战略": "长期视角",
        "财务": "财务角度", "资金": "财务角度", "钱": "财务角度", "经济": "财务角度", "财": "财务角度",
        "感情": "感情角度", "恋爱": "感情角度", "婚姻": "感情角度", "关系": "感情角度",
        "事业": "事业角度", "工作": "事业角度", "职业": "事业角度", "职场": "事业角度",
        "风险": "风险角度", "隐患": "风险角度", "危险": "风险角度", "问题": "风险角度",
        "机会": "机会角度", "机遇": "机会角度", "有利": "机会角度", "优势": "机会角度",
    }
    for kw, preset in keyword_map.items():
        if kw in text:
            return preset
    return None


def _generate_reinterpretation(
    session,
    new_angle: str,
    preset: Optional[Dict],
) -> str:
    """生成基于新角度的重新解读文本。"""
    workflow = session.workflow_result or {}
    step6 = workflow.get("step6", {})
    fortune = step6.get("fortune_level", "平")

    lines = []
    lines.append(f"【换角度解读】从「{new_angle}」重新审视本卦")
    lines.append("")

    if preset:
        lines.append(f"视角转换：{preset['shift_focus']}")
        lines.append("")
        lines.append("该角度下的关键关注点：")
        for i, q in enumerate(preset["key_questions"], 1):
            lines.append(f"  {i}. {q}")
        lines.append("")

    # 基于盘面数据的重新解读
    lines.append("【基于本卦的重新解读】")
    lines.append("")

    plate_view = build_plate_view(session.snapshot)
    ben_gua = plate_view.get("ben_gua") or "本卦"
    bian_gua = plate_view.get("bian_gua") or "变卦"

    lines.append(f"1. 本卦「{ben_gua}」从{new_angle}看：")
    if preset and "对方" in new_angle:
        lines.append(f"   应爻/用卦所反映的对方状态是本角度的核心。当前卦中对方力量{'较强' if fortune in ('大吉','小吉') else '需结合旺衰判断'}，")
        lines.append("   对方的诉求与行动倾向需从应爻所临六亲六神深入分析。")
    elif preset and "长期" in new_angle:
        lines.append(f"   本卦反映当前格局，但长期走向需重点看变卦「{bian_gua}」。")
        lines.append("   变卦是事项演变的最终指向，当前吉凶可能随时间推移而转化。")
    elif preset and "财务" in new_angle:
        lines.append("   妻财爻是本角度的核心用神。妻财旺衰直接反映资金状况，")
        lines.append("   兄弟爻动则主破财分流，子孙爻旺则为财源广进。")
    else:
        lines.append(f"   需从{new_angle}的核心关注点出发，重新审视卦中各符号的象义。")
        lines.append("   同一卦象在不同角度下，吉凶指向可能完全不同。")

    lines.append("")
    lines.append(f"2. 变卦「{bian_gua}」从{new_angle}看：")
    lines.append(f"   变卦代表事项发展的趋势与结果。从{new_angle}角度，变卦所反映的走向")
    lines.append(f"   {'较为有利' if fortune in ('大吉','小吉') else '需要谨慎应对'}，但需结合具体符号深入判断。")

    lines.append("")
    lines.append("3. 动爻与变爻：")
    moving = plate_view.get("moving_line")
    if moving:
        lines.append(f"   第{moving}爻动，是本卦气机发动之处。从{new_angle}角度，")
        lines.append("   该动爻所反映的变化因素需要重点关注，它可能是事态演变的关键触发点。")
    else:
        lines.append(f"   本卦无动爻（或动爻信息未明确），从{new_angle}角度，")
        lines.append("   事态相对稳定，变化可能来自外部因素而非内部发动。")

    lines.append("")
    lines.append(f"4. 原吉凶定性「{fortune}」在新角度下的修正：")
    lines.append(f"   原吉凶定性是从综合角度判断的。从{new_angle}角度，")
    if preset and "风险" in new_angle:
        lines.append("   应更重视隐患与不利因素。原判断中的有利面可能掩盖了潜在风险，")
        lines.append("   建议重点排查忌神、凶神、冲克等不利符号。")
    elif preset and "机会" in new_angle:
        lines.append("   应更重视机遇与助力因素。原判断中的不利面可能被过度强调，")
        lines.append("   建议重点挖掘原神、吉神、合局生扶等有利符号。")
    else:
        lines.append("   吉凶指向可能有所调整。建议结合该角度的核心关注点，")
        lines.append("   重新评估各因素的权重与影响。")

    lines.append("")
    lines.append("【铁律声明】换角度解读仅调整事理解读与象义映射，原始卦盘（snapshot）完全不变。")
    return "\n".join(lines)


def _suggest_other_angles(current_angle: str) -> List[str]:
    """建议其他可尝试的解读角度。"""
    all_angles = list(ANGLE_PRESETS.keys())
    matched = _match_preset(current_angle)
    if matched:
        return [a for a in all_angles if a != matched][:4]
    return all_angles[:5]
