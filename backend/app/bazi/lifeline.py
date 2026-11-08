"""个人生平时间轴：子平法、岁运（大运/流年）、皇极经世的确定性事实对齐。

依据库内原典（data/generated/wikisource-corpus）：
- 《淵海子平·宝法第二》：「子平之法，以日为主；先看提纲为重，次用年日时支，
  合成格局…皆以**月令为用，不可以年取格**」。本模块据此给出「月令提纲/
  藏干/透出/十神」等可查证事实与格局候选，不判格之成败、不生成吉凶断语。
- 《三命通會·論太歲》：「太岁如君也，大运如臣也」「真太岁」「岁运并临」
  「日年相并」「征太岁」。本模块只列这些组合事实，不取吉凶结论。
- 《皇極經世》卷一「以元經會」：元/会/运/世 129600/10800/360/30 年换算；
  纪元锚点仍为 pending_expert_review，此处只作宏观时间背景并列，不映射个人事件。

明确边界：
- 不预测未来事件、不推断寿命/六亲/婚育等现实结论、不由生平事件反推生辰；
- 生平事件仅接受调用方**已发生**的录入，做时间对齐展示（只读，不参与计算）；
- 所有产物为工程基线（status=draft），署名字段置空。
"""
from typing import Any, Dict, List, Optional

from lunar_python import Solar

from app.common.classics import get_library
from app.common.ganzhi import (
    BRANCH_CLASH, BRANCH_COMBINE, BRANCH_ELEMENTS, BRANCH_TRIPLE,
    HAI_PAIRS, STEM_COMBINE, STEM_ELEMENTS, XING_PAIRS, triple_group_of,
)
from app.core.yuanhui import cycle_position

from .engine import calculate_bazi
from .liunian import year_ganzhi
from .rules import HIDDEN_STEMS_MAP, NAYIN_TABLE, get_ten_god

RULE_ID = "BZ-LIFELINE-001"
SCHOOL = "ziping-yueling-engineering-baseline-v1"
RULE_VERSION = "bazi-ziping-core-v2.0"
EVIDENCE_QUERIES = ("月令", "提纲", "太歲", "大運", "元會運世")

# 《淵海子平·宝法第二》六格法：「逢官看财、逢财看杀、逢杀看印、逢印看官」
SIX_GE_LOOK_FOR = {
    "正官": "财", "七杀": "印", "正财": "官", "偏财": "官",
    "正印": "官", "偏印": "官", "食神": "财", "伤官": "印",
    "比肩": "财官", "劫财": "财官",
}

# 立春精确交接：以该年节气表「立春」Solar 对象取 Asia/Shanghai 参考时刻
def lichun_datetime(year: int) -> str:
    """返回该年立春交接时刻（Asia/Shanghai 参考时，秒精度）。"""
    if not 1900 <= year <= 2100:
        raise ValueError("year must be between 1900 and 2100")
    lunar = Solar.fromYmdHms(year, 3, 1, 12, 0, 0).getLunar()
    solar = lunar.getJieQiTable().get("立春")
    if solar is None:
        raise ValueError("立春 not found for year {}".format(year))
    return solar.toYmdHms()


def _yueling_facts(pillars: Dict[str, Any], day_stem: str) -> Dict[str, Any]:
    """《淵海子平》「先看提纲为重，皆以月令为用」：月令藏干、透出、十神事实。"""
    month = pillars.get("month", {})
    month_branch = month.get("branch", "")
    hidden = HIDDEN_STEMS_MAP.get(month_branch, ())
    stems = {
        label: pillars.get(key, {}).get("stem", "")
        for key, label in (("year", "年干"), ("month", "月干"), ("day", "日干"), ("hour", "时干"))
    }
    hidden_rows = []
    for stem, weight, kind in hidden:
        god = get_ten_god(day_stem, stem)
        exposed_at = [label for label, value in stems.items() if value == stem]
        hidden_rows.append({
            "stem": stem, "element": STEM_ELEMENTS[stem], "ten_god": god,
            "weight": weight, "qi": kind, "exposed_at": exposed_at,
            "exposed": bool(exposed_at),
        })
    # 本气透出者优先为格局候选（《子平真詮》月令取格通行读法，仅列候选）
    principal = hidden_rows[0] if hidden_rows else None
    candidates = []
    for row in hidden_rows:
        if not row["exposed"]:
            continue
        candidates.append({
            "basis": "月令{}气{}透出{}".format(row["qi"], row["stem"], "、".join(row["exposed_at"])),
            "ten_god": row["ten_god"],
            "pattern_candidate": "{}格候选".format(row["ten_god"]),
            "look_for": SIX_GE_LOOK_FOR.get(row["ten_god"], ""),
            "qi": row["qi"],
        })
    return {
        "rule": "淵海子平·宝法第二：先看提纲为重，皆以月令为用，不可以年取格",
        "month_branch": month_branch,
        "month_element": BRANCH_ELEMENTS.get(month_branch, ""),
        "hidden_stems": hidden_rows,
        "principal_qi": principal,
        "pattern_candidates": candidates,
        "note": "只列月令藏干/透出/十神等可查证事实与格局候选，不判格局成败、清浊、喜忌，不生成吉凶断语。",
    }


