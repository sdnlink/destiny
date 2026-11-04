"""模块D②：深度追问。

针对盘局中某一个符号、某一句断语进行深度追问。
基于已冻结盘面的原始数据（卦名、动爻、用神、旺衰等），
对用户追问的具体符号/断语进行深化解读，原始盘面不变。
"""

from typing import Any, Dict, List

from app.workflow.plate_facts import build_plate_view


# 可深度追问的符号类型关键词映射
SYMBOL_KEYWORDS = {
    "hexagram": ["卦", "本卦", "变卦", "互卦", "体卦", "用卦"],
    "moving_line": ["动爻", "变爻", "爻辞", "第几爻", "上爻", "初爻", "二爻", "三爻", "四爻", "五爻"],
    "yongshen": ["用神", "世爻", "应爻", "原神", "忌神", "仇神"],
    "liugin": ["六亲", "父母", "官鬼", "兄弟", "妻财", "子孙"],
    "liushen": ["六神", "青龙", "朱雀", "勾陈", "螣蛇", "腾蛇", "白虎", "玄武"],
    "wuxing": ["五行", "金", "木", "水", "火", "土", "生克", "相生", "相克"],
    "wangshuai": ["旺衰", "得令", "得地", "得势", "休囚", "入墓", "绝"],
    "chonghe": ["冲合", "相冲", "相合", "六合", "三合", "刑", "害", "破"],
    "fortune": ["吉凶", "大吉", "小吉", "小凶", "大凶", "应期", "趋势"],
}

# 六神象义
LIUSHEN_MEANING = {
    "青龙": "主喜庆、婚姻、财帛、升迁；性温和、好享受；临吉神则吉，临凶神则乐极生悲",
    "朱雀": "主口舌、文书、消息、诉讼；性急、好言；动则有口舌是非或文书往来",
    "勾陈": "主拖延、阻滞、田土、牢狱；性稳重、固执；临事则进展缓慢、纠缠不清",
    "螣蛇": "主惊恐、疑虑、怪异、虚惊；性多疑、善变；临事则心中不安、虚虚实实",
    "白虎": "主刑伤、血光、疾病、丧事、武职；性刚决、好斗；临凶则灾祸，临吉则威严果断",
    "玄武": "主隐秘、盗贼、暧昧、欺诈、水患；性阴险、难测；临事则有暗中操作或不可告人之事",
}

# 六亲象义
LIUQIN_MEANING = {
    "父母": "主长辈、文书、证件、房屋、车辆、学业、辛苦劳顿；生我者",
    "官鬼": "主官职、事业、丈夫、疾病、灾祸、官非、压力；克我者",
    "兄弟": "主同辈、竞争者、破财、阻力、合作、朋友；同我者",
    "妻财": "主妻子、财运、物质、利益、下属；我克者",
    "子孙": "主子女、晚辈、下属、福神、解忧、医药、娱乐、投资；我生者",
}


def deep_question(
    session,
    question: str,
) -> Dict[str, Any]:
    """深度追问：基于已冻结盘面，对用户追问的符号/断语进行深化解读。

    Args:
        session: 推演会话（snapshot 已冻结）
        question: 用户的深度追问问题

    Returns:
        {
            "question": 原始问题,
            "detected_symbols": 检测到的符号类型,
            "analysis": 深化解读文本,
            "related_plate_data": 关联的盘面原始数据,
            "snapshot_unchanged": True,
        }
    """
    if session.snapshot is None:
        return {"error": "盘面尚未生成，无法进行深度追问。请先执行排盘。"}

    # 检测问题中涉及的符号类型
    detected = _detect_symbols(question)

    # 从冻结盘面提取相关数据
    plate_data = _extract_plate_data(session, detected)

    # 生成深化解读
    analysis = _generate_deep_analysis(session, question, detected, plate_data)

    return {
        "type": "deep_question",
        "question": question,
        "detected_symbols": detected,
        "analysis": analysis,
        "related_plate_data": plate_data,
        "snapshot_unchanged": True,  # 铁律：原始盘面不变
    }


def _detect_symbols(question: str) -> List[str]:
    """从追问问题中检测涉及的符号类型。"""
    detected = []
    for symbol_type, keywords in SYMBOL_KEYWORDS.items():
        if any(kw in question for kw in keywords):
            detected.append(symbol_type)
    if not detected:
        detected.append("general")  # 通用追问
    return detected


