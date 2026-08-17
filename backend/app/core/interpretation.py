"""Deduction interpretation layer connecting charts and hexagram meanings to real-world questions."""

from typing import Any, Dict, List, Optional
from app.core.hexagram_service import get_hexagram_explanation

MODULE_LABELS = {
    "zhouyi": "周易",
    "meihua": "梅花易数",
    "liuyao": "六爻",
    "liuren": "大六壬",
    "ziwei": "紫微斗数",
}
CATEGORY_LABELS = {
    "career": "事业",
    "finance": "财务",
    "relationship": "关系",
    "travel": "出行",
    "study": "学业",
    "other": "当前事项",
}
RELATIVE_MEANINGS = {
    "父母": "文书契约、规章资质、长辈领导、信息支撑或房产车辆",
    "兄弟": "同级同僚、协作者、合伙人、竞争对手或资源分流",
    "子孙": "策划方案、创新产出、客户群体、福德消灾或执行成果",
    "妻财": "资金资产、投资收益、交易标的、薪酬报酬或可支配资源",
    "官鬼": "管理约束、工作职责、考核监管、风险压力或亟待解决的问题",
}
SPIRIT_MEANINGS = {
    "青龙": "吉庆祥和、贵人相助、开拓喜悦、正派光明",
    "朱雀": "文书信息、口舌辩论、宣传传播、通讯信息",
    "勾陈": "田土房产、内部事务、拖延羁绊、稳重固执",
    "螣蛇": "虚惊疑虑、梦境异变、纠缠反复、心思多变",
    "白虎": "刚决果断、道路交通、严厉惩戒、风波隐患",
    "玄武": "暗中运筹、隐秘事务、智慧谋略、防范欺瞒",
}
RELATION_MEANINGS = {
    "same_element": "体用同属一行（比和），同气相求、和衷共济，宜加强共识同频与团队协同",
    "use_generates_body": "用生体，外部条件滋养主体，贵人临门、资源借力顺畅，宜顺势承接",
    "body_generates_use": "体生用，主体对外持续输出，精力或资金持续投入，宜控制节奏防范过度消耗",
    "use_controls_body": "用克体，外部规则、竞争或客观环境制约主体，逆境受限，宜守正防守避其锋芒",
    "body_controls_use": "体克用，主体具备掌控力与突破能力，能够主导推进克服障碍，但需戒骄戒躁",
}


def _find(module_results, name):
    return next((item["result"] for item in module_results if item.get("module") == name), None)


def _imagery_for(imagery, module, roles=None):
    rows = []
    for candidate in (imagery or {}).get("candidates", []):
        if candidate.get("module") != module or (roles and candidate.get("role") not in roles):
            continue
        phrases = []
        for dimension, values in candidate.get("selected_imagery", {}).items():
            phrases.append(f"{dimension}如{('、'.join(values))}")
        rows.append({
            "candidate_id": candidate.get("candidate_id"),
            "role": candidate.get("role"),
            "symbol": candidate.get("symbol"),
            "text": "；".join(phrases),
        })
    return rows


def _zhouyi(result: Dict[str, Any], imagery: Optional[Dict[str, Any]], category: str = "other") -> Dict[str, Any]:
    facts = result.get("facts", {})
    orig = facts.get("original", {})
    chg = facts.get("changed", {})
    mutual = facts.get("mutual", {})
    opposite = facts.get("opposite", {})
    reversed_h = facts.get("reversed", {})
    moving = facts.get("moving_lines", [])

    orig_exp = get_hexagram_explanation(orig.get("name"))
    chg_exp = get_hexagram_explanation(chg.get("name"))
    imagery_rows = _imagery_for(imagery, "zhouyi")

    # 卦象详解
    cat_key = f"{category}_interpretation"
    orig_detail = orig_exp.get(cat_key) or orig_exp.get("summary", "") if orig_exp else ""
    orig_nature = orig_exp.get("nature", "") if orig_exp else ""
    orig_image = orig_exp.get("great_image", "") if orig_exp else ""
    orig_judg = orig_exp.get("judgment", "") if orig_exp else ""

    if not moving:
        change_desc = "六爻静而不动，局势基本处于既有框架与稳态积累之中，解卦重点在于明晰本卦本质，遵循原有规律前行。"
    elif len(moving) == 1:
        change_desc = f"动爻在第{moving[0]}爻，提示变动的核心驱动力集中于此位，宜在此关口聚焦发力或针对性防范。"
    else:
        change_desc = f"共有{len(moving)}处动爻（{'、'.join(map(str, moving))}），提示局势存在多变量联动与转换，宜分步验证、审慎推进。"

    correspondence = (
        f"【本卦卦意】《{orig.get('name')}》卦（{orig_nature}），卦辞曰“{orig_judg}”，象曰“{orig_image}”。{orig_detail} "
        f"【动变趋向】{change_desc} 最终转化为《{chg.get('name')}》卦（{chg_exp.get('nature', '') if chg_exp else ''}）。"
        f"【关联卦象】互卦为《{mutual.get('name')}》（内在动力），错卦为《{opposite.get('name')}》（对立反思），综卦为《{reversed_h.get('name')}》（换位视角）。"
    )
    if imagery_rows:
        correspondence += f" 本卦类象参考：{('；'.join(row['text'] for row in imagery_rows[:2]))}。"

    return {
        "module": "zhouyi",
        "title": "周易：卦象演变与时位机理",
        "chart_fact": f"本卦《{orig.get('name')}》（第{orig.get('ordinal')}卦），动爻{'、'.join(map(str, moving)) if moving else '无'}，变卦《{chg.get('name')}》（第{chg.get('ordinal')}卦）。",
        "hexagram_nature": orig_nature,
        "great_image": orig_image,
        "judgment": orig_judg,
        "correspondence": correspondence,
        "verification": "将本卦卦德与动爻位置对应到现实中的关键节点；顺应自然时位，切忌违时妄动。",
        "evidence_refs": [row["candidate_id"] for row in imagery_rows],
        "rule_ids": ["INTERP-CORRESPONDENCE-001", "YI-RELATION-001", "XIANG-CONTEXT-001"],
    }


