"""7步排盘推理流程步骤实现。

每一步接收会话与前置步骤输出，返回结构化分析结果。
步骤间数据单向流动，后续步骤只能读取前面步骤的输出，不能回写修改。
"""

from typing import Any, Dict, List, Optional, Tuple

from app.core.advisory import CATEGORY_PROFILES, generate_advisory
from app.core.hexagram_service import get_hexagram_explanation
from app.core.interpretation import (
    CATEGORY_LABELS,
    MODULE_LABELS,
    RELATIVE_MEANINGS,
    RELATION_MEANINGS,
    SPIRIT_MEANINGS,
    explain_correspondences,
)
from app.core.imagery import collect_imagery
from app.core.literature import collect_literature_opinions
from app.core.synthesis import synthesize
from app.core.yuanhui import analyze_yuan_hui_yun_shi


# ============================================================
# 步骤1：信息校验 & 起盘数据源确认
# ============================================================

def step1_info_validation(session) -> Dict[str, Any]:
    """校验求测信息与起盘素材，输出信息确认结果。

    Returns:
        {
            "question": 求测事由,
            "casting_method": 起盘方式,
            "casting_source": 起盘所用时间/数字,
            "system": 术数门类,
            "missing_fields": 缺失字段列表,
            "ready": 是否可进入排盘,
        }
    """
    missing = []
    if not session.question or not session.question.strip():
        missing.append("求测事由")
    if not session.casting_source.get("local_datetime") and session.casting_method in ("auto", "time"):
        missing.append("起盘时间")
    if session.casting_method == "numbers" and not session.casting_source.get("numbers"):
        missing.append("报数")

    return {
        "step": 1,
        "name": "信息校验与起盘数据源确认",
        "question": session.question,
        "category": session.category,
        "category_label": CATEGORY_LABELS.get(session.category, session.category),
        "casting_method": session.casting_method,
        "casting_source": session.casting_source,
        "system": session.system,
        "user_profile": session.user_profile,
        "missing_fields": missing,
        "ready": len(missing) == 0,
    }


# ============================================================
# 步骤2：完整排盘输出（由 engine.py 调用 casting.py 后填充）
# ============================================================

def step2_format_plate(module_results: List[Dict[str, Any]], systems_used: List[str]) -> Dict[str, Any]:
    """格式化排盘结果为客观盘面数据（不加入主观判断）。

    Returns:
        {
            "step": 2,
            "name": "完整排盘输出",
            "systems": 使用的术数体系,
            "plates": 各体系盘面客观数据,
            "calendar": 历法基线数据,
        }
    """
    plates = {}
    calendar_data = None
    for item in module_results:
        module = item["module"]
        result = item["result"]
        if module == "calendar":
            calendar_data = result
        else:
            plates[module] = {
                "system_label": MODULE_LABELS.get(module, module),
                "facts": result.get("facts", {}),
                "calculation_trace": result.get("calculation_trace", []),
                "steps": result.get("steps", []),
                "warnings": result.get("warnings", []),
                "engine_version": result.get("engine_version", ""),
                "rule_version": result.get("rule_version", ""),
            }
    return {
        "step": 2,
        "name": "完整排盘输出",
        "systems": systems_used,
        "plates": plates,
        "calendar": calendar_data,
    }


# ============================================================
# 步骤3：定用神，锁定分析焦点
# ============================================================

