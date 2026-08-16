from lunar_python import Solar

from app.calendar import calendar_analysis
from app.common.casting import derive_integer, nonce_hash
from app.common.five_elements import FIVE_ELEMENTS_CONTROLS
from app.common.ganzhi import (
    BRANCH_ELEMENTS, EARTHLY_BRANCHES, STEM_ELEMENTS, polarity, xun_info,
)

from .models import OccupationNumberInput, PlateInput
from .rules import (
    HEAVENLY_GENERALS, MONTH_GENERALS, NOBLE_BRANCHES, STEM_LODGES,
    TRANSMISSION_COVERAGE,
)


ENGINE_VERSION = "daliuren-engine-2.0.0+lunar-python-1.4.8"
RULE_VERSION = "daliuren-engineering-baseline-2.0.0"


def _month_general(calendar):
    solar = calendar["solar"]
    lunar = Solar.fromYmdHms(
        solar["year"], solar["month"], solar["day"], solar["hour"], solar["minute"], solar["second"]
    ).getLunar()
    qi = lunar.getCurrentQi() or lunar.getPrevQi()
    name = qi.getName()
    branch, title = MONTH_GENERALS[name]
    return {
        "branch": branch, "name": title, "boundary_term": name,
        "boundary_datetime": qi.getSolar().toYmdHms(),
    }


def _heaven_plate(month_general_branch, occupation_branch):
    general_index = EARTHLY_BRANCHES.index(month_general_branch)
    hour_index = EARTHLY_BRANCHES.index(occupation_branch)
    branches = tuple(
        EARTHLY_BRANCHES[(general_index + index - hour_index) % 12]
        for index in range(12)
    )
    PlateInput(branches)
    return dict(zip(EARTHLY_BRANCHES, branches))


def _lesson(sequence, lower, upper):
    lower_element = STEM_ELEMENTS.get(lower, BRANCH_ELEMENTS.get(lower))
    upper_element = BRANCH_ELEMENTS[upper]
    relation = "none"
    if FIVE_ELEMENTS_CONTROLS[lower_element] == upper_element:
        relation = "lower_controls_upper"
    elif FIVE_ELEMENTS_CONTROLS[upper_element] == lower_element:
        relation = "upper_controls_lower"
    return {
        "sequence": sequence, "lower": lower, "upper": upper,
        "lower_element": lower_element, "upper_element": upper_element,
        "lower_polarity": polarity(lower), "upper_polarity": polarity(upper),
        "relation": relation,
    }


def _four_lessons(day_pillar, plate):
    stem, branch = day_pillar
    first_upper = plate[STEM_LODGES[stem]]
    third_upper = plate[branch]
    return [
        _lesson(1, stem, first_upper),
        _lesson(2, first_upper, plate[first_upper]),
        _lesson(3, branch, third_upper),
        _lesson(4, third_upper, plate[third_upper]),
    ]


def _unique_candidates(lessons, relation):
    result = []
    for lesson in lessons:
        if lesson["relation"] == relation and lesson["upper"] not in result:
            result.append(lesson["upper"])
    return result


def _unique_lesson_count(lessons):
    canonical = []
    for lesson in lessons:
        lower = STEM_LODGES.get(lesson["lower"], lesson["lower"])
        canonical.append((lower, lesson["upper"]))
    return len(set(canonical))


def _select_by_day_polarity(candidates, day_stem):
    matching = [branch for branch in candidates if polarity(branch) == polarity(day_stem)]
    return matching[0] if len(matching) == 1 else None


def _completed_transmissions(initial, plate, lesson_type, source_path, candidates, trace):
    middle = plate[initial]
    final = plate[middle]
    return {
        "status": "completed", "lesson_type": lesson_type, "source_path": source_path,
        "candidates": candidates, "transmissions": [initial, middle, final], "trace": trace + [
            "初传{}上神为{}，取中传".format(initial, middle),
            "中传{}上神为{}，取末传".format(middle, final),
        ],
    }


def _unsupported(path, candidates, trace, reason):
    return {
        "status": "pending_rule_selection", "lesson_type": path, "source_path": path,
        "candidates": candidates, "pending_path": path, "transmissions": [],
        "reason": reason, "trace": trace,
    }