def _meihua(result: Dict[str, Any], imagery: Optional[Dict[str, Any]], category: str = "other") -> Dict[str, Any]:
    facts = result.get("facts", {})
    body_use = facts.get("body_use", {})
    body_tri = body_use.get("body_trigram", {})
    use_tri = body_use.get("use_trigram", {})
    original_evidence = next((item for item in result.get("evidence", []) if item.get("stage") == "original"), result.get("evidence", [{}])[0])
    relation_text = RELATION_MEANINGS.get(original_evidence.get("code"), "")
    imagery_rows = _imagery_for(imagery, "meihua", {"body", "use", "changed_use"})
    body_image = next((row["text"] for row in imagery_rows if row.get("role") == "body"), "")
    use_image = next((row["text"] for row in imagery_rows if row.get("role") == "use"), "")

    orig_h = facts.get("original", {})
    chg_h = facts.get("changed", {})
    orig_exp = get_hexagram_explanation(orig_h.get("name"))

    correspondence = (
        f"【体用定位】以【{body_tri.get('name')}】（属{body_tri.get('element')}）为体卦代表求问主体自身，"
        f"以【{use_tri.get('name')}】（属{use_tri.get('element')}）为用卦代表外部环境与对应事物。"
        f"【五行生克】{relation_text}。"
        f"【本卦变卦】起得本卦《{orig_h.get('name')}》（{orig_exp.get('nature', '') if orig_exp else ''}），动第{facts.get('moving_line')}爻，变卦为《{chg_h.get('name')}》。"
        f"体卦类象包含：{body_image or '暂无'}；用卦类象包含：{use_image or '暂无'}。"
    )

    return {
        "module": "meihua",
        "title": "梅花易数：体用生克与内外气机",
        "chart_fact": f"体卦【{body_tri.get('name')}】（{body_tri.get('element')}）、用卦【{use_tri.get('name')}】（{use_tri.get('element')}），本卦阶段为{original_evidence.get('label')}。",
        "correspondence": correspondence,
        "verification": "明确自身能力基本盘（体）与外部条件、对手、资源（用）的相互生克力量，据此决定攻守策略。",
        "evidence_refs": [original_evidence.get("evidence_id")] + [row["candidate_id"] for row in imagery_rows],
        "rule_ids": ["INTERP-CORRESPONDENCE-001", "MH-BODYUSE-001", "MH-FIVE-ELEMENT-001", "XIANG-CONTEXT-001"],
    }