# 事项类别 → 用神映射（六爻体系）
CATEGORY_YONGSHEN = {
    "career": {"primary": "官鬼", "secondary": "父母", "logic": "事业看官鬼爻（职权、考核、压力），父母爻为文书资质、单位平台"},
    "finance": {"primary": "妻财", "secondary": "子孙", "logic": "财运看妻财爻（资金、收益、标的），子孙爻为财源、客户"},
    "relationship": {"primary": "应爻", "secondary": "妻财/官鬼", "logic": "感情看应爻（对方），男测妻财为用神，女测官鬼为用神"},
    "study": {"primary": "父母", "secondary": "官鬼", "logic": "考试学业看父母爻（文书、成绩、录取），官鬼为名次、压力"},
    "lawsuit": {"primary": "官鬼", "secondary": "父母", "logic": "官司看官鬼爻（官方、诉讼、责罚），父母爻为文书证据"},
    "travel": {"primary": "父母", "secondary": "世爻", "logic": "出行看父母爻（车船、行程、证件），世爻为自身状态"},
    "missing_person": {"primary": "用神（按关系）", "secondary": "应爻", "logic": "寻人按人物关系定用神，应爻为对方所在、动向"},
    "lost_item": {"primary": "妻财", "secondary": "子孙", "logic": "失物看妻财爻（失物本身），子孙为寻找方向、找回可能"},
    "health": {"primary": "官鬼", "secondary": "子孙", "logic": "健康看官鬼爻（病神、病灶），子孙爻为医药、康复"},
    "decision": {"primary": "世爻", "secondary": "应爻", "logic": "抉择看世爻（自身立场、能力）与应爻（对方/外部条件）对比"},
    "other": {"primary": "世爻", "secondary": "应爻", "logic": "通用事项以世爻为自身、应爻为外部环境，结合卦象综合判断"},
}

# 梅花易数体用用神
MEIHUA_YONGSHEN = {
    "career": {"yong": "用卦（官鬼/父母象）", "ti": "体卦", "logic": "梅花以体卦为自身，用卦为事项；事业看用卦是否生体、比和"},
    "finance": {"yong": "用卦（妻财象）", "ti": "体卦", "logic": "财运以体卦为自身，用卦为财；用生体/比和为得财之象"},
    "relationship": {"yong": "用卦（应象）", "ti": "体卦", "logic": "感情以体卦为自身，用卦为对方；体用生克关系反映互动"},
    "other": {"yong": "用卦", "ti": "体卦", "logic": "通用以体卦为自身、用卦为事项，动爻为变化契机"},
}


def step3_identify_yongshen(session, plate_data: Dict[str, Any]) -> Dict[str, Any]:
    """定用神，锁定分析焦点。多人事件列出各方对应用神。

    Returns:
        {
            "step": 3,
            "name": "用神定位",
            "category": 事项类别,
            "primary_yongshen": 主用神,
            "secondary_yongshen": 辅助用神,
            "logic": 取用理由,
            "party_yongshen": 多方人物用神（如有）,
        }
    """
    category = session.category
    liuyao_yong = CATEGORY_YONGSHEN.get(category, CATEGORY_YONGSHEN["other"])
    meihua_yong = MEIHUA_YONGSHEN.get(category, MEIHUA_YONGSHEN["other"])

    # 多方人物取象（如果用户描述中涉及多人）
    party_yongshen = []
    question = session.question or ""
    if any(kw in question for kw in ["双方", "两人", "对方", "合作", "竞争", "夫妻", "男女朋友"]):
        party_yongshen = [
            {"party": "求测人（世爻/体卦）", "yongshen": "世爻", "role": "自身立场、状态、能力"},
            {"party": "对方（应爻/用卦）", "yongshen": "应爻", "role": "对方立场、态度、动向"},
        ]

    systems = plate_data.get("systems", [])
    yongshen_by_system = {}
    if "meihua" in systems:
        yongshen_by_system["meihua"] = meihua_yong
    if "liuyao" in systems:
        yongshen_by_system["liuyao"] = liuyao_yong

    return {
        "step": 3,
        "name": "用神定位",
        "category": category,
        "category_label": CATEGORY_LABELS.get(category, category),
        "primary_yongshen": liuyao_yong["primary"],
        "secondary_yongshen": liuyao_yong["secondary"],
        "logic": liuyao_yong["logic"],
        "yongshen_by_system": yongshen_by_system,
        "party_yongshen": party_yongshen,
    }


