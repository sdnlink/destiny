"""Computational engine for BaZi (子平八字四柱命理与大运推演)."""

from typing import Any, Dict, List, Optional

from lunar_python import Solar

from app.calendar.engine import CalendarEngine
from app.calendar.timezone import parse_local_datetime

from .rules import (
    BRANCH_ELEMENTS,
    EARTHLY_BRANCHES,
    ELEMENT_GENERATED_BY,
    ELEMENT_GENERATING,
    ELEMENT_OVERCOME_BY,
    ELEMENT_OVERCOMING,
    HEAVENLY_STEMS,
    HIDDEN_STEMS_MAP,
    HUA_GAI_MAP,
    JIANG_XING_MAP,
    LU_SHEN,
    NAYIN_TABLE,
    SAN_HE_GROUP,
    STEM_ELEMENTS,
    STEM_POLARITY,
    TAO_HUA_MAP,
    TIAN_DE_MAP,
    TIAN_YI_DOC_MAP,
    TIAN_YI_GUI_REN,
    WEN_CHANG_GUI_REN,
    YANG_REN,
    YI_MA_MAP,
    YUE_DE_MAP,
    get_ten_god,
    get_twelve_stage,
)

RULE_VERSION = "bazi-ziping-core-v2.0"


def _sexagenary_pillars_cycle(start_ganzhi: str, direction: int, count: int = 8) -> List[str]:
    """根据月柱生成顺行(1)或逆行(-1)的大运干支序列。"""
    stem, branch = start_ganzhi[0], start_ganzhi[1]
    stem_idx = HEAVENLY_STEMS.index(stem)
    branch_idx = EARTHLY_BRANCHES.index(branch)

    result = []
    for i in range(1, count + 1):
        curr_stem = HEAVENLY_STEMS[(stem_idx + i * direction) % 10]
        curr_branch = EARTHLY_BRANCHES[(branch_idx + i * direction) % 12]
        result.append(f"{curr_stem}{curr_branch}")
    return result


def _calculate_shensha(
    day_stem: str,
    year_stem: str,
    month_stem: str,
    hour_stem: str,
    year_branch: str,
    month_branch: str,
    day_branch: str,
    hour_branch: str,
) -> Dict[str, List[str]]:
    """针对四柱各柱计算神煞。"""
    all_branches = {
        "year": year_branch,
        "month": month_branch,
        "day": day_branch,
        "hour": hour_branch,
    }
    all_stems = {
        "year": year_stem,
        "month": month_stem,
        "day": day_stem,
        "hour": hour_stem,
    }
    pillar_shensha: Dict[str, List[str]] = {k: [] for k in all_branches}

    # 1. 天乙贵人 (以日干和年干查)
    tian_yi_targets = set(TIAN_YI_GUI_REN.get(day_stem, ())) | set(TIAN_YI_GUI_REN.get(year_stem, ()))
    for p_name, br in all_branches.items():
        if br in tian_yi_targets:
            pillar_shensha[p_name].append("天乙贵人")

    # 2. 文昌贵人 (以日干和年干查)
    wen_chang_targets = {WEN_CHANG_GUI_REN.get(day_stem), WEN_CHANG_GUI_REN.get(year_stem)} - {None}
    for p_name, br in all_branches.items():
        if br in wen_chang_targets:
            pillar_shensha[p_name].append("文昌贵人")

    # 3. 羊刃 (以日干查)
    yang_ren_br = YANG_REN.get(day_stem)
    for p_name, br in all_branches.items():
        if br == yang_ren_br:
            pillar_shensha[p_name].append("羊刃")

    # 4. 禄神 (以日干查)
    lu_shen_br = LU_SHEN.get(day_stem)
    for p_name, br in all_branches.items():
        if br == lu_shen_br:
            pillar_shensha[p_name].append("禄神")

    # 5. 驿马、桃花、华盖、将星 (以年支和日支查)
    for ref_br in {year_branch, day_branch}:
        group_elem = SAN_HE_GROUP.get(ref_br)
        if group_elem:
            yi_ma = YI_MA_MAP.get(group_elem)
            tao_hua = TAO_HUA_MAP.get(group_elem)
            hua_gai = HUA_GAI_MAP.get(group_elem)
            jiang_xing = JIANG_XING_MAP.get(group_elem)

            for p_name, br in all_branches.items():
                if br == yi_ma and "驿马" not in pillar_shensha[p_name]:
                    pillar_shensha[p_name].append("驿马")
                if br == tao_hua and "桃花" not in pillar_shensha[p_name]:
                    pillar_shensha[p_name].append("桃花")
                if br == hua_gai and "华盖" not in pillar_shensha[p_name]:
                    pillar_shensha[p_name].append("华盖")
                if br == jiang_xing and "将星" not in pillar_shensha[p_name]:
                    pillar_shensha[p_name].append("将星")

    # 6. 天德、月德、天医 (以月令查)
    # 天德可能是天干也可能是地支，月德固定为天干：两者都要逐柱比对。
    tian_de = TIAN_DE_MAP.get(month_branch)
    yue_de = YUE_DE_MAP.get(month_branch)
    tian_yi_br = TIAN_YI_DOC_MAP.get(month_branch)

    for p_name, branch in all_branches.items():
        if tian_de and (all_stems[p_name] == tian_de or branch == tian_de):
            pillar_shensha[p_name].append("天德贵人")
        if yue_de and all_stems[p_name] == yue_de and "月德贵人" not in pillar_shensha[p_name]:
            pillar_shensha[p_name].append("月德贵人")
        if branch == tian_yi_br and "天医" not in pillar_shensha[p_name]:
            pillar_shensha[p_name].append("天医")

    return pillar_shensha