def _extract_plate_data(session, detected: List[str]) -> Dict[str, Any]:
    """从冻结盘面提取与追问符号相关的原始数据。"""
    snapshot = session.snapshot
    # 统一走盘面事实视图：快照里冻结了归一后的卦名、动爻、体用卦
    raw_plate = build_plate_view(snapshot)
    workflow = session.workflow_result or {}

    data = {}

    if "hexagram" in detected:
        data["hexagram_info"] = {
            "ben_gua": raw_plate.get("ben_gua") or None,
            "bian_gua": raw_plate.get("bian_gua") or None,
            "hu_gua": raw_plate.get("hu_gua") or None,
            "ti_gua": raw_plate.get("ti_gua") or None,
            "yong_gua": raw_plate.get("yong_gua") or None,
        }

    if "moving_line" in detected:
        data["moving_line_info"] = {
            "moving_line": raw_plate.get("moving_line"),
            "bian_yao": raw_plate.get("bian_yao") or None,
            "yao_ci": raw_plate.get("yao_ci") or None,
        }

    if "yongshen" in detected:
        step3 = workflow.get("step3", {})
        data["yongshen_info"] = {
            "primary": step3.get("primary_yongshen"),
            "secondary": step3.get("secondary_yongshen"),
            "logic": step3.get("logic"),
        }

    if "wangshuai" in detected:
        step4 = workflow.get("step4", {})
        data["wangshuai_info"] = step4

    if "fortune" in detected:
        step6 = workflow.get("step6", {})
        data["fortune_info"] = {
            "level": step6.get("fortune_level"),
            "basis": step6.get("fortune_basis"),
            "trend": step6.get("trend"),
            "timing": step6.get("timing"),
        }

    # 通用信息始终包含
    data["basic"] = {
        "question": session.question,
        "category": session.category,
        "system": session.system,
        "casting_method": session.casting_method,
        "snapshot_id": snapshot.snapshot_id,
    }

    return data