def _pair_relations(a_branch: str, b_branch: str) -> List[str]:
    """两支之间的可查证组合（复用 common.ganzhi 单一真源）。"""
    out = []
    pair = frozenset((a_branch, b_branch))
    if BRANCH_CLASH.get(a_branch) == b_branch:
        out.append("六冲")
    if BRANCH_COMBINE.get(a_branch) == b_branch:
        out.append("六合")
    if pair in HAI_PAIRS:
        out.append("六害")
    if a_branch != b_branch and pair in XING_PAIRS:
        out.append("三刑（两支）")
    group = triple_group_of(a_branch)
    if group and b_branch in group and a_branch != b_branch:
        out.append("三合局半合（{}）".format(BRANCH_TRIPLE.get(group, "")))
    return out


def _suiyun_facts(ganzhi: str, luck: Optional[Dict[str, Any]],
                   natal_pillars: Dict[str, Any], day_stem: str) -> Dict[str, Any]:
    """《三命通會·論太歲》岁运组合事实：真太岁/岁运并临/日年相并/征太岁/君臣关系。"""
    ln_stem, ln_branch = ganzhi[0], ganzhi[1]
    year_gz = natal_pillars.get("year", {}).get("ganzhi", "")
    day_gz = natal_pillars.get("day", {}).get("ganzhi", "")
    luck_gz = (luck or {}).get("ganzhi", "")
    facts: Dict[str, Any] = {
        "true_taisui": ganzhi == year_gz,          # 真太岁：流年干支重逢生年
        "suiyun_binglin": bool(luck_gz) and ganzhi == luck_gz,  # 岁运并临
        "day_year_parallel": ganzhi == day_gz,      # 日年相并
        "zheng_taisui": False,                     # 征太岁：日/运干支冲克太岁
        "relations": {},
        "note": "只列《三命通會·論太歲》可查证的组合事实（真太岁/岁运并临/日年相并/征太岁/"
                "太岁与大运及四柱的冲合刑害），不取「吉/凶」结论。",
    }
    day_branch = day_gz[1] if len(day_gz) == 2 else ""
    luck_branch = luck_gz[1] if len(luck_gz) == 2 else ""
    if day_branch and BRANCH_CLASH.get(day_branch) == ln_branch:
        facts["zheng_taisui"] = True
    if luck_branch and BRANCH_CLASH.get(luck_branch) == ln_branch:
        facts["zheng_taisui"] = True
    if luck_gz:
        facts["relations"]["with_luck_pillar"] = {
            "ganzhi": luck_gz,
            "branch_relations": _pair_relations(ln_branch, luck_branch),
            "stem_combine": STEM_COMBINE.get(ln_stem, (None, None))[0] == luck_gz[0],
        }
    for key, label in (("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "时柱")):
        pb = natal_pillars.get(key, {}).get("branch", "")
        if pb:
            rel = _pair_relations(ln_branch, pb)
            if rel:
                facts["relations"].setdefault("with_natal_pillars", {})[label] = rel
    return facts


def _yuanhui_facts(year: int) -> Dict[str, Any]:
    """皇极经世宏观周期背景（纪元锚点仍待专家审核，不映射个人事件）。"""
    pos = cycle_position(year)
    return {
        "status": "engineering_cycle_context_pending_expert_review",
        "epoch_status": pos["epoch"]["status"],
        "yuan": pos["yuan"]["label"], "hui": pos["hui"]["label"],
        "hui_branch": pos["hui"]["branch"], "hui_element": pos["hui"]["element"],
        "yun": pos["yun"]["label"], "shi": pos["shi"]["label"],
        "year_in_shi": pos["shi"]["year_in_shi"],
        "note": "《皇極經世》元会运世宏观时间背景；纪元锚点待专家审核，只计算到公历年粒度，"
                "不表示个人吉凶、事件概率或应期。",
    }


def analyze_lifeline(local_datetime: str, timezone: str = "Asia/Shanghai",
                     gender: str = "男", longitude: Optional[float] = None,
                     use_true_solar_time: bool = False,
                     start_year: Optional[int] = None, count: int = 12,
                     events: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """生成个人生平时间轴：子平命盘事实 + 岁运序列 + 皇极经世背景 + 已发生事件对齐。

    `events` 只接受调用方录入的已发生事件（需含 year 字段），仅做时间对齐展示，
    不参与任何计算、不用于反推生辰、不生成未来事件预测。
    """
    if not 1 <= count <= 60:
        raise ValueError("count must be between 1 and 60")
    natal = calculate_bazi(local_datetime, timezone=timezone, gender=gender,
                           longitude=longitude, use_true_solar_time=use_true_solar_time)
    facts = natal["facts"]
    pillars = facts["pillars"]
    day_stem = natal["day_master"]
    luck_pillars = facts["luck_pillars"]
    birth_year = int(str(natal["solar_datetime"])[:4])
    if start_year is None:
        start_year = facts["luck_start_info"]["start_year"]
    if not 1900 <= start_year <= 2100 or start_year + count - 1 > 2100:
        raise ValueError("start_year/count out of supported range (1900-2100)")

    events = events or []
    events_by_year: Dict[int, List[Dict[str, Any]]] = {}
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get("year"), int):
            raise ValueError("each event must be an object with an integer 'year'")
        if not 1900 <= event["year"] <= 2100:
            raise ValueError("event year out of range (1900-2100)")
        events_by_year.setdefault(event["year"], []).append(event)

    yueling = _yueling_facts(pillars, day_stem)
    timeline = []
    for step in range(count):
        year = start_year + step
        ganzhi = year_ganzhi(year)
        ln_stem, ln_branch = ganzhi[0], ganzhi[1]
        luck = next((p for p in luck_pillars
                     if p["start_year"] <= year <= p["end_year"]), None)
        luck_view = None
        if luck:
            luck_view = {"index": luck["index"], "ganzhi": luck["ganzhi"],
                         "stem_ten_god": luck["stem_ten_god"],
                         "start_year": luck["start_year"], "end_year": luck["end_year"],
                         "age_range": "{}~{}岁".format(luck["start_age"], luck["end_age"])}
        timeline.append({
            "year": year,
            "ganzhi": ganzhi,
            "stem": ln_stem, "branch": ln_branch,
            "stem_ten_god": get_ten_god(day_stem, ln_stem),
            "nayin": NAYIN_TABLE.get(ganzhi, ""),
            "age": year - birth_year, "virtual_age": year - birth_year + 1,
            "lichun_datetime": lichun_datetime(year),
            "year_boundary": "立春",
            "luck_pillar": luck_view,
            "taisui_branch": ln_branch,
            "suipo_branch": BRANCH_CLASH[ln_branch],
            "suiyun": _suiyun_facts(ganzhi, luck_view, pillars, day_stem),
            "yuan_hui_yun_shi": _yuanhui_facts(year),
            "recorded_events": events_by_year.get(year, []),
        })

    library = get_library()
    evidence = library.evidence(EVIDENCE_QUERIES, category="mingli", per_query=1, limit=6)
    return {
        "schema_version": "1.0",
        "rule_id": RULE_ID,
        "system": "bazi-lifeline",
        "school": SCHOOL,
        "rule_version": RULE_VERSION,
        "status": "engineering_baseline_draft",
        "input": natal["input"],
        "day_master": day_stem,
        "birth_year": birth_year,
        "start_year": start_year,
        "count": count,
        "ziping": yueling,
        "natal_summary": {
            "pillars": {k: v.get("ganzhi") for k, v in pillars.items()},
            "day_master_strength": facts["day_master_strength"]["level"],
            "luck_start_info": facts["luck_start_info"],
        },
        "timeline": timeline,
        "evidence": evidence,
        "judgements": [],
        "warnings": [
            "子平月令取格仅列藏干/透出/十神与格局候选，格局成败、喜忌、清浊待专家签署，不生成吉凶断语。",
            "岁运组合只列《三命通會·論太歲》可查证事实，不取吉凶结论。",
            "皇极经世纪元锚点待专家审核，只计算到公历年粒度，不表示个人吉凶或应期。",
            "生平事件仅对调用方录入的既成事实做时间对齐，不预测未来事件、不由事件反推生辰。",
            "流年干支按公历通行纪年；立春精确交接时刻并列给出，节令界口径请结合 calendar 模块。",
        ],
    }


def lifeline_cast(local_datetime: str, start_year: Optional[int] = None, count: int = 12,
                  timezone: str = "Asia/Shanghai", gender: str = "男",
                  longitude: Optional[float] = None, use_true_solar_time: bool = False,
                  events: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """供 API 分派使用的薄封装。"""
    return analyze_lifeline(
        local_datetime, timezone=timezone, gender=gender, longitude=longitude,
        use_true_solar_time=use_true_solar_time, start_year=start_year,
        count=count, events=events,
    )


__all__ = ("analyze_lifeline", "lifeline_cast", "lichun_datetime", "RULE_ID", "SCHOOL")
