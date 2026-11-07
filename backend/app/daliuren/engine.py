from datetime import datetime

from lunar_python import Solar

from app.calendar import calendar_analysis
from app.common.casting import derive_integer, nonce_hash
from app.common.five_elements import FIVE_ELEMENTS_CONTROLS
from app.common.ganzhi import (
    BRANCH_ELEMENTS, EARTHLY_BRANCHES, STEM_ELEMENTS, polarity, xun_info,
)

from .models import OccupationNumberInput, PlateInput
from .rules import (
    BRANCH_CLASHES, BRANCH_PUNISHMENTS, HEAVENLY_GENERALS, JI_BRANCHES,
    LODGED_STEMS_BY_BRANCH, MENG_BRANCHES, MONTH_GENERALS, NOBLE_BRANCHES,
    STEM_COMBINATIONS, STEM_LODGES, TRANSMISSION_COVERAGE, ZHONG_BRANCHES,
)


ENGINE_VERSION = "daliuren-engine-2.0.0+lunar-python-1.4.8"
RULE_VERSION = "daliuren-engineering-baseline-2.0.0"


def _month_general(calendar):
    """月将按中气换将（《六壬指南》：正月雨水后日躔娵訾之次入亥宫，乃登明将）。

    中气边界须与四柱/节气同源：CalendarEngine 用 effective 时刻换算到
    Asia/Shanghai 参考时求节气；此处改用同一个 solar_term_reference_datetime，
    避免非东八区或真太阳时修正下 effective local 与参考时跨中气导致错将。
    """
    ref = calendar["normalized_input"]["solar_term_reference_datetime"]
    d = datetime.fromisoformat(ref)
    lunar = Solar.fromYmdHms(
        d.year, d.month, d.day, d.hour, d.minute, d.second
    ).getLunar()
    # getCurrentQi 仅在中气当日返回；其余日取最近已过中气（雨水后仍用雨水将）。
    qi = lunar.getCurrentQi() or lunar.getPrevQi()
    if qi is None or qi.getName() not in MONTH_GENERALS:
        raise ValueError("cannot determine 中气 for month general from {}".format(ref))
    name = qi.getName()
    branch, title = MONTH_GENERALS[name]
    return {
        "branch": branch, "name": title, "boundary_term": name,
        "boundary_datetime": qi.getSolar().toYmdHms(),
        "reference_datetime": ref,
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


def _candidate_lessons(lessons, relation):
    result = []
    seen = set()
    for lesson in lessons:
        if lesson["relation"] == relation and lesson["upper"] not in seen:
            seen.add(lesson["upper"])
            result.append(lesson)
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


def _path_between(start, destination):
    start_index = EARTHLY_BRANCHES.index(start)
    distance_to_destination = (EARTHLY_BRANCHES.index(destination) - start_index) % 12 or 12
    return [
        EARTHLY_BRANCHES[(start_index + distance) % 12]
        for distance in range(1, distance_to_destination)
    ]


def _shehai_depth(lesson):
    lower_ground = STEM_LODGES.get(lesson["lower"], lesson["lower"])
    upper = lesson["upper"]
    upper_element = BRANCH_ELEMENTS[upper]
    encounters = []
    for ground in _path_between(lower_ground, upper):
        local_symbols = (ground,) + LODGED_STEMS_BY_BRANCH[ground]
        for symbol in local_symbols:
            local_element = STEM_ELEMENTS.get(symbol, BRANCH_ELEMENTS.get(symbol))
            is_harm = (
                FIVE_ELEMENTS_CONTROLS[local_element] == upper_element
                if lesson["relation"] == "lower_controls_upper"
                else FIVE_ELEMENTS_CONTROLS[upper_element] == local_element
            )
            if is_harm:
                encounters.append({"ground": ground, "symbol": symbol, "element": local_element})
    return {
        "upper": upper, "lesson_sequence": lesson["sequence"], "lower_ground": lower_ground,
        "depth": len(encounters), "encounters": encounters,
    }


def _season_rank(branch):
    if branch in MENG_BRANCHES:
        return 0
    if branch in ZHONG_BRANCHES:
        return 1
    if branch in JI_BRANCHES:
        return 2
    raise ValueError("unknown branch season position")


def _shehai_transmissions(day_pillar, plate, candidate_lessons, source_path):
    depths = [_shehai_depth(lesson) for lesson in candidate_lessons]
    deepest = max(item["depth"] for item in depths)
    finalists = [item for item in depths if item["depth"] == deepest]
    trace = [
        "{}比用仍有多候选，逐一归本家计算涉害深度：{}".format(
            source_path, {item["upper"]: item["depth"] for item in depths}
        )
    ]
    subtype = "涉害"
    if len(finalists) > 1:
        best_rank = min(_season_rank(item["lower_ground"]) for item in finalists)
        finalists = [item for item in finalists if _season_rank(item["lower_ground"]) == best_rank]
        subtype = "见机" if best_rank == 0 else "察微"
        trace.append("深度相同，按孟仲季取当前地盘层级{}".format(finalists[0]["lower_ground"]))
    if len(finalists) > 1:
        preferred = (1, 2) if polarity(day_pillar[0]) == "阳" else (3, 4)
        preferred_finalists = [item for item in finalists if item["lesson_sequence"] in preferred]
        if preferred_finalists:
            finalists = preferred_finalists
        subtype = "缀瑕"
        trace.append("深度和孟仲季复等，{}日取{}课先见".format(
            "刚" if polarity(day_pillar[0]) == "阳" else "柔", "日" if preferred == (1, 2) else "辰"
        ))
    selected = min(finalists, key=lambda item: item["lesson_sequence"])
    trace.append("取{}课上神{}为初传，涉害{}重".format(
        selected["lesson_sequence"], selected["upper"], selected["depth"]
    ))
    result = _completed_transmissions(
        selected["upper"], plate, "涉害", subtype,
        [item["upper"] for item in depths], trace,
    )
    result["candidate_depths"] = depths
    return result


def _direct_transmissions(day_pillar, plate, lessons):
    candidates = _candidate_lessons(lessons, "lower_controls_upper")
    source_path = "贼克" if candidates else None
    if not candidates:
        candidates = _candidate_lessons(lessons, "upper_controls_lower")
        source_path = "克" if candidates else None
    if not candidates:
        return None
    candidate_branches = [lesson["upper"] for lesson in candidates]
    trace = ["检查四课上下克，{}候选为{}".format(source_path, candidate_branches)]
    if len(candidates) == 1:
        return _completed_transmissions(candidate_branches[0], plate, source_path, source_path, candidate_branches, trace)
    selected = _select_by_day_polarity(candidate_branches, day_pillar[0])
    if selected is not None:
        trace.append("多课有克，取与日干阴阳相同的{}为比用".format(selected))
        return _completed_transmissions(selected, plate, "比用", source_path, candidate_branches, trace)
    return _shehai_transmissions(day_pillar, plate, candidates, source_path)


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
        # 遥克比用后仍有多个候选：转入涉害，按涉害深度（见机/察微/缀瑕）取初传，
        # 取法在同一涉害规则内，保持可复核；绝不退回 pending，保证三传必然可计算。
        lesson_candidates = []
        seen = set()
        for lesson in lessons:
            if lesson["upper"] in candidates and lesson["upper"] not in seen:
                seen.add(lesson["upper"])
                lesson_candidates.append(lesson)
        result = _shehai_transmissions(day_pillar, plate, lesson_candidates, "遥克")
        result["remote_control"] = {
            "path": "遥克", "source_path": source_path, "candidates": candidates,
        }
        result["trace"].insert(0, "遥克{}比用不定，转涉害取深".format(source_path))
        return result
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


def _branch_shift(branch, distance):
    return EARTHLY_BRANCHES[(EARTHLY_BRANCHES.index(branch) + distance) % 12]


def _bieze_transmissions(day_pillar, plate, lessons):
    stem, branch = day_pillar
    day_upper = lessons[0]["upper"]
    if polarity(stem) == "阳":
        combined_stem = STEM_COMBINATIONS[stem]
        combined_lodge = STEM_LODGES[combined_stem]
        initial = plate[combined_lodge]
        source_path = "刚日干合"
        trace = ["三课无克无遥，刚日{}与{}合，取寄宫{}上神{}为初传".format(
            stem, combined_stem, combined_lodge, initial
        )]
    else:
        initial = _branch_shift(branch, 4)
        source_path = "柔日支前三合"
        trace = ["三课无克无遥，柔日支{}取前三合{}为初传".format(branch, initial)]
    trace.append("别责中末传均取日上神{}".format(day_upper))
    return {
        "status": "completed", "lesson_type": "别责", "source_path": source_path,
        "candidates": [initial], "transmissions": [initial, day_upper, day_upper], "trace": trace,
    }


def _bazhuan_transmissions(day_pillar, lessons):
    day_upper = lessons[0]["upper"]
    if polarity(day_pillar[0]) == "阳":
        source = day_upper
        initial = _branch_shift(source, 2)
        source_path = "阳日顺数三位"
    else:
        source = lessons[3]["upper"]
        initial = _branch_shift(source, -2)
        source_path = "阴日逆数三位"
    return {
        "status": "completed", "lesson_type": "八专", "source_path": source_path,
        "candidates": [initial], "transmissions": [initial, day_upper, day_upper],
        "trace": ["八专无克，{}从{}连本位数至{}为初传".format(source_path, source, initial),
                  "八专中末传均取日上神{}".format(day_upper)],
    }


def _fuyin_transmissions(day_pillar, plate, lessons):
    stem, branch = day_pillar
    candidates = _candidate_lessons(lessons, "lower_controls_upper")
    source_path = "伏吟有克"
    if not candidates:
        candidates = _candidate_lessons(lessons, "upper_controls_lower")
    if candidates:
        candidate_branches = [lesson["upper"] for lesson in candidates]
        initial = candidate_branches[0] if len(candidates) == 1 else _select_by_day_polarity(candidate_branches, stem)
        if initial is None:
            selected = _shehai_transmissions(day_pillar, plate, candidates, "伏吟有克")
            initial = selected["transmissions"][0]
        origin = "day" if next(lesson for lesson in candidates if lesson["upper"] == initial)["sequence"] <= 2 else "branch"
    elif polarity(stem) == "阳":
        initial = lessons[0]["upper"]
        origin = "day"
        source_path = "自任"
    else:
        initial = branch
        origin = "branch"
        source_path = "自信"

    if BRANCH_PUNISHMENTS[initial] == initial:
        middle = branch if origin == "day" else lessons[0]["upper"]
        trace = ["{}取{}为初传；初传自刑，改取{}为中传".format(source_path, initial, middle)]
        subtype = "杜传"
    else:
        middle = BRANCH_PUNISHMENTS[initial]
        trace = ["{}取{}为初传，所刑{}为中传".format(source_path, initial, middle)]
        subtype = source_path
    next_punishment = BRANCH_PUNISHMENTS[middle]
    if next_punishment in (initial, middle):
        final = BRANCH_CLASHES[middle]
        trace.append("中传刑神重复，取中传所冲{}为末传".format(final))
        subtype = "杜传"
    else:
        final = next_punishment
        trace.append("取中传所刑{}为末传".format(final))
    return {
        "status": "completed", "lesson_type": "伏吟", "source_path": subtype,
        "candidates": [initial], "transmissions": [initial, middle, final], "trace": trace,
    }


def _fanyin_transmissions(day_pillar, plate, lessons):
    branch = day_pillar[1]
    diagonal = _branch_shift(branch, 4)
    initial = plate[diagonal]
    middle = lessons[2]["upper"]
    final = lessons[0]["upper"]
    return {
        "status": "completed", "lesson_type": "返吟", "source_path": "井栏射",
        "candidates": [initial], "transmissions": [initial, middle, final],
        "trace": ["返吟无克，日支{}斜射{}上神{}为初传".format(branch, diagonal, initial),
                  "井栏射取辰上神{}为中传、日上神{}为末传".format(middle, final)],
    }


def _three_transmissions(day_pillar, plate, lessons):
    offset = _plate_offset(plate)
    if offset == 0:
        return _fuyin_transmissions(day_pillar, plate, lessons)

    direct = _direct_transmissions(day_pillar, plate, lessons)
    if direct is not None:
        return direct

    lesson_count = _unique_lesson_count(lessons)
    if offset == 6:
        return _fanyin_transmissions(day_pillar, plate, lessons)
    if lesson_count == 2:
        return _bazhuan_transmissions(day_pillar, lessons)

    remote = _remote_transmissions(day_pillar, plate, lessons)
    if remote is not None:
        return remote
    if lesson_count == 3:
        return _bieze_transmissions(day_pillar, plate, lessons)
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


def _transmission_rule_id(transmissions):
    return {
        "涉害": "LR-SHEHAI-001", "遥克": "LR-REMOTE-001", "昴星": "LR-STAR-001",
        "别责": "LR-BIEZE-001", "八专": "LR-BAZHUAN-001", "伏吟": "LR-FUYIN-001",
        "返吟": "LR-FANYIN-001",
    }.get(transmissions["lesson_type"], "LR-COVERAGE-001" if transmissions["status"] != "completed" else "LR-TRANSMISSION-001")


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
             "rule_ids": [_transmission_rule_id(transmissions)]},
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