# ============================================================
# 步骤4：旺衰状态计算
# ============================================================

def step4_wangshuai_analysis(session, plate_data: Dict[str, Any], yongshen_data: Dict[str, Any]) -> Dict[str, Any]:
    """计算用神、体用、世应、关键干支旺衰。

    参考月令日辰、得地得势得令、休囚死墓绝、冲合刑害生克。
    逐条写清生克链条。

    Returns:
        {
            "step": 4,
            "name": "旺衰与生克分析",
            "calendar_context": 月令日辰,
            "yongshen_wangshuai": 用神旺衰,
            "tiyong_relation": 体用关系（梅花）,
            "shiying_relation": 世应关系（六爻）,
            "ganzhi_interactions": 干支冲合刑害,
            "analysis_chain": 生克链条分析,
        }
    """
    calendar = plate_data.get("calendar") or {}
    ganzhi = calendar.get("ganzhi", {})
    month_pillar = ganzhi.get("month", {})
    day_pillar = ganzhi.get("day", {})
    month_branch = month_pillar.get("branch", "")
    day_branch = day_pillar.get("branch", "")

    # 月令五行
    BRANCH_ELEMENT = {
        "寅": "木", "卯": "木", "巳": "火", "午": "火",
        "申": "金", "酉": "金", "亥": "水", "子": "水",
        "辰": "土", "戌": "土", "丑": "土", "未": "土",
    }
    month_element = BRANCH_ELEMENT.get(month_branch, "")
    day_element = BRANCH_ELEMENT.get(day_branch, "")

    # 用神五行（基于类别推断）
    YONGSHEN_ELEMENT = {
        "官鬼": "木",  # 官鬼克我，需结合日干
        "妻财": "土",  # 我克者为财
        "父母": "水",  # 生我者为父母
        "子孙": "金",  # 我生者为子孙
        "兄弟": "火",  # 同我者为兄弟
    }
    primary = yongshen_data.get("primary_yongshen", "")
    yongshen_element = YONGSHEN_ELEMENT.get(primary, "")

    # 旺衰判断（简化：月令生扶为旺，克泄为衰）
    ELEMENT_SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
    ELEMENT_KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

    wangshuai_level = "平"
    wangshuai_reason = ""
    if yongshen_element and month_element:
        if yongshen_element == month_element:
            wangshuai_level = "旺（得令）"
            wangshuai_reason = f"用神{yongshen_element}与月令{month_branch}（{month_element}）同气，得令而旺。"
        elif ELEMENT_SHENG.get(month_element) == yongshen_element:
            wangshuai_level = "相（月令生用）"
            wangshuai_reason = f"月令{month_branch}（{month_element}）生用神{yongshen_element}，用神得生为相。"
        elif ELEMENT_KE.get(month_element) == yongshen_element:
            wangshuai_level = "休（用神生月令）"
            wangshuai_reason = f"用神{yongshen_element}生月令{month_branch}（{month_element}），泄气为休。"
        elif ELEMENT_KE.get(yongshen_element) == month_element:
            wangshuai_level = "囚（月令克用）"
            wangshuai_reason = f"月令{month_branch}（{month_element}）克用神{yongshen_element}，受克为囚。"
        else:
            wangshuai_level = "死（用神克月令）"
            wangshuai_reason = f"用神{yongshen_element}克月令{month_branch}（{month_element}），耗力为死。"

    # 体用关系（梅花）
    tiyong_relation = None
    meihua_plate = plate_data.get("plates", {}).get("meihua", {})
    facts = meihua_plate.get("facts", {})
    if facts:
        body_trigram = facts.get("body_trigram") or facts.get("ti_trigram")
        use_trigram = facts.get("use_trigram") or facts.get("yong_trigram")
        if body_trigram and use_trigram:
            body_elem = body_trigram.get("element", "") if isinstance(body_trigram, dict) else ""
            use_elem = use_trigram.get("element", "") if isinstance(use_trigram, dict) else ""
            if body_elem == use_elem:
                tiyong_relation = {"type": "比和", "meaning": RELATION_MEANINGS["same_element"]}
            elif ELEMENT_SHENG.get(use_elem) == body_elem:
                tiyong_relation = {"type": "用生体", "meaning": RELATION_MEANINGS["use_generates_body"]}
            elif ELEMENT_SHENG.get(body_elem) == use_elem:
                tiyong_relation = {"type": "体生用", "meaning": RELATION_MEANINGS["body_generates_use"]}

    # 生克链条
    analysis_chain = []
    if wangshuai_reason:
        analysis_chain.append(wangshuai_reason)
    if tiyong_relation:
        analysis_chain.append(f"体用关系：{tiyong_relation['type']}——{tiyong_relation['meaning']}")
    analysis_chain.append(f"日辰为{day_branch}（{day_element}），需结合日辰对用神的生克冲合作最终判断。")

    return {
        "step": 4,
        "name": "旺衰与生克分析",
        "calendar_context": {
            "month_pillar": month_pillar,
            "day_pillar": day_pillar,
            "month_branch": month_branch,
            "day_branch": day_branch,
            "month_element": month_element,
            "day_element": day_element,
        },
        "yongshen_wangshuai": {
            "yongshen": primary,
            "element": yongshen_element,
            "level": wangshuai_level,
            "reason": wangshuai_reason,
        },
        "tiyong_relation": tiyong_relation,
        "shiying_relation": {"note": "六爻世应关系需从纳甲装卦结果中提取世爻应爻位置与生克关系"},
        "analysis_chain": analysis_chain,
    }