def _direct_transmissions(day_pillar, plate, lessons):
    candidates = _unique_candidates(lessons, "lower_controls_upper")
    source_path = "贼克" if candidates else None
    if not candidates:
        candidates = _unique_candidates(lessons, "upper_controls_lower")
        source_path = "克" if candidates else None
    if not candidates:
        return None
    trace = ["检查四课上下克，{}候选为{}".format(source_path, candidates)]
    if len(candidates) == 1:
        return _completed_transmissions(candidates[0], plate, source_path, source_path, candidates, trace)
    selected = _select_by_day_polarity(candidates, day_pillar[0])
    if selected is not None:
        trace.append("多课有克，取与日干阴阳相同的{}为比用".format(selected))
        return _completed_transmissions(selected, plate, "比用", source_path, candidates, trace)
    return _unsupported(
        "涉害", candidates, trace + ["比用后仍有多个候选，进入涉害"],
        "涉害深浅、孟仲季及复等规则尚未完成标准案例签署",
    )


def _remote_transmissions(day_pillar, plate, lessons):
    day_stem = day_pillar[0]
    day_element = STEM_ELEMENTS[day_stem]
    uppers = []
    for lesson in lessons:
        if lesson["upper"] not in uppers:
            uppers.append(lesson["upper"])
    candidates = [branch for branch in uppers if FIVE_ELEMENTS_CONTROLS[BRANCH_ELEMENTS[branch]] == day_element]
    source_path = "蒿矢"
    if not candidates:
        candidates = [branch for branch in uppers if FIVE_ELEMENTS_CONTROLS[day_element] == BRANCH_ELEMENTS[branch]]
        source_path = "弹射"
    if not candidates:
        return None
    trace = ["四课无上下克，检查遥克{}候选为{}".format(source_path, candidates)]
    selected = candidates[0] if len(candidates) == 1 else _select_by_day_polarity(candidates, day_stem)
    if selected is None:
        return _unsupported(
            "遥克", candidates, trace + ["遥克比用后仍有多个候选"],
            "多个遥克候选的后续取法尚未完成标准案例签署",
        )
    if len(candidates) > 1:
        trace.append("多个遥克候选中取与日干阴阳相同的{}".format(selected))
    return _completed_transmissions(selected, plate, "遥克", source_path, candidates, trace)


def _star_transmissions(day_pillar, plate, lessons):
    day_stem = day_pillar[0]
    day_upper = lessons[0]["upper"]
    branch_upper = lessons[2]["upper"]
    if polarity(day_stem) == "阳":
        initial = plate["酉"]
        transmissions = [initial, branch_upper, day_upper]
        trace = ["四课无克且无遥克，阳日仰视酉上神{}为初传".format(initial),
                 "阳日先取辰上神{}为中传，再取日上神{}为末传".format(branch_upper, day_upper)]
        source_path = "阳日仰视"
    else:
        initial = next(ground for ground, heaven in plate.items() if heaven == "酉")
        transmissions = [initial, day_upper, branch_upper]
        trace = ["四课无克且无遥克，阴日俯视天盘酉所临地盘{}为初传".format(initial),
                 "阴日先取日上神{}为中传，再取辰上神{}为末传".format(day_upper, branch_upper)]
        source_path = "阴日俯视"
    return {
        "status": "completed", "lesson_type": "昴星", "source_path": source_path,
        "candidates": [initial], "transmissions": transmissions, "trace": trace,
    }


def _plate_offset(plate):
    return (EARTHLY_BRANCHES.index(plate["子"]) - EARTHLY_BRANCHES.index("子")) % 12


def _three_transmissions(day_pillar, plate, lessons):
    direct = _direct_transmissions(day_pillar, plate, lessons)
    if direct is not None:
        return direct

    offset = _plate_offset(plate)
    lesson_count = _unique_lesson_count(lessons)
    if offset == 0:
        return _unsupported("伏吟", [], ["天地盘同位且四课无上下克，进入伏吟"], "伏吟刑、冲递传规则待标准案例签署")
    if offset == 6:
        return _unsupported("返吟", [], ["天地盘相冲且四课无上下克，进入返吟井栏"], "返吟井栏规则待六日标准案例签署")
    if lesson_count == 2:
        return _unsupported("八专", [], ["四课去重后仅二课且无上下克，进入八专"], "八专顺逆三位规则待标准案例签署")

    remote = _remote_transmissions(day_pillar, plate, lessons)
    if remote is not None:
        return remote
    if lesson_count == 3:
        return _unsupported("别责", [], ["四课去重后三课且无克无遥，进入别责"], "别责刚日干合、柔日支前三合规则待标准案例签署")
    return _star_transmissions(day_pillar, plate, lessons)