def _evaluate_day_master_strength(
    day_stem: str,
    month_branch: str,
    all_stems: List[str],
    all_hidden_stems: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """量化计算日主强弱、五行能量得分与喜用神。"""
    day_elem = STEM_ELEMENTS[day_stem]
    same_elem = day_elem
    gen_elem = ELEMENT_GENERATED_BY[day_elem]  # 生我者 (印星)
    drain_elem = ELEMENT_GENERATING[day_elem]  # 我生者 (食伤)
    opp_elem = ELEMENT_OVERCOME_BY[day_elem]   # 克我者 (官杀)
    wealth_elem = ELEMENT_OVERCOMING[day_elem] # 我克者 (财星)

    # 统计五行总分
    element_scores = {"木": 0.0, "火": 0.0, "土": 0.0, "金": 0.0, "水": 0.0}

    # 天干分值 (每个天干基础权重 10 分)
    for stem in all_stems:
        elem = STEM_ELEMENTS[stem]
        element_scores[elem] += 10.0

    # 地支藏干分值 (每个地支总权重 12 分，按权重分配，月令乘 1.5 倍权重系数)
    for idx, item in enumerate(all_hidden_stems):
        is_month_branch = (idx == 1)  # 第 2 个是月支
        branch_factor = 1.6 if is_month_branch else 1.0

        for h in item["hidden"]:
            h_elem = STEM_ELEMENTS[h["stem"]]
            element_scores[h_elem] += 12.0 * h["weight"] * branch_factor

    total_score = sum(element_scores.values()) or 1.0
    for k in element_scores:
        element_scores[k] = round(element_scores[k], 2)

    # 日主支持分 (同我比劫 + 生我印星)
    support_score = element_scores[same_elem] + element_scores[gen_elem]
    support_ratio = support_score / total_score

    # 得令分析
    month_elem = BRANCH_ELEMENTS[month_branch]
    de_ling = (month_elem == same_elem or month_elem == gen_elem)

    # 得地分析 (地支藏干中是否有比劫禄刃或强通根)
    de_di = any(
        h["stem"] == day_stem or STEM_ELEMENTS[h["stem"]] == same_elem
        for item in all_hidden_stems
        for h in item["hidden"]
    )

    # 判定强弱等级
    if support_ratio >= 0.65:
        level = "极旺"
    elif support_ratio >= 0.52:
        level = "偏旺"
    elif support_ratio >= 0.45:
        level = "中和"
    elif support_ratio >= 0.30:
        level = "偏弱"
    else:
        level = "极弱"

    # 判定喜用神与忌神
    if level in ("极旺", "偏旺"):
        favorable = [opp_elem, wealth_elem, drain_elem]
        unfavorable = [gen_elem, same_elem]
    else:
        favorable = [gen_elem, same_elem]
        unfavorable = [opp_elem, wealth_elem, drain_elem]

    distribution = [
        {
            "element": elem,
            "score": element_scores[elem],
            "percentage": round(element_scores[elem] / total_score * 100, 1),
        }
        for elem in ("木", "火", "土", "金", "水")
    ]

    return {
        "element_scores": element_scores,
        "element_distribution": distribution,
        "day_master_strength": {
            "day_master": day_stem,
            "element": day_elem,
            "score": round(support_ratio * 100, 1),
            "level": level,
            "favorable_elements": favorable,
            "unfavorable_elements": unfavorable,
            "analysis": {
                "de_ling": de_ling,
                "de_di": de_di,
                "support_ratio": round(support_ratio, 4),
                "summary": f"日主【{day_stem}{day_elem}】{level}。{'得令' if de_ling else '不得令'}，{'得地通根' if de_di else '根气较弱'}。喜用五行：{'、'.join(favorable)}；忌神五行：{'、'.join(unfavorable)}。",
            },
        },
    }


def _generate_bazi_advisory(day_master_info: Dict[str, Any], day_stem: str, pillars: Dict[str, Any]) -> Dict[str, str]:
    """生成八字格局与事项维度的综合研判建议。"""
    level = day_master_info["level"]
    fav = "、".join(day_master_info["favorable_elements"])
    unfav = "、".join(day_master_info["unfavorable_elements"])
    elem = day_master_info["element"]

    general = f"日元{day_stem}属{elem}，全局五行气象{level}。调候与立足之道以生助克泄平衡为基准，宜流通【{fav}】之气。"
    career = f"行事宜顺应【{fav}】行业与方位；在重大职涯决断上，保持稳步推进，避开【{unfav}】过旺之冲击。"
    wealth = "求财以稳健为主，命中喜用五行为生财之源，利于把握专业技能与长期积累带来的收益机会。"
    health = f"注意五行【{unfav}】所对应脏腑与经络的日常调理与养护，注重作息与气血调和。"

    return {
        "general": general,
        "career": career,
        "wealth": wealth,
        "health": health,
    }


def calculate_bazi(
    local_datetime: str,
    timezone: str = "Asia/Shanghai",
    gender: str = "男",
    longitude: Optional[float] = None,
    use_true_solar_time: bool = False,
) -> Dict[str, Any]:
    """执行子平八字四柱排盘、十神神煞、五行旺衰及大运推演。"""
    cal_engine = CalendarEngine()
    cal_result = cal_engine.calculate(
        local_datetime=local_datetime,
        timezone=timezone,
        longitude=longitude,
        use_true_solar_time=use_true_solar_time,
    )

    year_ganzhi = cal_result["ganzhi"]["year"]["text"]
    month_ganzhi = cal_result["ganzhi"]["month"]["text"]
    day_ganzhi = cal_result["ganzhi"]["day"]["text"]
    hour_ganzhi = cal_result["ganzhi"]["hour"]["text"]

    year_stem, year_branch = year_ganzhi[0], year_ganzhi[1]
    month_stem, month_branch = month_ganzhi[0], month_ganzhi[1]
    day_stem, day_branch = day_ganzhi[0], day_ganzhi[1]
    hour_stem, hour_branch = hour_ganzhi[0], hour_ganzhi[1]

    # 神煞计算
    shensha_map = _calculate_shensha(
        day_stem=day_stem,
        year_stem=year_stem,
        month_stem=month_stem,
        hour_stem=hour_stem,
        year_branch=year_branch,
        month_branch=month_branch,
        day_branch=day_branch,
        hour_branch=hour_branch,
    )

    # 各柱详情构建
    raw_pillars = [
        ("year", "年柱", year_ganzhi, year_stem, year_branch),
        ("month", "月柱", month_ganzhi, month_stem, month_branch),
        ("day", "日柱", day_ganzhi, day_stem, day_branch),
        ("hour", "时柱", hour_ganzhi, hour_stem, hour_branch),
    ]

    pillars_output: Dict[str, Any] = {}
    all_hidden_list = []

    for key, name, ganzhi, stem, branch in raw_pillars:
        stem_elem = STEM_ELEMENTS[stem]
        branch_elem = BRANCH_ELEMENTS[branch]
        stem_god = "日元" if key == "day" else get_ten_god(day_stem, stem)
        stage = get_twelve_stage(day_stem, branch)
        nayin = NAYIN_TABLE.get(ganzhi, "")

        hidden_defs = HIDDEN_STEMS_MAP.get(branch, ())
        hidden_details = []
        for h_stem, h_weight, h_type in hidden_defs:
            hidden_details.append({
                "stem": h_stem,
                "element": STEM_ELEMENTS[h_stem],
                "ten_god": get_ten_god(day_stem, h_stem),
                "weight": h_weight,
                "type": h_type,
            })

        all_hidden_list.append({"branch": branch, "hidden": hidden_details})

        pillars_output[key] = {
            "name": name,
            "stem": stem,
            "branch": branch,
            "ganzhi": ganzhi,
            "stem_element": stem_elem,
            "branch_element": branch_elem,
            "stem_ten_god": stem_god,
            "hidden_stems": hidden_details,
            "nayin": nayin,
            "twelve_stage": stage,
            "shensha": shensha_map.get(key, []),
        }

    # 日主强弱与五行分析
    all_stems = [year_stem, month_stem, day_stem, hour_stem]
    eval_result = _evaluate_day_master_strength(
        day_stem=day_stem,
        month_branch=month_branch,
        all_stems=all_stems,
        all_hidden_stems=all_hidden_list,
    )

    # 大运计算
    # 阳男阴女顺行，阴男阳女逆行
    year_polar = STEM_POLARITY[year_stem]
    is_forward = (year_polar == "阳" and gender == "男") or (year_polar == "阴" and gender == "女")
    direction = 1 if is_forward else -1

    # 起运岁数标准算法：3天1岁，1天4个月
    # 依据 solar_term_context 计算距离节令的时间差
    effective_dt = parse_local_datetime(local_datetime, timezone)
    solar_inst = Solar.fromYmdHms(
        effective_dt.year, effective_dt.month, effective_dt.day,
        effective_dt.hour, effective_dt.minute, effective_dt.second
    )
    lunar_inst = solar_inst.getLunar()
    eight_char = lunar_inst.getEightChar()
    eight_char.setSect(1)
    yun = eight_char.getYun(1 if gender == "男" else 0)
    start_year_offset = yun.getStartYear() or 3
    start_month_offset = yun.getStartMonth() or 0

    birth_year = effective_dt.year
    start_actual_year = birth_year + start_year_offset

    dayun_ganzhis = _sexagenary_pillars_cycle(month_ganzhi, direction, count=8)
    luck_pillars = []
    for idx, dy_gz in enumerate(dayun_ganzhis):
        dy_stem = dy_gz[0]
        dy_god = get_ten_god(day_stem, dy_stem)
        s_age = start_year_offset + idx * 10
        e_age = s_age + 9
        s_yr = start_actual_year + idx * 10
        e_yr = s_yr + 9
        luck_pillars.append({
            "index": idx + 1,
            "ganzhi": dy_gz,
            "stem_ten_god": dy_god,
            "start_age": s_age,
            "end_age": e_age,
            "start_year": s_yr,
            "end_year": e_yr,
            "nayin": NAYIN_TABLE.get(dy_gz, ""),
        })

    advisory = _generate_bazi_advisory(eval_result["day_master_strength"], day_stem, pillars_output)

    # 规范化结果
    facts = {
        "day_master": day_stem,
        "day_master_element": STEM_ELEMENTS[day_stem],
        "gender": gender,
        "pillars": pillars_output,
        "day_master_strength": eval_result["day_master_strength"],
        "element_distribution": eval_result["element_distribution"],
        "luck_start_info": {
            "start_age": start_year_offset,
            "start_month": start_month_offset,
            "direction": "顺行" if is_forward else "逆行",
            "start_year": start_actual_year,
            "description": f"出生后 {start_year_offset} 岁 {start_month_offset} 个月起运，大运【{'顺行' if is_forward else '逆行'}】。",
        },
        "luck_pillars": luck_pillars,
    }

    return {
        "rule_id": RULE_VERSION,
        "system": "bazi",
        "gender": gender,
        "solar_datetime": cal_result["time"]["effective_local_datetime"],
        "lunar_datetime": f"{cal_result['lunar']['year']}年 {'(闰)' if cal_result['lunar']['is_leap_month'] else ''}{cal_result['lunar']['month_name']}月{cal_result['lunar']['day_name']}",
        "day_master": day_stem,
        "facts": facts,
        "element_scores": eval_result["element_scores"],
        "element_distribution": eval_result["element_distribution"],
        "day_master_strength": eval_result["day_master_strength"],
        "all_shensha": shensha_map,
        "luck_start_info": facts["luck_start_info"],
        "luck_pillars": luck_pillars,
        "advisory": advisory,
    }


def auto_cast(
    local_datetime: str,
    cast_nonce: str,
    timezone: str = "Asia/Shanghai",
    gender: str = "男",
    longitude: Optional[float] = None,
    use_true_solar_time: bool = False,
) -> Dict[str, Any]:
    """根据确定性哈希与时间生成八字排盘。"""
    res = calculate_bazi(
        local_datetime=local_datetime,
        timezone=timezone,
        gender=gender,
        longitude=longitude,
        use_true_solar_time=use_true_solar_time,
    )
    res["cast_nonce"] = cast_nonce
    return res


def time_cast(
    local_datetime: str,
    timezone: str = "Asia/Shanghai",
    gender: str = "男",
    longitude: Optional[float] = None,
    use_true_solar_time: bool = False,
) -> Dict[str, Any]:
    """时间起盘八字推演。"""
    return calculate_bazi(
        local_datetime=local_datetime,
        timezone=timezone,
        gender=gender,
        longitude=longitude,
        use_true_solar_time=use_true_solar_time,
    )