# ============================================================
# 步骤5：象义拆解推理
# ============================================================

def step5_xiangyi_deduction(session, plate_data: Dict[str, Any], yongshen_data: Dict[str, Any]) -> Dict[str, Any]:
    """提取卦爻星门神煞传统象义，翻译映射到用户现实事件。

    禁止单纯摘抄古文，符号含义必须结合测事场景。

    Returns:
        {
            "step": 5,
            "name": "卦象符号事理解读",
            "hexagram_meaning": 卦象释义,
            "symbol_mappings": 符号→现实事件映射,
            "correspondences": 事项对应解释,
        }
    """
    category = session.category
    plates = plate_data.get("plates", {})

    # 提取主卦信息
    hexagram_name = ""
    hexagram_explanation = None
    for module_key in ("meihua", "zhouyi", "liuyao"):
        plate = plates.get(module_key, {})
        facts = plate.get("facts", {})
        original = facts.get("original") or facts.get("original_hexagram")
        if original:
            hexagram_name = original.get("name", "") if isinstance(original, dict) else str(original)
            break

    if hexagram_name:
        try:
            hexagram_explanation = get_hexagram_explanation(hexagram_name)
        except Exception:
            hexagram_explanation = None

    # 符号映射
    symbol_mappings = []
    if hexagram_explanation:
        summary = hexagram_explanation.get("summary", "")
        if summary:
            symbol_mappings.append({
                "symbol": f"本卦「{hexagram_name}」",
                "original_meaning": summary,
                "event_mapping": f"在{CATEGORY_LABELS.get(category, category)}事项中，此卦象提示：{summary}",
            })
        # 类别-specific 解读
        cat_field = f"{category}_interpretation"
        cat_interp = hexagram_explanation.get(cat_field, "")
        if cat_interp:
            symbol_mappings.append({
                "symbol": f"「{hexagram_name}」之{CATEGORY_LABELS.get(category, category)}象",
                "original_meaning": cat_interp,
                "event_mapping": cat_interp,
            })

    # 六神象义（如果六爻结果中有）
    liuyao_plate = plates.get("liuyao", {})
    liuyao_facts = liuyao_plate.get("facts", {})
    six_spirits = liuyao_facts.get("six_spirits") or liuyao_facts.get("liushen")
    if six_spirits:
        for spirit in six_spirits if isinstance(six_spirits, list) else []:
            spirit_name = spirit if isinstance(spirit, str) else spirit.get("name", "")
            if spirit_name in SPIRIT_MEANINGS:
                symbol_mappings.append({
                    "symbol": f"六神「{spirit_name}」",
                    "original_meaning": SPIRIT_MEANINGS[spirit_name],
                    "event_mapping": f"在本事项中，{spirit_name}临爻提示：{SPIRIT_MEANINGS[spirit_name]}",
                })

    return {
        "step": 5,
        "name": "卦象符号事理解读",
        "hexagram_name": hexagram_name,
        "hexagram_explanation": hexagram_explanation,
        "symbol_mappings": symbol_mappings,
    }