def _heavenly_generals(day_stem, plate, hour, day_period):
    noble_branch = NOBLE_BRANCHES[day_stem][0 if day_period == "day" else 1]
    noble_ground = next(ground for ground, heaven in plate.items() if heaven == noble_branch)
    start = EARTHLY_BRANCHES.index(noble_ground)
    direction = 1 if noble_ground in ("亥", "子", "丑", "寅", "卯", "辰") else -1
    by_ground = {}
    for offset, general in enumerate(HEAVENLY_GENERALS):
        by_ground[EARTHLY_BRANCHES[(start + direction * offset) % 12]] = general
    return {
        "period": day_period, "civil_hour": hour, "noble_branch": noble_branch,
        "noble_ground": noble_ground, "distribution_direction": "顺布" if direction == 1 else "逆布",
        "by_ground": by_ground,
    }


def _coverage_report():
    return [dict(item) for item in TRANSMISSION_COVERAGE]


def _cast(local_datetime, timezone, occupation_branch=None, occupation_number=None,
          longitude=None, use_true_solar_time=False):
    calendar = calendar_analysis(local_datetime, timezone, longitude, use_true_solar_time)
    actual_branch = calendar["time_branch"]["name"]
    selected_branch = occupation_branch or actual_branch
    month_general = _month_general(calendar)
    plate = _heaven_plate(month_general["branch"], selected_branch)
    day_pillar = calendar["pillars"]["day"]
    lessons = _four_lessons(day_pillar, plate)
    transmissions = _three_transmissions(day_pillar, plate, lessons)
    xun = xun_info(day_pillar)
    hour = calendar["solar"]["hour"]
    generals = _heavenly_generals(day_pillar[0], plate, hour, "day" if 6 <= hour < 18 else "night")
    method = "number_hour" if occupation_number is not None else "time"
    input_facts = {
        "local_datetime": local_datetime, "timezone": timezone, "longitude": longitude,
        "use_true_solar_time": use_true_solar_time, "occupation_number": occupation_number,
    }
    trace = [
        "历法确定日柱{}、实际时支{}".format(day_pillar, actual_branch),
        "中气{}起月将{}{}".format(month_general["boundary_term"], month_general["name"], month_general["branch"]),
        "月将{}加临占时{}，顺布十二天盘".format(month_general["branch"], selected_branch),
        "按日干寄宫和日支生成四课：{}".format(
            ["{}上{}".format(lesson["lower"], lesson["upper"]) for lesson in lessons]
        ),
    ] + transmissions["trace"] + [
        "按{}日贵人起十二天将并{}".format(generals["period"], generals["distribution_direction"]),
        "日柱{}属于{}，旬空{}".format(day_pillar, xun["name"], "、".join(xun["empty_branches"])),
    ]
    warnings = ["大六壬月将、天地盘、四课和天将采用工程基线，尚待专家与标准案例签署。"]
    if transmissions["status"] != "completed":
        warnings.append("本课进入{}路径；规则和标准案例未签署，系统未生成三传猜测值。".format(transmissions["pending_path"]))
    return {
        "schema_version": "2.0", "system": "liuren", "school": "daliuren-engineering-baseline",
        "engine_version": ENGINE_VERSION, "algorithm_version": ENGINE_VERSION, "rule_version": RULE_VERSION,
        "input": input_facts,
        "normalized_input": {
            "effective_local_datetime": calendar["normalized_input"]["effective_local_datetime"],
            "day_pillar": day_pillar, "actual_time_branch": actual_branch,
            "occupation_branch": selected_branch,
        },
        "facts": {
            "method": method, "calendar": {"pillars": calendar["pillars"], "solar_terms": calendar["solar_terms"]},
            "day_pillar": day_pillar, "actual_time_branch": actual_branch,
            "occupation_time": {"branch": selected_branch, "number": EARTHLY_BRANCHES.index(selected_branch) + 1,
                                "input_number": occupation_number},
            "month_general": month_general, "earth_plate": list(EARTHLY_BRANCHES), "heaven_plate": plate,
            "four_lessons": lessons, "three_transmissions": transmissions,
            "transmission_coverage": _coverage_report(), "heavenly_generals": generals, "xun": xun,
        },
        "calculation_trace": trace,
        "steps": [
            {"sequence": 1, "operation": "derive_month_general_and_occupation_time",
             "inputs": {"local_datetime": local_datetime, "occupation_number": occupation_number},
             "output": {"month_general": month_general, "occupation_branch": selected_branch},
             "rule_ids": ["LR-MONTH-GENERAL-001", "LR-HOUR-001" if occupation_number is None else "LR-NUMBER-001"]},
            {"sequence": 2, "operation": "derive_heaven_plate_and_four_lessons",
             "inputs": {"month_general": month_general["branch"], "occupation_branch": selected_branch,
                        "day_pillar": day_pillar},
             "output": {"heaven_plate": plate, "four_lessons": lessons},
             "rule_ids": ["LR-PLATE-001", "LR-LESSON-001"]},
            {"sequence": 3, "operation": "derive_three_transmissions",
             "inputs": {"four_lessons": lessons, "day_pillar": day_pillar, "plate_offset": _plate_offset(plate)},
             "output": transmissions,
             "rule_ids": (["LR-REMOTE-001"] if transmissions["lesson_type"] == "遥克" else
                          ["LR-STAR-001"] if transmissions["lesson_type"] == "昴星" else
                          ["LR-COVERAGE-001"] if transmissions["status"] != "completed" else
                          ["LR-TRANSMISSION-001"])},
            {"sequence": 4, "operation": "derive_generals_void_and_coverage",
             "inputs": {"day_pillar": day_pillar, "civil_hour": hour},
             "output": {"heavenly_generals": generals, "xun": xun, "coverage": _coverage_report()},
             "rule_ids": ["LR-GENERAL-001", "CYCLE-XUN-001", "LR-COVERAGE-001"]},
        ],
        "evidence": [], "judgements": [], "warnings": warnings,
    }