def _liuyao(result: Dict[str, Any], imagery: Optional[Dict[str, Any]], category: str = "other") -> Dict[str, Any]:
    facts = result.get("facts", {})
    line_chart = facts.get("line_chart", [])
    moving_lines = [line for line in line_chart if line.get("is_moving")]
    palace = facts.get("palace", {})
    xun = facts.get("xun", {})

    moving_texts = []
    for line in moving_lines:
        status = []
        if line.get("roles"):
            status.append("、".join(line["roles"]))
        if line.get("is_void"):
            status.append("旬空")
        spirit_desc = SPIRIT_MEANINGS.get(line.get("six_spirit"), "")
        rel_desc = RELATIVE_MEANINGS.get(line.get("six_relative"), "")
        moving_texts.append(
            f"第{line.get('position')}爻【{line.get('six_relative')}】临【{line.get('six_spirit')}】（{spirit_desc}），"
            f"纳干支{line.get('stem_branch')}（{line.get('element')}），其象指向{rel_desc}"
            f"{('，并处于' + '、'.join(status)) if status else ''}"
        )

    imagery_rows = _imagery_for(imagery, "liuyao", {"palace"})

    correspondence = (
        f"【八宫归属】本卦归于【{palace.get('name')}宫】（{palace.get('stage')}），"
        f"世爻在第{palace.get('host_line')}爻代表求问者自身，应爻在第{palace.get('response_line')}爻代表对方或目标环境。"
        f"【旬空与动爻】占日为{facts.get('day_pillar')}，旬空在【{'、'.join(xun.get('empty_branches', []))}】。"
        f"{('；'.join(moving_texts) if moving_texts else '盘中无动爻，六亲各自安位，宜静观其变。')}"
    )

    return {
        "module": "liuyao",
        "title": "六爻纳甲：世应格局与六亲神煞",
        "chart_fact": f"{palace.get('name')}宫{palace.get('stage')}，世爻第{palace.get('host_line')}爻，应爻第{palace.get('response_line')}爻；动爻{'；'.join(moving_texts) if moving_texts else '无动爻'}。",
        "correspondence": correspondence,
        "verification": "将动爻所临六亲与六神转换为具体现实角色进行核对；旬空为阶段性蓄力或暂时未定，不必悲观臆断。",
        "evidence_refs": [row["candidate_id"] for row in imagery_rows],
        "rule_ids": ["INTERP-CORRESPONDENCE-001", "LY-PALACE-001", "LY-RELATIVE-001", "CYCLE-XUN-001"],
    }


def _liuren(result: Dict[str, Any], imagery: Optional[Dict[str, Any]], category: str = "other") -> Dict[str, Any]:
    facts = result.get("facts", {})
    transmissions = facts.get("three_transmissions", {})
    month_general = facts.get("month_general", {})
    occupation = facts.get("occupation_time", {})
    imagery_rows = _imagery_for(imagery, "liuren")

    if transmissions.get("status") == "completed":
        t_vals = transmissions.get("transmissions", [])
        progression = f"课体为【{transmissions.get('lesson_type')}】，三传依次为：初传【{t_vals[0]}】（发端起因）、中传【{t_vals[1]}】（移易演变）、末传【{t_vals[2]}】（归结终局）。"
        verification = "分别核对事项当前触发诱因、中途执行演变与最终收尾条件，按过程逻辑稳步推进。"
    else:
        progression = f"本课进入【{transmissions.get('pending_path')}】，正在进一步完善深层传变规则。"
        verification = "遵循大六壬正统起例，重点关注天地盘神将生克与日干支寄宫。"

    transmission_rule = {
        "涉害": "LR-SHEHAI-001", "遥克": "LR-REMOTE-001", "昴星": "LR-STAR-001",
        "别责": "LR-BIEZE-001", "八专": "LR-BAZHUAN-001", "伏吟": "LR-FUYIN-001",
        "返吟": "LR-FANYIN-001",
    }.get(transmissions.get("lesson_type"), "LR-TRANSMISSION-001")

    images = "；".join(f"{row['symbol']}：{row['text']}" for row in imagery_rows)

    correspondence = (
        f"【天地盘与月将】最近中气为{month_general.get('boundary_term')}，以月将【{month_general.get('name')}】（{month_general.get('branch')}）加临占时【{occupation.get('branch')}】顺布天盘。"
        f"【四课三传】由{facts.get('day_pillar')}日干支定四课，{progression} "
        f"{('类象提示：' + images) if images else ''}"
    )

    return {
        "module": "liuren",
        "title": "大六壬：环境全景与因果三传",
        "chart_fact": f"{month_general.get('name')}将加临{occupation.get('branch')}时；{progression}",
        "correspondence": correspondence,
        "verification": verification,
        "evidence_refs": [row["candidate_id"] for row in imagery_rows],
        "rule_ids": ["INTERP-CORRESPONDENCE-001", "LR-PLATE-001", transmission_rule, "XIANG-BRANCH-001"],
    }