# ============================================================
# 步骤6：综合吉凶定性 & 事态推演
# ============================================================

def step6_synthesis_judgement(
    session,
    module_results: List[Dict[str, Any]],
    plate_data: Dict[str, Any],
    yongshen_data: Dict[str, Any],
    wangshuai_data: Dict[str, Any],
    xiangyi_data: Dict[str, Any],
) -> Dict[str, Any]:
    """综合吉凶定性与事态推演。

    1. 当前现状
    2. 发展趋势，有利因素、阻碍问题
    3. 参考应期时间段
    4. 吉凶等级：大吉/小吉/平/小凶/大凶，附带判定依据

    Returns:
        {
            "step": 6,
            "name": "事态综合推演",
            "current_status": 当前现状,
            "favorable": 有利点,
            "obstacles": 阻碍点,
            "trend": 发展趋势,
            "timing": 参考应期,
            "fortune_level": 吉凶等级,
            "fortune_basis": 判定依据,
            "synthesis": 多体系综合研判,
            "advisory": 事项建议,
            "imagery": 类象候选,
            "yuanhui": 元会运世背景,
            "literature": 文献引证,
        }
    """
    category = session.category
    context = {"category": category, "question_summary": session.question}

    # 调用现有综合研判
    try:
        synthesis_result = synthesize(module_results)
    except Exception:
        synthesis_result = {"note": "综合研判数据不足，基于单模块分析"}

    # 类象
    try:
        imagery_result = collect_imagery(module_results, context)
    except Exception:
        imagery_result = {}

    # 元会运世
    try:
        yuanhui_result = analyze_yuan_hui_yun_shi(module_results)
    except Exception:
        yuanhui_result = {}

    # 文献引证
    try:
        literature_result = collect_literature_opinions(module_results, context=context)
    except Exception:
        literature_result = {}

    # 事项建议
    try:
        advisory_result = generate_advisory(module_results, context)
    except Exception:
        advisory_result = {}

    # 吉凶等级判定（基于旺衰 + 体用关系 + 综合研判极性）
    wangshuai_level = wangshuai_data.get("yongshen_wangshuai", {}).get("level", "平")
    tiyong = wangshuai_data.get("tiyong_relation", {}) or {}
    tiyong_type = tiyong.get("type", "")

    score = 0
    basis = []
    if "旺" in wangshuai_level or "相" in wangshuai_level:
        score += 2
        basis.append(f"用神{wangshuai_level}，力量充足")
    elif "囚" in wangshuai_level or "死" in wangshuai_level:
        score -= 2
        basis.append(f"用神{wangshuai_level}，力量不足")
    else:
        basis.append(f"用神{wangshuai_level}，力量中等")

    if tiyong_type == "用生体":
        score += 2
        basis.append("用生体，外部条件滋养自身")
    elif tiyong_type == "比和":
        score += 1
        basis.append("体用比和，同气相求")
    elif tiyong_type == "体生用":
        score -= 1
        basis.append("体生用，自身持续消耗")

    if score >= 3:
        fortune_level = "大吉"
    elif score >= 1:
        fortune_level = "小吉"
    elif score == 0:
        fortune_level = "平"
    elif score >= -1:
        fortune_level = "小凶"
    else:
        fortune_level = "大凶"

    # 当前现状
    current_status = f"事项处于{CATEGORY_LABELS.get(category, category)}范畴，用神{yongshen_data.get('primary_yongshen', '')}当前{wangshuai_level}。"
    if tiyong_type:
        current_status += f"体用关系为{tiyong_type}。"

    # 有利点
    favorable = []
    if "旺" in wangshuai_level or "相" in wangshuai_level:
        favorable.append("用神旺相，自身力量充足，具备推进条件")
    if tiyong_type in ("用生体", "比和"):
        favorable.append("体用关系有利，外部环境支持或与自身同频")
    if not favorable:
        favorable.append("当前无明显有利因素，需谨慎观望")

    # 阻碍点
    obstacles = []
    if "囚" in wangshuai_level or "死" in wangshuai_level or "休" in wangshuai_level:
        obstacles.append("用神休囚死，力量不足，推进阻力较大")
    if tiyong_type == "体生用":
        obstacles.append("体生用，自身精力/资源持续消耗，需控制投入")
    if not obstacles:
        obstacles.append("当前无明显阻碍，但需注意细节变化")

    # 趋势与应期
    trend = "事态将随用神旺衰变化而演变，当前阶段宜根据用神力量决定进退。"
    timing = "参考应期：近则7日内（动爻逢值逢冲），远则按月令节气交接前后观察变化。具体应期需结合动爻地支与日辰冲合确定。"

    return {
        "step": 6,
        "name": "事态综合推演",
        "current_status": current_status,
        "favorable": favorable,
        "obstacles": obstacles,
        "trend": trend,
        "timing": timing,
        "fortune_level": fortune_level,
        "fortune_basis": basis,
        "synthesis": synthesis_result,
        "advisory": advisory_result,
        "imagery": imagery_result,
        "yuanhui": yuanhui_result,
        "literature": literature_result,
    }