def time_cast(local_datetime, timezone, longitude=None, use_true_solar_time=False):
    return _cast(local_datetime, timezone, longitude=longitude, use_true_solar_time=use_true_solar_time)


def number_cast(number, local_datetime, timezone, longitude=None, use_true_solar_time=False):
    source = OccupationNumberInput(number).value
    branch = EARTHLY_BRANCHES[(source - 1) % 12]
    return _cast(local_datetime, timezone, occupation_branch=branch, occupation_number=source,
                 longitude=longitude, use_true_solar_time=use_true_solar_time)


def auto_cast(cast_nonce, local_datetime, timezone, longitude=None, use_true_solar_time=False):
    report_number = derive_integer("liuren-report-number-v1", cast_nonce, 1, 1, 12)
    result = number_cast(report_number, local_datetime, timezone, longitude, use_true_solar_time)
    result["facts"]["method"] = "personalized_report_number"
    result["facts"]["cast_nonce_hash"] = nonce_hash(cast_nonce)
    result["facts"]["report_number"] = report_number
    result["input"]["cast_nonce_hash"] = nonce_hash(cast_nonce)
    result["steps"][0] = {
        "sequence": 1, "operation": "derive_personalized_occupation_number",
        "inputs": {"cast_nonce_hash": nonce_hash(cast_nonce), "domain": "liuren-report-number-v1"},
        "output": {"report_number": report_number, "occupation_branch": result["facts"]["occupation_time"]["branch"]},
        "rule_ids": ["LR-AUTO-REPORT-001", "LR-NUMBER-001"],
    }
    result["calculation_trace"].insert(0, "由六壬专属凭证域派生报数{}".format(report_number))
    result["warnings"].insert(0, "个体自动排盘采用凭证派生报数确定占时；实际时支仍保留在盘面中。")
    return result


__all__ = ("auto_cast", "number_cast", "time_cast")
