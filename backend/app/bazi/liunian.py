"""八字流年（岁运）确定性事实序列。

只计算可查证的干支事实：
- 公历年份 → 干支（以甲子年 4 年为锚的 60 甲子循环）、纳音、十神；
- 流年所属大运区间（来自排盘结果的 luck_pillars）；
- 流年干支与四柱干支之间的六冲/六合/六害/三刑/自刑/半合/天干五合；
- 太岁与岁破地支；年龄（周岁与虚岁分别标注）。

不生成吉凶断语；典籍依据由本地典籍库按关键词检索原文段落挂入 evidence。
"""

from typing import Any, Dict, List, Optional

from app.common.classics import get_library
from app.common.ganzhi import (
    BRANCH_CLASH, BRANCH_COMBINE, BRANCH_TRIPLE, EARTHLY_BRANCHES,
    HAI_PAIRS, HEAVENLY_STEMS, SELF_XING_BRANCHES, STEM_COMBINE,
    STEM_ELEMENTS, XING_PAIRS, triple_group_of,
)

from .engine import calculate_bazi
from .rules import BRANCH_ELEMENTS, NAYIN_TABLE, get_ten_god

RULE_ID = "BZ-LIUNIAN-001"
SCHOOL = "ziping-yueling-engineering-baseline-v1"
RULE_VERSION = "bazi-ziping-core-v2.0"
PILLAR_NAMES = (("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "时柱"))
EVIDENCE_QUERIES = ("流年", "太歲", "大運", "行運")


def year_ganzhi(year: int) -> str:
    """公历年干支：4 年为甲子，60 年一循环。"""
    offset = year - 4
    return HEAVENLY_STEMS[offset % 10] + EARTHLY_BRANCHES[offset % 12]


def _branch_relations(ln_branch: str, pillars: Dict[str, Any]) -> List[Dict[str, str]]:
    relations = []
    for key, label in PILLAR_NAMES:
        pillar = pillars.get(key, {})
        branch = pillar.get("branch", "")
        if not branch:
            continue
        pair = frozenset((ln_branch, branch))
        if BRANCH_CLASH.get(ln_branch) == branch:
            relations.append({"type": "六冲", "with": label, "branches": f"{ln_branch}{branch}"})
        if BRANCH_COMBINE.get(ln_branch) == branch:
            relations.append({"type": "六合", "with": label, "branches": f"{ln_branch}{branch}"})
        if pair in HAI_PAIRS:
            relations.append({"type": "六害", "with": label, "branches": f"{ln_branch}{branch}"})
        if ln_branch != branch and pair in XING_PAIRS:
            relations.append({"type": "三刑（两支）", "with": label, "branches": f"{ln_branch}{branch}"})
        if ln_branch == branch and branch in SELF_XING_BRANCHES:
            relations.append({"type": "自刑（同支并见）", "with": label, "branches": f"{ln_branch}{branch}"})
        group = triple_group_of(ln_branch)
        if group and branch in group and ln_branch != branch:
            element = BRANCH_TRIPLE.get(group, "")
            relations.append({"type": "三合局半合", "with": label,
                              "branches": f"{ln_branch}{branch}", "group": group, "element": element})
    return relations


def _stem_relations(ln_stem: str, pillars: Dict[str, Any]) -> List[Dict[str, str]]:
    relations = []
    combine = STEM_COMBINE.get(ln_stem)
    if not combine:
        return relations
    for key, label in PILLAR_NAMES:
        stem = pillars.get(key, {}).get("stem", "")
        if stem == combine[0]:
            relations.append({"type": "天干五合", "with": label,
                              "stems": f"{ln_stem}{stem}", "combines_to": combine[1]})
    return relations


def _luck_pillar_for_year(year: int, luck_pillars: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    for pillar in luck_pillars:
        if pillar.get("start_year", 0) <= year <= pillar.get("end_year", 0):
            return {"index": pillar.get("index"), "ganzhi": pillar.get("ganzhi"),
                    "stem_ten_god": pillar.get("stem_ten_god"),
                    "start_year": pillar.get("start_year"), "end_year": pillar.get("end_year")}
    return None


def calculate_liunian(natal: Dict[str, Any], start_year: Optional[int] = None,
                      count: int = 10) -> Dict[str, Any]:
    """基于排盘结果生成逐年流年事实序列。"""
    if not 1 <= count <= 60:
        raise ValueError("count must be between 1 and 60")
    facts = natal.get("facts", {})
    pillars = facts.get("pillars", {})
    day_stem = natal.get("day_master") or facts.get("day_master", "")
    luck_pillars = natal.get("luck_pillars") or facts.get("luck_pillars", [])
    solar_datetime = str(natal.get("solar_datetime", ""))
    try:
        birth_year = int(solar_datetime[:4])
    except (ValueError, TypeError) as exc:
        raise ValueError("natal result missing valid solar_datetime: {!r}".format(solar_datetime)) from exc
    if start_year is None:
        start_year = natal.get("luck_start_info", {}).get("start_year") or birth_year
    if not 1900 <= start_year <= 2100:
        raise ValueError("start_year must be between 1900 and 2100")
    if start_year + count - 1 > 2100:
        raise ValueError("start_year + count - 1 must not exceed 2100")

    years = []
    for step in range(count):
        year = start_year + step
        ganzhi = year_ganzhi(year)
        ln_stem, ln_branch = ganzhi[0], ganzhi[1]
        years.append({
            "year": year,
            "ganzhi": ganzhi,
            "stem": ln_stem,
            "branch": ln_branch,
            "stem_element": STEM_ELEMENTS[ln_stem],
            "stem_ten_god": get_ten_god(day_stem, ln_stem),
            "branch_element": BRANCH_ELEMENTS[ln_branch],
            "nayin": NAYIN_TABLE.get(ganzhi, ""),
            "age": year - birth_year if birth_year else None,
            "virtual_age": year - birth_year + 1 if birth_year else None,
            "luck_pillar": _luck_pillar_for_year(year, luck_pillars),
            "taisui_branch": ln_branch,
            "suipo_branch": BRANCH_CLASH[ln_branch],
            "branch_relations": _branch_relations(ln_branch, pillars),
            "stem_relations": _stem_relations(ln_stem, pillars),
        })

    library = get_library()
    evidence = library.evidence(EVIDENCE_QUERIES, category="mingli", per_query=1, limit=4)
    return {
        "schema_version": "1.0",
        "rule_id": RULE_ID,
        "system": "bazi-liunian",
        "school": SCHOOL,
        "rule_version": RULE_VERSION,
        "status": "engineering_baseline_draft",
        "day_master": day_stem,
        "birth_year": birth_year,
        "start_year": start_year,
        "count": count,
        "years": years,
        "evidence": evidence,
        "judgements": [],
        "warnings": [
            "只列干支、十神、纳音与大运区间等可查证事实，不判断吉凶、不生成断语。",
            "流年干支按公历通行纪年；立春精确交接时刻见 /v1/bazi/lifeline 的 lichun_datetime。",
            "格局成败、喜忌与岁运应期待专家签署，产物仍为工程基线。",
        ],
        "notes": [
            "干支纪年以公历 4 年甲子为锚的 60 甲子循环；流年以立春交节为界，本接口按公历年给出通行纪年干支，节令精确交接请结合 calendar 模块。",
            "branch_relations/stem_relations 只列可查证的组合事实（六冲/六合/六害/三刑/自刑/半合/天干五合），不含吉凶断语。",
            "age 为周岁差（year - 出生年），virtual_age 为传统虚岁；两者口径并列，避免混用。",
            "luck_pillar 为排盘结果中覆盖该年的大运区间，未覆盖（起运前/八步之后）为 null。",
        ],
    }


def liunian_cast(local_datetime: str, start_year: Optional[int] = None, count: int = 10,
                 timezone: str = "Asia/Shanghai", gender: str = "男",
                 longitude: Optional[float] = None, use_true_solar_time: bool = False) -> Dict[str, Any]:
    """排盘 + 流年序列一次性返回（供 API 使用）。"""
    natal = calculate_bazi(local_datetime, timezone=timezone, gender=gender,
                           longitude=longitude, use_true_solar_time=use_true_solar_time)
    result = calculate_liunian(natal, start_year=start_year, count=count)
    result["natal_summary"] = {
        "day_master": natal.get("day_master"),
        "luck_start_info": natal.get("luck_start_info"),
        "luck_pillars": natal.get("luck_pillars"),
    }
    return result