def _ziwei(result: Dict[str, Any], imagery: Optional[Dict[str, Any]], category: str = "other") -> Dict[str, Any]:
    facts = result.get("facts", {})
    ming_palace = facts.get("ming_palace", {})
    shen_palace = facts.get("shen_palace", {})
    bureau = facts.get("bureau", {})
    sihua = facts.get("si_hua", {})
    ming_p = next((p for p in facts.get("palaces_by_order", []) if p.get("name") == "命宫"), None)

    main_stars_str = "、".join(s["name"] for s in (ming_p.get("main_stars", []) if ming_p else [])) or "无主星"
    lucky_stars_str = "、".join(s["name"] for s in (ming_p.get("lucky_stars", []) if ming_p else [])) or "无"
    bad_stars_str = "、".join(s["name"] for s in (ming_p.get("bad_stars", []) if ming_p else [])) or "无"
    sihua_str = "、".join(f"{v}{k}" for k, v in sihua.items())

    correspondence = (
        f"【命身格局】命宫坐落于【{ming_palace.get('palace_stem_branch')}】，身宫在【{shen_palace.get('palace_stem_branch')}】，五行局定为【{bureau.get('name')}】（{bureau.get('nayin')}），命主{facts.get('ming_zhu')}，身主{facts.get('shen_zhu')}。"
        f"【命宫星曜】主星为【{main_stars_str}】，辅曜吉星为【{lucky_stars_str}】，煞曜为【{bad_stars_str}】。"
        f"【生年四化】配置为【{sihua_str}】。化禄主机遇丰盈，化权主掌控决断，化科主名声贵显，化忌主阻滞考验。"
    )

    return {
        "module": "ziwei",
        "title": "紫微斗数：命身格局与四化机运",
        "chart_fact": f"命宫在{ming_palace.get('palace_stem_branch')}（主星：{main_stars_str}），五行局为{bureau.get('name')}，生年四化：{sihua_str}。",
        "correspondence": correspondence,
        "verification": "结合命宫主星特质与生年四化落点，发挥长处规避化忌短板，合理把握起运大限节奏。",
        "evidence_refs": [],
        "rule_ids": ["ZW-CAL-001", "ZW-MING-001", "ZW-BUREAU-001", "ZW-STARS-001", "ZW-SIHUA-001"],
    }


def explain_correspondences(
    module_results: List[Dict[str, Any]],
    context: Optional[Dict[str, Any]],
    imagery: Optional[Dict[str, Any]] = None,
    yuan_hui: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    if not context:
        return None
    category = context.get("category", "other")
    question = context.get("question_summary", "").strip()

    modules = []
    builders = {
        "zhouyi": _zhouyi,
        "meihua": _meihua,
        "liuyao": _liuyao,
        "liuren": _liuren,
        "ziwei": _ziwei,
    }
    for module in ("zhouyi", "meihua", "liuyao", "liuren", "ziwei"):
        res = _find(module_results, module)
        if res:
            modules.append(builders[module](res, imagery, category))

    cross_layer = []
    if yuan_hui:
        facts = yuan_hui.get("facts", {})
        cross_layer.append({
            "title": "宏观时间背景（皇极经世）",
            "text": f"公历{facts.get('solar_year')}年在元会运世宏观周期中位于{facts.get('yuan', {}).get('label')}、{facts.get('hui', {}).get('label')}（{facts.get('hui', {}).get('branch')}会、五行{facts.get('hui', {}).get('element')}）、{facts.get('yun', {}).get('label')}、{facts.get('shi', {}).get('label')}，世内第{facts.get('shi', {}).get('year_in_shi')}年。提示宏观大运时代背景与中长周期趋势。",
            "evidence_refs": [item.get("evidence_id") for item in yuan_hui.get("evidence", [])],
            "rule_ids": ["INTERP-INTEGRATE-001", "YHYS-CYCLE-001", "YHYS-RELATION-001"],
        })

    return {
        "schema_version": "1.0",
        "status": "provisional_correspondence_explanation",
        "review_status": "unreviewed_deterministic_template",
        "context": {
            "category": category,
            "category_label": CATEGORY_LABELS.get(category, "当前事项"),
            "question_summary": question,
        },
        "headline": "卦象本质解析与所问事项全景映射",
        "summary": f"针对“{question}”（{CATEGORY_LABELS.get(category, '当前事项')}），系统综合{len(modules)}个推演系统（易经卦意、梅花体用、六爻世应、大六壬三传、紫微命局），从现状根基、动态演变、关键转折与潜在盲区多维度进行深度解析，提供清晰的研判结论与实践策略。",
        "modules": modules,
        "cross_layer": cross_layer,
        "verification_points": [item["verification"] for item in modules],
        "rule_ids": ["INTERP-CORRESPONDENCE-001", "INTERP-INTEGRATE-001"],
        "limitations": [
            "对应解释用于组织核实方向，不表示类象已经与现实对象一一确认。",
            "对应解释融合传统易学经典（彖象文言、纳甲六亲、体用生克、四化机理）与现代分析模型。",
            "未经专家签署，不从对应关系生成吉凶定论或现实概率保证，仅供辅助思考与风险排查。",
        ],
    }