def _generate_deep_analysis(
    session,
    question: str,
    detected: List[str],
    plate_data: Dict[str, Any],
) -> str:
    """生成深化解读文本。"""
    lines = []
    lines.append(f"【深度追问】{question}")
    lines.append("")

    if "general" in detected:
        lines.append("本追问未明确指向特定符号类型，以下从整体盘面角度进行深化解读：")
        lines.append("")
        basic = plate_data.get("basic", {})
        lines.append(f"1. 盘面基础：求测「{basic.get('question', '')}」，类别为{basic.get('category', '')}，使用{basic.get('system', '')}体系起盘。")
        lines.append(f"2. 盘面快照ID：{basic.get('snapshot_id', '')}，原始数据已永久冻结，本次解读仅基于该快照展开。")
        lines.append("3. 建议明确追问方向：可针对具体卦名、动爻、用神、六亲、六神、旺衰、应期等符号进行深化。")
        return "\n".join(lines)

    for symbol_type in detected:
        if symbol_type == "hexagram":
            info = plate_data.get("hexagram_info", {})
            lines.append("【卦象符号深化】")
            if info.get("ben_gua"):
                lines.append(f"- 本卦：{info['ben_gua']}，代表事项当前的基本格局与初始状态。")
            if info.get("bian_gua"):
                lines.append(f"- 变卦：{info['bian_gua']}，代表事项发展的最终趋势与结果指向。")
            if info.get("hu_gua"):
                lines.append(f"- 互卦：{info['hu_gua']}，代表事项发展过程中的中间状态与隐藏因素。")
            if info.get("ti_gua") and info.get("yong_gua"):
                lines.append(f"- 体用关系：体卦为{info['ti_gua']}（求测人自身），用卦为{info['yong_gua']}（所测之事）。体用生克关系决定吉凶基本走向——用生体则事来助我，体生用则我去耗力，体克用则我能掌控，用克体则事来伤我，比和则双方均衡。")
            lines.append("")

        elif symbol_type == "moving_line":
            info = plate_data.get("moving_line_info", {})
            lines.append("【动爻符号深化】")
            if info.get("moving_line"):
                lines.append(f"- 动爻位置：第{info['moving_line']}爻。动爻是卦中气机发动之处，代表事项中最活跃、最关键的变化因素。")
                lines.append("- 动爻所主：动爻临何六亲、何六神，决定该变化的性质与方向。动爻生世/应则吉，冲世/应则凶。")
            if info.get("yao_ci"):
                lines.append(f"- 爻辞参考：{info['yao_ci']}")
            lines.append("- 变爻：动爻变化后形成的爻，代表变化后的新状态，需结合变卦综合判断。")
            lines.append("")

        elif symbol_type == "yongshen":
            info = plate_data.get("yongshen_info", {})
            lines.append("【用神符号深化】")
            if info.get("primary"):
                lines.append(f"- 主用神：{info['primary']}。用神是六爻预测的核心，代表所测之事的核心载体与关键要素。")
            if info.get("logic"):
                lines.append(f"- 取用逻辑：{info['logic']}")
            lines.append("- 用神旺衰直接决定吉凶：用神旺相则事可成，用神休囚则事难就，用神入墓绝则事停滞。")
            lines.append("- 原神（生用神者）旺则用神有源，忌神（克用神者）旺则用神受损，仇神（克原神生忌神者）旺则雪上加霜。")
            lines.append("")

        elif symbol_type == "liugin":
            lines.append("【六亲符号深化】")
            for qin, meaning in LIUQIN_MEANING.items():
                if qin in question:
                    lines.append(f"- {qin}：{meaning}")
                    lines.append(f"  在本卦中，{qin}爻的旺衰、动变、与世应的生克关系，直接影响所测之事的走向。")
            lines.append("")

        elif symbol_type == "liushen":
            lines.append("【六神符号深化】")
            for shen, meaning in LIUSHEN_MEANING.items():
                if shen in question or (shen == "螣蛇" and "腾蛇" in question):
                    lines.append(f"- {shen}：{meaning}")
                    lines.append("  六神附于爻上，为该爻增添特定的色彩与倾向。同一六亲临不同六神，其表现方式截然不同。")
            lines.append("")

        elif symbol_type == "wuxing":
            lines.append("【五行生克深化】")
            lines.append("- 五行相生：金生水、水生木、木生火、火生土、土生金。生者付出，被生者受益。")
            lines.append("- 五行相克：金克木、木克土、土克水、水克火、火克金。克者制约，被克者受损。")
            lines.append("- 在卦中，用神的五行属性与月令日辰的五行生克关系，决定用神的旺衰状态。")
            lines.append("- 体卦与用卦的五行生克，是梅花易数判断吉凶的基本依据。")
            lines.append("")

        elif symbol_type == "wangshuai":
            info = plate_data.get("wangshuai_info", {})
            lines.append("【旺衰状态深化】")
            if info:
                ys = info.get("yongshen_wangshuai") or info.get("用神旺衰") or {}
                if ys:
                    lines.append(f"- 用神旺衰：{ys.get('level', '未知')}")
                    lines.append(f"  得令：{ys.get('得令', '未知')}，得地：{ys.get('得地', '未知')}，得势：{ys.get('得势', '未知')}")
            lines.append("- 旺相休囚死：春木旺火相水休金囚土死，夏火旺土相木休水囚金死，秋金旺水相土休火囚木死，冬水旺木相金休土囚火死。")
            lines.append("- 用神旺相则力量充足，事易成；休囚则力量不足，事难就；入墓绝则停滞不前。")
            lines.append("- 动爻即使休囚，也有发动之力；静爻即使旺相，也需待时方应。")
            lines.append("")

        elif symbol_type == "chonghe":
            lines.append("【冲合刑害深化】")
            lines.append("- 六冲：子午冲、丑未冲、寅申冲、卯酉冲、辰戌冲、巳亥冲。冲主动、散、破、离。")
            lines.append("- 六合：子丑合、寅亥合、卯戌合、辰酉合、巳申合、午未合。合主聚、留、绊、和。")
            lines.append("- 三合局：申子辰合水局、亥卯未合木局、寅午戌合火局、巳酉丑合金局。合局则力量汇聚。")
            lines.append("- 三刑：寅巳申三刑、丑戌未三刑、子卯相刑。刑主伤害、纠纷、官非。")
            lines.append("- 六害：子未害、丑午害、寅巳害、卯辰害、申亥害、酉戌害。害主暗中受损、不和。")
            lines.append("- 用神逢冲则动，逢合则绊；世应相冲则双方对立，世应相合则双方和合。")
            lines.append("")

        elif symbol_type == "fortune":
            info = plate_data.get("fortune_info", {})
            lines.append("【吉凶定性深化】")
            if info.get("level"):
                lines.append(f"- 吉凶等级：{info['level']}")
            if info.get("basis"):
                basis = info["basis"]
                if isinstance(basis, list):
                    lines.append(f"- 判定依据：{'；'.join(basis)}")
                else:
                    lines.append(f"- 判定依据：{basis}")
            if info.get("trend"):
                lines.append(f"- 发展趋势：{info['trend']}")
            if info.get("timing"):
                lines.append(f"- 参考应期：{info['timing']}")
            lines.append("- 吉凶等级是综合判断的结果，非绝对预言。大吉中也有隐患，大凶中也有转机。")
            lines.append("- 应期是参考时间窗口，实际兑现时间受人为决策与外部因素影响。")
            lines.append("")

    lines.append("【铁律声明】以上深化解读基于已永久冻结的原始盘面数据，盘面本身未做任何修改。")
    return "\n".join(lines)