# ============================================================
# 步骤7：行动建议与免责提示
# ============================================================

def step7_advice_and_disclaimer(session, synthesis_data: Dict[str, Any]) -> Dict[str, Any]:
    """输出可落地趋吉避凶现实建议 + 免责提示。

    Returns:
        {
            "step": 7,
            "name": "趋吉避凶建议",
            "advice": 建议列表,
            "disclaimer": 免责提示,
        }
    """
    category = session.category
    fortune = synthesis_data.get("fortune_level", "平")
    profile = CATEGORY_PROFILES.get(category, CATEGORY_PROFILES["other"])

    advice = []
    # 基于吉凶等级的通用建议
    if fortune in ("大吉", "小吉"):
        advice.append("当前卦象有利，可在用神旺相时段积极推进，但仍需核实关键细节，避免因顺境疏忽。")
    elif fortune == "平":
        advice.append("当前吉凶参半，宜稳扎稳打，不宜冒进；先小范围验证再扩大投入。")
    else:
        advice.append("当前卦象有阻，宜暂缓重大决策，优先排查风险点，待用神得令或外部条件转变后再行推进。")

    # 类别-specific 建议
    for title, detail in profile.get("recommendations", []):
        advice.append(f"{title}：{detail}")

    # 核实清单
    questions = profile.get("questions", [])
    if questions:
        advice.append("核实清单：" + "；".join(questions))

    disclaimer = "以上为传统易经术数文化推演，仅作参考，现实中请结合自身实际理性判断。推演结果不构成任何决策依据，最终结果取决于个人选择与客观现实。"

    return {
        "step": 7,
        "name": "趋吉避凶建议",
        "advice": advice,
        "disclaimer": disclaimer,
    }
