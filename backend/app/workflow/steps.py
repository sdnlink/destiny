"""7步排盘推理流程步骤实现。

每一步接收会话与前置步骤输出，返回结构化分析结果。
步骤间数据单向流动，后续步骤只能读取前面步骤的输出，不能回写修改。
"""

from typing import Any, Dict, List, Optional, Tuple

from app.common.categories import CATEGORY_LABELS, normalize_category
from app.common.five_elements import (
    FIVE_ELEMENTS_CONTROLS,
    FIVE_ELEMENTS_GENERATES,
    element_relation,
)
from app.common.ganzhi import (
    BRANCH_CLASH,
    BRANCH_COMBINE,
    BRANCH_ELEMENTS,
    EARTHLY_BRANCHES,
    branch_label,
)
from app.core.advisory import CATEGORY_PROFILES, generate_advisory
from app.core.hexagram_service import get_hexagram_explanation
from app.core.interpretation import (
    MODULE_LABELS,
    RELATION_MEANINGS,
    SPIRIT_MEANINGS,
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
        "category_label": CATEGORY_LABELS[normalize_category(session.category)],
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

# 梅花易数体用用神（键名与 app.common.categories 保持一致）
MEIHUA_YONGSHEN = {
    "career": {"yong": "用卦（官鬼/父母象）", "ti": "体卦", "logic": "梅花以体卦为自身，用卦为事项；事业看用卦是否生体、比和"},
    "finance": {"yong": "用卦（妻财象）", "ti": "体卦", "logic": "财运以体卦为自身，用卦为财；用生体/比和为得财之象"},
    "relationship": {"yong": "用卦（应象）", "ti": "体卦", "logic": "感情以体卦为自身，用卦为对方；体用生克关系反映互动"},
    "study": {"yong": "用卦（父母/文昌象）", "ti": "体卦", "logic": "学业以体卦为自身，用卦为成绩文书；用生体或比和者学业顺遂"},
    "lawsuit": {"yong": "用卦（官鬼象）", "ti": "体卦", "logic": "官司以体卦为己方，用卦为对方与公论；体克用者主可控，用克体者受制"},
    "travel": {"yong": "用卦（父母/驿马象）", "ti": "体卦", "logic": "出行以体卦为自身，用卦为行程；体生用者耗于路途，用生体者得助"},
    "missing_person": {"yong": "用卦（应象）", "ti": "体卦", "logic": "寻人以体卦为自身，用卦为对方所在；用生体者易寻，用克体者难遇"},
    "lost_item": {"yong": "用卦（妻财象）", "ti": "体卦", "logic": "失物以体卦为自身，用卦为失物；用生体或比和者易复得"},
    "health": {"yong": "用卦（官鬼／子孙象）", "ti": "体卦", "logic": "健康以体卦为自身，用卦为病气；体克用者可控，用克体者需严防"},
    "decision": {"yong": "用卦（对方/外部条件）", "ti": "体卦", "logic": "抉择以体卦为自身立场，用卦为外部条件；比较两者生克定取舍"},
    "other": {"yong": "用卦", "ti": "体卦", "logic": "通用以体卦为自身、用卦为事项，动爻为变化契机"},
}


HEXAGRAM_MODULES = ("meihua", "liuyao", "zhouyi")
DOMAIN_MODULES = ("bazi", "ziwei", "qimen", "liuren", "daliuren")

# 紫微斗数按事项取用事宫位（键与 app.common.categories 一致）
ZIWEI_CATEGORY_PALACES = {
    "career": ("官禄宫", "命宫", "紫微论事业以官禄宫为用事宫位，命宫看自身格局与承担力"),
    "finance": ("财帛宫", "命宫", "紫微论财运以财帛宫为用事宫位，兼看田宅与福德"),
    "relationship": ("夫妻宫", "命宫", "紫微论感情以夫妻宫为用事宫位，命宫看自身立场"),
    "study": ("官禄宫", "命宫", "紫微论学业考试以官禄宫为用事宫位，兼看文昌文曲与化科"),
    "lawsuit": ("官禄宫", "迁移宫", "紫微论官讼以官禄宫为用事宫位，迁移宫看外部对手与环境"),
    "travel": ("迁移宫", "命宫", "紫微论出行以迁移宫为用事宫位，命宫看自身准备"),
    "missing_person": ("交友宫", "迁移宫", "紫微论寻人以交友宫为用事宫位，迁移宫看对方动向"),
    "lost_item": ("田宅宫", "财帛宫", "紫微论失物以田宅宫为用事宫位，财帛宫看财物本体"),
    "health": ("疾厄宫", "命宫", "紫微论健康以疾厄宫为用事宫位，命宫看整体气数"),
    "decision": ("命宫", "迁移宫", "紫微论抉择以命宫为自身立场，迁移宫看外部条件与变动"),
    "other": ("命宫", "迁移宫", "紫微通用事项以命宫为自身，迁移宫看外部环境"),
}


def _present_modules(plate_data: Dict[str, Any]) -> set:
    systems = plate_data.get("systems") or []
    plates = plate_data.get("plates") or {}
    return set(systems) | set(plates.keys())


def _has_hexagram_system(plate_data: Dict[str, Any]) -> bool:
    return bool(_present_modules(plate_data) & set(HEXAGRAM_MODULES))


def _facts_of(plate_data: Dict[str, Any], module: str) -> Dict[str, Any]:
    return ((plate_data.get("plates") or {}).get(module) or {}).get("facts") or {}


def _domain_yongshen(plate_data: Dict[str, Any], category: str) -> Optional[Dict[str, str]]:
    """非卦象体系（八字/紫微/奇门/六壬）按各自口径定用神。

    这些体系没有六亲爻位，直接沿用「事业看官鬼爻」会把不存在的概念写进结论。
    只在本次没排梅花/六爻/周易时启用，卦象体系仍走原来的两套表。
    """
    present = _present_modules(plate_data)
    label = CATEGORY_LABELS[category]

    if "bazi" in present:
        strength = _facts_of(plate_data, "bazi").get("day_master_strength") or {}
        facts = _facts_of(plate_data, "bazi")
        favorable = strength.get("favorable_elements") or []
        unfavorable = strength.get("unfavorable_elements") or []
        day_master = facts.get("day_master") or strength.get("day_master") or ""
        primary = "喜用五行" + ("（{}）".format("、".join(favorable)) if favorable else "")
        secondary = "忌神五行" + ("（{}）".format("、".join(unfavorable)) if unfavorable else "")
        logic = (strength.get("analysis") or {}).get("summary") or "八字以日主强弱定喜忌，取喜用五行为用神"
        if day_master:
            logic = "日主为{}，{}".format(day_master, logic)
        return {
            "framework": "bazi",
            "framework_label": "八字命理",
            "primary": primary,
            "secondary": secondary,
            "logic": logic,
        }

    if "ziwei" in present:
        palace, east_west, logic = ZIWEI_CATEGORY_PALACES.get(category, ZIWEI_CATEGORY_PALACES["other"])
        return {
            "framework": "ziwei",
            "framework_label": "紫微斗数",
            "primary": "{}（{}用事宫）".format(palace, label),
            "secondary": east_west,
            "logic": logic,
        }

    if "qimen" in present:
        return {
            "framework": "qimen",
            "framework_label": "奇门遁甲",
            "primary": "日干（求测人）",
            "secondary": "时干（所测之事）",
            "logic": "奇门以日干为求测人、时干为所测之事，兼看值符值使与用神宫的门星神格局",
        }

    if "liuren" in present or "daliuren" in present:
        return {
            "framework": "liuren",
            "framework_label": "大六壬",
            "primary": "日干（求测人）",
            "secondary": "三传（事态脉络）",
            "logic": "大六壬以日干为求测人，三传为事态脉络：初传发端、中传经过、末传结果",
        }

    return None


def _domain_party_yongshen(framework_label: str) -> List[Dict[str, str]]:
    """非卦象体系的多方人物取象：用本体系符号，不用世爻/应爻。"""
    pairs = {
        "奇门遁甲": ("日干", "时干"),
        "大六壬": ("日干", "三传"),
        "八字命理": ("日主", "对应十神（配偶/财官）"),
        "紫微斗数": ("命宫", "夫妻宫/交友宫"),
    }
    self_symbol, other_symbol = pairs.get(framework_label, ("本体系用神", "本体系对应符号"))
    return [
        {"party": "求测人", "yongshen": self_symbol, "role": "自身立场、状态、能力"},
        {"party": "对方", "yongshen": other_symbol, "role": "对方立场、态度、动向"},
    ]


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
    category = normalize_category(session.category)
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

    # 没有卦象体系时，按本体系口径定用神；不要把六亲爻位写给八字/紫微/奇门/六壬
    domain = None if _has_hexagram_system(plate_data) else _domain_yongshen(plate_data, category)
    if domain:
        # 没有卦爻就没有世应：多方人物按本体系符号取象
        if party_yongshen:
            party_yongshen = _domain_party_yongshen(domain["framework_label"])
        yongshen_by_system[domain["framework"]] = {
            "primary": domain["primary"],
            "secondary": domain["secondary"],
            "logic": domain["logic"],
        }
        return {
            "step": 3,
            "name": "用神定位",
            "category": category,
            "category_label": CATEGORY_LABELS[category],
            "primary_yongshen": domain["primary"],
            "secondary_yongshen": domain["secondary"],
            "logic": domain["logic"],
            "yongshen_framework": domain["framework_label"],
            "yongshen_by_system": yongshen_by_system,
            "party_yongshen": party_yongshen,
        }

    return {
        "step": 3,
        "name": "用神定位",
        "category": category,
        "category_label": CATEGORY_LABELS[category],
        "primary_yongshen": liuyao_yong["primary"],
        "secondary_yongshen": liuyao_yong["secondary"],
        "logic": liuyao_yong["logic"],
        "yongshen_framework": "卦象体系",
        "yongshen_by_system": yongshen_by_system,
        "party_yongshen": party_yongshen,
    }


# ============================================================
# 步骤4：旺衰状态计算
# ============================================================

# 世应五行关系的读法（与体用关系同一套五行算法，但语义按世/应解读）
SHIYING_LABELS = {
    "same_element": "世应比和",
    "use_generates_body": "应生世",
    "body_generates_use": "世生应",
    "use_controls_body": "应克世",
    "body_controls_use": "世克应",
}


def _liuyao_line_chart(plate_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """取六爻纳甲爻表；非六爻盘返回空列表。"""
    facts = (plate_data.get("plates", {}).get("liuyao") or {}).get("facts", {})
    lines = facts.get("line_chart") or []
    return [line for line in lines if isinstance(line, dict)]


def _extract_moving_branches(plate_data: Dict[str, Any]) -> List[str]:
    """提取动爻地支（六爻纳甲为准）。"""
    branches = []
    for line in _liuyao_line_chart(plate_data):
        if line.get("is_moving"):
            branch = line.get("najia_branch") or ""
            if branch and branch not in branches:
                branches.append(branch)
    return branches


def _resolve_yongshen_element(plate_data: Dict[str, Any], primary: str) -> Tuple[str, str]:
    """按盘面推导用神五行。

    六亲五行随卦宫五行变化，因此不能使用固定的「六亲→五行」对照表：
    优先取用神所在爻的纳甲五行，其次取世/应爻，最后退回梅花用卦五行。
    """
    if not primary:
        return "", "未提供用神，无法推导五行"

    lines = _liuyao_line_chart(plate_data)
    candidates = []
    if lines:
        if primary in ("世爻", "世"):
            candidates = [line for line in lines if "世" in (line.get("roles") or [])]
        elif primary in ("应爻", "应") or "按关系" in primary:
            candidates = [line for line in lines if "应" in (line.get("roles") or [])]
        else:
            parts = [part.strip() for part in primary.split("/")]
            candidates = [line for line in lines if line.get("six_relative") in parts]
        if candidates:
            moving = [line for line in candidates if line.get("is_moving")]
            line = (moving or candidates)[0]
            element = line.get("element") or ""
            if element:
                note = "用神{}取第{}爻（{}，{}），纳甲地支{}属{}".format(
                    primary,
                    line.get("position", ""),
                    line.get("six_relative", ""),
                    "动爻" if line.get("is_moving") else "静爻",
                    line.get("najia_branch", ""),
                    element,
                )
                if len(candidates) > 1:
                    note += "；该用神两现，取{}".format("动爻" if moving else "首见之爻")
                return element, note

    meihua_facts = (plate_data.get("plates", {}).get("meihua") or {}).get("facts", {})
    body_use = meihua_facts.get("body_use") or {}
    use_trigram = body_use.get("use_trigram") or {}
    if use_trigram.get("element"):
        return use_trigram["element"], "梅花费数为用神，用卦{}属{}".format(
            use_trigram.get("name", ""), use_trigram["element"]
        )

    return "", "当前盘面缺少可用的用神定位依据（仅有卦象、无纳甲装卦）"


def _extract_shiying_relation(plate_data: Dict[str, Any]) -> Dict[str, Any]:
    """提取世应两爻及其五行关系。"""
    lines = _liuyao_line_chart(plate_data)
    shi = next((line for line in lines if "世" in (line.get("roles") or [])), None)
    ying = next((line for line in lines if "应" in (line.get("roles") or [])), None)
    if not shi or not ying:
        return {"note": "当前盘面无六爻纳甲，世应关系不适用"}
    result = {
        "shi": {
            "position": shi.get("position"),
            "six_relative": shi.get("six_relative"),
            "element": shi.get("element"),
            "branch": shi.get("najia_branch"),
        },
        "ying": {
            "position": ying.get("position"),
            "six_relative": ying.get("six_relative"),
            "element": ying.get("element"),
            "branch": ying.get("najia_branch"),
        },
    }
    shi_element = shi.get("element") or ""
    ying_element = ying.get("element") or ""
    if shi_element and ying_element:
        relation = element_relation(shi_element, ying_element)
        result["relation"] = {
            "code": relation["code"],
            "label": SHIYING_LABELS[relation["code"]],
            "meaning": RELATION_MEANINGS.get(relation["code"], ""),
        }
    return result


def _extract_ganzhi_interactions(moving_branches: List[str], day_branch: str, month_branch: str) -> List[Dict[str, Any]]:
    """动爻地支与日辰、月令的冲合关系。"""
    items = []
    for branch in moving_branches:
        clash = BRANCH_CLASH.get(branch, "")
        combine = BRANCH_COMBINE.get(branch, "")
        parts = []
        if clash and clash == day_branch:
            parts.append("与日辰{}相冲，事多变动".format(day_branch))
        if combine and combine == day_branch:
            parts.append("与日辰{}相合，事易牵连反复".format(day_branch))
        if clash and clash == month_branch:
            parts.append("与月令{}相冲，月内起伏明显".format(month_branch))
        if combine and combine == month_branch:
            parts.append("与月令{}相合，事有依托".format(month_branch))
        detail = "动爻{}".format(branch_label(branch))
        detail += "、".join("，" + part for part in parts) if parts else "，与日辰月令无冲合，应期以逢值逢冲论"
        items.append({
            "branch": branch,
            "day_relation": "冲" if clash and clash == day_branch else ("合" if combine and combine == day_branch else ""),
            "month_relation": "冲" if clash and clash == month_branch else ("合" if combine and combine == month_branch else ""),
            "detail": detail,
        })
    return items


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
    month_pillar = ganzhi.get("month", {}) or {}
    day_pillar = ganzhi.get("day", {}) or {}
    month_branch = month_pillar.get("branch", "") if isinstance(month_pillar, dict) else str(month_pillar)
    day_branch = day_pillar.get("branch", "") if isinstance(day_pillar, dict) else str(day_pillar)
    month_pillar_text = month_pillar.get("text", "") if isinstance(month_pillar, dict) else str(month_pillar)
    day_pillar_text = day_pillar.get("text", "") if isinstance(day_pillar, dict) else str(day_pillar)

    # 月令、日辰五行（地支五行唯一真源：app.common.ganzhi.BRANCH_ELEMENTS）
    month_element = BRANCH_ELEMENTS.get(month_branch, "")
    day_element = BRANCH_ELEMENTS.get(day_branch, "")

    # 用神五行按盘面推导：六亲爻/世应爻/用卦，绝不用固定对照表
    primary = yongshen_data.get("primary_yongshen", "")

    # 没有卦象体系时，旺衰/体用/世应这些卦象概念一律不适用，不硬套
    domain = None if _has_hexagram_system(plate_data) else _domain_yongshen(
        plate_data, normalize_category(session.category)
    )
    if domain:
        element = ""
        if domain["framework"] == "bazi":
            favorable = (_facts_of(plate_data, "bazi").get("day_master_strength") or {}).get("favorable_elements") or []
            element = favorable[0] if favorable else ""
        analysis_chain = [
            "本次盘面为{}，采用该体系用神：{}（不取卦爻六亲）。".format(domain["framework_label"], primary),
            domain["logic"],
            "未排梅花/六爻/周易，卦象旺衰、体用与世应关系不适用。",
        ]
        return {
            "step": 4,
            "name": "旺衰与生克分析",
            "calendar_context": {
                "month_pillar": month_pillar_text,
                "day_pillar": day_pillar_text,
                "month_branch": month_branch,
                "day_branch": day_branch,
                "month_element": month_element,
                "day_element": day_element,
            },
            "yongshen_wangshuai": {
                "yongshen": primary,
                "element": element,
                "element_source": domain["logic"],
                "level": "不适用",
                "reason": "{}不以月令定卦象旺衰".format(domain["framework_label"]),
            },
            "yongshen_framework": domain["framework_label"],
            "tiyong_relation": None,
            "shiying_relation": {"note": "当前盘面无六爻纳甲，世应关系不适用"},
            "ganzhi_interactions": [],
            "analysis_chain": analysis_chain,
            "rule_ids": [],
        }

    yongshen_element, element_source = _resolve_yongshen_element(plate_data, primary)

    wangshuai_level = "平"
    wangshuai_reason = ""
    if yongshen_element and month_element:
        if yongshen_element == month_element:
            wangshuai_level = "旺（得令）"
            wangshuai_reason = f"用神{yongshen_element}与月令{month_branch}（{month_element}）同气，得令而旺。"
        elif FIVE_ELEMENTS_GENERATES.get(month_element) == yongshen_element:
            wangshuai_level = "相（月令生用）"
            wangshuai_reason = f"月令{month_branch}（{month_element}）生用神{yongshen_element}，用神得生为相。"
        elif FIVE_ELEMENTS_GENERATES.get(yongshen_element) == month_element:
            wangshuai_level = "休（用神生月令）"
            wangshuai_reason = f"用神{yongshen_element}生月令{month_branch}（{month_element}），泄气为休。"
        elif FIVE_ELEMENTS_CONTROLS.get(month_element) == yongshen_element:
            wangshuai_level = "囚（月令克用）"
            wangshuai_reason = f"月令{month_branch}（{month_element}）克用神{yongshen_element}，受克为囚。"
        else:
            wangshuai_level = "死（用神克月令）"
            wangshuai_reason = f"用神{yongshen_element}克月令{month_branch}（{month_element}），耗力为死。"
    elif not yongshen_element:
        wangshuai_reason = element_source

    # 体用关系（梅花）：直接采用引擎已判定的五行关系，保证五类齐全且与引擎同源
    tiyong_relation = None
    meihua_facts = (plate_data.get("plates", {}).get("meihua") or {}).get("facts", {})
    body_use = meihua_facts.get("body_use") or {}
    relation = (meihua_facts.get("body_use_relation") or {}).get("original") or {}
    if body_use and relation.get("code"):
        code = relation["code"]
        tiyong_relation = {
            "code": code,
            "type": relation.get("label", ""),
            "body_element": (body_use.get("body_trigram") or {}).get("element", ""),
            "use_element": (body_use.get("use_trigram") or {}).get("element", ""),
            "meaning": RELATION_MEANINGS.get(code, ""),
        }

    # 世应关系（六爻）：从纳甲装卦结果提取世应两爻及其五行生克
    shiying_relation = _extract_shiying_relation(plate_data)

    # 干支冲合：动爻与日辰、月令的冲合关系
    moving_branches = _extract_moving_branches(plate_data)
    ganzhi_interactions = _extract_ganzhi_interactions(moving_branches, day_branch, month_branch)

    # 生克链条
    analysis_chain = []
    if wangshuai_reason:
        analysis_chain.append(wangshuai_reason)
    if element_source:
        analysis_chain.append("用神定位：" + element_source)
    if tiyong_relation:
        analysis_chain.append(f"体用关系：{tiyong_relation['type']}——{tiyong_relation['meaning']}")
    for item in ganzhi_interactions:
        analysis_chain.append(item["detail"])
    analysis_chain.append(f"日辰为{day_branch}（{day_element}），需结合日辰对用神的生克冲合作最终判断。")

    return {
        "step": 4,
        "name": "旺衰与生克分析",
        "calendar_context": {
            "month_pillar": month_pillar_text,
            "day_pillar": day_pillar_text,
            "month_branch": month_branch,
            "day_branch": day_branch,
            "month_element": month_element,
            "day_element": day_element,
        },
        "yongshen_wangshuai": {
            "yongshen": primary,
            "element": yongshen_element,
            "element_source": element_source,
            "level": wangshuai_level,
            "reason": wangshuai_reason,
        },
        "yongshen_framework": "卦象体系",
        "tiyong_relation": tiyong_relation,
        "shiying_relation": shiying_relation,
        "ganzhi_interactions": ganzhi_interactions,
        "analysis_chain": analysis_chain,
        "rule_ids": ["WF-YONGSHEN-001", "WF-WANGSHUAI-001"],
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
    category = normalize_category(session.category)
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
                "event_mapping": f"在{CATEGORY_LABELS[category]}事项中，此卦象提示：{summary}",
            })
        # 类别-specific 解读
        cat_field = f"{category}_interpretation"
        cat_interp = hexagram_explanation.get(cat_field, "")
        if cat_interp:
            symbol_mappings.append({
                "symbol": f"「{hexagram_name}」之{CATEGORY_LABELS[category]}象",
                "original_meaning": cat_interp,
                "event_mapping": cat_interp,
            })

    # 六神象义（六爻纳甲爻表中每爻的六神）
    seen_spirits = set()
    for line in _liuyao_line_chart(plate_data):
        spirit_name = line.get("six_spirit", "")
        if not spirit_name or spirit_name in seen_spirits or spirit_name not in SPIRIT_MEANINGS:
            continue
        seen_spirits.add(spirit_name)
        symbol_mappings.append({
            "symbol": f"六神「{spirit_name}」",
            "original_meaning": SPIRIT_MEANINGS[spirit_name],
            "event_mapping": f"在本事项中，{spirit_name}临第{line.get('position', '')}爻（{line.get('six_relative', '')}）提示：{SPIRIT_MEANINGS[spirit_name]}",
        })

    return {
        "step": 5,
        "name": "卦象符号事理解读" if hexagram_name else "盘面符号事理解读",
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
    category = normalize_category(session.category)
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

    # 没有卦象体系时，吉凶等级在规则口径下无法成立：不出分、给「未评级」
    domain = None if _has_hexagram_system(plate_data) else _domain_yongshen(plate_data, category)
    if domain:
        framework = domain["framework_label"]
        return {
            "step": 6,
            "name": "事态综合推演",
            "current_status": "事项处于{}范畴；本次以{}盘面为据，用神为{}，未取卦象用神。".format(
                CATEGORY_LABELS[category], framework, domain["primary"]
            ),
            "favorable": [],
            "obstacles": [],
            "trend": "未排梅花/六爻/周易，不作卦象吉凶与趋势推演；{}盘面的结构见步骤2盘面摘要，事项建议见顾问结论。".format(framework),
            "timing": None,
            "fortune_level": "未评级",
            "fortune_score": None,
            "fortune_basis": [
                "本次未排卦象体系（梅花/六爻/周易），按 WF-FORTUNE-001 的口径无法出具卦象吉凶等级",
                "{}用神：{}".format(framework, domain["primary"]),
            ],
            "yongshen_framework": framework,
            "synthesis": synthesis_result,
            "advisory": advisory_result,
            "imagery": imagery_result,
            "yuanhui": yuanhui_result,
            "literature": literature_result,
            "rule_ids": [],
        }

    # 吉凶等级判定（旺衰 + 体用五行关系；判定口径登记为 WF-FORTUNE-001）
    wangshuai_level = wangshuai_data.get("yongshen_wangshuai", {}).get("level", "平")
    tiyong = wangshuai_data.get("tiyong_relation", {}) or {}
    tiyong_code = tiyong.get("code", "")
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

    TIYONG_SCORE = {
        "use_generates_body": (2, "用生体，外部条件滋养自身"),
        "same_element": (1, "体用比和，同气相求"),
        "body_controls_use": (1, "体克用，自身可掌控局面"),
        "body_generates_use": (-1, "体生用，自身持续消耗"),
        "use_controls_body": (-2, "用克体，外部制约明显"),
    }
    if tiyong_code in TIYONG_SCORE:
        delta, text = TIYONG_SCORE[tiyong_code]
        score += delta
        basis.append(text)

    if score >= 3:
        fortune_level = "大吉"
    elif score >= 1:
        fortune_level = "小吉"
    elif score == -1:
        fortune_level = "小凶"
    elif score <= -2:
        fortune_level = "大凶"
    else:
        fortune_level = "平"

    # 当前现状
    current_status = f"事项处于{CATEGORY_LABELS[category]}范畴，用神{yongshen_data.get('primary_yongshen', '')}当前{wangshuai_level}。"
    if tiyong_type:
        current_status += f"体用关系为{tiyong_type}。"

    # 有利点
    favorable = []
    if "旺" in wangshuai_level or "相" in wangshuai_level:
        favorable.append("用神旺相，自身力量充足，具备推进条件")
    if tiyong_code in ("use_generates_body", "same_element", "body_controls_use"):
        favorable.append("体用关系有利，外部环境支持或自身可掌控局面")
    if not favorable:
        favorable.append("当前无明显有利因素，需谨慎观望")

    # 阻碍点
    obstacles = []
    if "囚" in wangshuai_level or "死" in wangshuai_level or "休" in wangshuai_level:
        obstacles.append("用神休囚死，力量不足，推进阻力较大")
    if tiyong_code == "body_generates_use":
        obstacles.append("体生用，自身精力/资源持续消耗，需控制投入")
    if tiyong_code == "use_controls_body":
        obstacles.append("用克体，外部规则或竞争持续压制，宜避其锋芒")
    if not obstacles:
        obstacles.append("当前无明显阻碍，但需注意细节变化")

    # 趋势与应期（基于动爻地支、日辰冲合、月令的专业推算）
    trend = _calculate_trend(category, wangshuai_level, tiyong_code, fortune_level)
    timing = _calculate_timing(plate_data, wangshuai_data, yongshen_data, fortune_level)

    return {
        "step": 6,
        "name": "事态综合推演",
        "current_status": current_status,
        "favorable": favorable,
        "obstacles": obstacles,
        "trend": trend,
        "timing": timing,
        "fortune_level": fortune_level,
        "fortune_score": score,
        "fortune_basis": basis,
        "synthesis": synthesis_result,
        "advisory": advisory_result,
        "imagery": imagery_result,
        "yuanhui": yuanhui_result,
        "literature": literature_result,
        "rule_ids": ["WF-WANGSHUAI-001", "WF-FORTUNE-001", "WF-TIMING-001"],
    }


# ============================================================
# 应期推算辅助函数（术数专业性深化）
# ============================================================

# 地支顺序、六冲、六合、三合局、地支五行统一取自 app.common.ganzhi，此处不再重复定义

# 月令对应节气（近似）
MONTH_BRANCH = {"寅": "立春", "卯": "惊蛰", "辰": "清明", "巳": "立夏", "午": "芒种", "未": "小暑",
                "申": "立秋", "酉": "白露", "戌": "寒露", "亥": "立冬", "子": "大雪", "丑": "小寒"}

TIYONG_TREND = {
    "use_generates_body": "用生体格局，外部环境持续滋养自身，长期趋势向好",
    "body_generates_use": "体生用格局，自身持续消耗于外，需注意资源透支风险",
    "use_controls_body": "用克体格局，外部压力较大，需防范突发阻碍",
    "body_controls_use": "体克用格局，自身可掌控局面，但需付出较大努力",
    "same_element": "体用比和，内外同频，事态平稳发展",
}


def _calculate_trend(category, wangshuai_level, tiyong_code, fortune_level):
    """基于用神旺衰、体用五行关系、吉凶等级推算发展趋势。"""
    parts = []
    if "旺" in wangshuai_level or "相" in wangshuai_level:
        parts.append("当前用神旺相，事态处于上升期，具备主动推进的力量基础")
    elif "休" in wangshuai_level:
        parts.append("用神休囚，事态处于平稳期，宜积蓄力量等待时机")
    elif "囚" in wangshuai_level or "死" in wangshuai_level:
        parts.append("用神囚死，事态处于下降期，阻力较大，宜守不宜攻")
    else:
        parts.append("用神力量中等，事态处于胶着期，需视具体变化决定进退")

    if tiyong_code in TIYONG_TREND:
        parts.append(TIYONG_TREND[tiyong_code])

    if fortune_level in ("大吉", "小吉"):
        parts.append("综合判断趋势偏吉，关键节点把握得当则可获有利结果")
    elif fortune_level in ("大凶", "小凶"):
        parts.append("综合判断趋势偏凶，需重点防范风险，必要时调整策略")
    else:
        parts.append("综合判断吉凶参半，宜稳扎稳打，不宜冒进也不宜过度保守")

    return "。".join(parts) + "。"


def _calculate_timing(plate_data, wangshuai_data, yongshen_data, fortune_level):
    """基于动爻地支、日辰冲合、月令推算具体应期时间窗口。

    应期法则：
    1. 动爻逢值（值日）、逢冲（对冲日）为近期应期
    2. 用神旺相则应期近，休囚则应期远
    3. 远应年月，近应日时
    """
    calendar = plate_data.get("calendar", {})
    ganzhi = calendar.get("ganzhi", {})
    day_branch = ganzhi.get("day", "")
    if isinstance(day_branch, dict):
        day_branch = day_branch.get("branch", "")
    month_branch = ganzhi.get("month", "")
    if isinstance(month_branch, dict):
        month_branch = month_branch.get("branch", "")

    # 动爻地支以六爻纳甲爻表为准
    moving_branches = _extract_moving_branches(plate_data)

    wangshuai_level = wangshuai_data.get("yongshen_wangshuai", {}).get("level", "平")

    timing_parts = []

    # 近期应期（日）
    if moving_branches:
        for mb in moving_branches[:2]:
            chong = BRANCH_CLASH.get(mb, "")
            combine = BRANCH_COMBINE.get(mb, "")
            line = f"动爻临「{mb}」，逢值（{mb}日）或逢冲（{chong}日）为近期应期"
            if combine:
                line += f"，逢合（{combine}日）多主牵连待解"
            timing_parts.append(line)
            if day_branch and day_branch in EARTHLY_BRANCHES and mb in EARTHLY_BRANCHES:
                day_idx = EARTHLY_BRANCHES.index(day_branch)
                days_to_value = (EARTHLY_BRANCHES.index(mb) - day_idx) % 12
                if chong in EARTHLY_BRANCHES:
                    days_to_chong = (EARTHLY_BRANCHES.index(chong) - day_idx) % 12
                    timing_parts.append(f"  距今日约{days_to_value}日逢值，约{days_to_chong}日逢冲")
                else:
                    timing_parts.append(f"  距今日约{days_to_value}日逢值")
    elif day_branch:
        timing_parts.append(f"无明确动爻，以日辰「{day_branch}」为基准，逢用神旺相之日应事")

    # 中期应期（月/节气）
    if month_branch:
        next_jieqi = MONTH_BRANCH.get(month_branch, "")
        month_label = f"月令「{month_branch}」（{next_jieqi}）" if next_jieqi else f"月令「{month_branch}」"
        timing_parts.append(f"{month_label}，月内用神得令则应期在本月，失令则待下月")

    # 旺衰决定应期远近
    if "旺" in wangshuai_level or "相" in wangshuai_level:
        timing_parts.append("用神旺相，应期偏近，重点关注7日内的变化")
    elif "休" in wangshuai_level:
        timing_parts.append("用神休囚，应期偏中，关注本月内节气交接前后")
    elif "囚" in wangshuai_level or "死" in wangshuai_level:
        timing_parts.append("用神囚死，应期偏远，需待用神得令之月（可能跨月或跨季）")
    else:
        timing_parts.append("用神力量中等，应期在近中远之间，需持续观察")

    # 吉凶对应期的影响
    if fortune_level in ("大凶", "小凶"):
        timing_parts.append("凶卦应期多为突发，需警惕近期（3日内）的意外变化")
    elif fortune_level in ("大吉", "小吉"):
        timing_parts.append("吉卦应期多为渐进，利好逐步兑现，不宜操之过急")

    timing_parts.append("注：应期为传统术数推算的参考时间窗口，实际兑现受人为决策与外部因素影响")

    return "\n".join(timing_parts)


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
    category = normalize_category(session.category)
    fortune = synthesis_data.get("fortune_level", "平")
    profile = CATEGORY_PROFILES.get(category, CATEGORY_PROFILES["other"])

    advice = []
    # 基于吉凶等级的通用建议
    if fortune == "未评级":
        framework = synthesis_data.get("yongshen_framework") or "所选体系"
        advice.append("本次未排卦象体系，{}盘面不输出卦象吉凶；建议以盘面事实与顾问结论为参考，按事项自身条件评估推进节奏。".format(framework))
    elif fortune in ("大吉", "小吉"):
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
