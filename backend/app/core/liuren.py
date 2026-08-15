from lunar_python import Solar

from .calendar import calendar_analysis
from .constants import EARTHLY_BRANCHES, FIVE_ELEMENTS_CONTROLS
from .cyclical import BRANCH_ELEMENTS, STEM_ELEMENTS, polarity, xun_info


ENGINE_VERSION = "liuren-engine-1.0.0+lunar-python-1.4.8"
RULE_VERSION = "liuren-engineering-baseline-1.0.0"

MONTH_GENERALS = {
    "雨水": ("亥", "登明"), "春分": ("戌", "河魁"), "谷雨": ("酉", "从魁"),
    "小满": ("申", "传送"), "夏至": ("未", "小吉"), "大暑": ("午", "胜光"),
    "处暑": ("巳", "太乙"), "秋分": ("辰", "天罡"), "霜降": ("卯", "太冲"),
    "小雪": ("寅", "功曹"), "冬至": ("丑", "大吉"), "大寒": ("子", "神后"),
}
STEM_LODGES = {"甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳", "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑"}
NOBLE_BRANCHES = {
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"), "丙": ("亥", "酉"),
    "丁": ("亥", "酉"), "壬": ("巳", "卯"), "癸": ("巳", "卯"), "辛": ("午", "寅"),
}
HEAVENLY_GENERALS = ("贵人", "螣蛇", "朱雀", "六合", "勾陈", "青龙", "天空", "白虎", "太常", "玄武", "太阴", "天后")


def _month_general(calendar):
    solar = calendar["solar"]
    lunar = Solar.fromYmdHms(solar["year"], solar["month"], solar["day"], solar["hour"], solar["minute"], solar["second"]).getLunar()
    qi = lunar.getPrevQi()
    if lunar.getCurrentQi() is not None:
        qi = lunar.getCurrentQi()
    name = qi.getName()
    branch, title = MONTH_GENERALS[name]
    return {"branch": branch, "name": title, "boundary_term": name, "boundary_datetime": qi.getSolar().toYmdHms()}


def _heaven_plate(month_general_branch, occupation_branch):
    general_index = EARTHLY_BRANCHES.index(month_general_branch)
    hour_index = EARTHLY_BRANCHES.index(occupation_branch)
    return {
        ground: EARTHLY_BRANCHES[(general_index + index - hour_index) % 12]
        for index, ground in enumerate(EARTHLY_BRANCHES)
    }


def _lesson(sequence, lower, upper):
    lower_element = STEM_ELEMENTS.get(lower, BRANCH_ELEMENTS.get(lower))
    upper_element = BRANCH_ELEMENTS[upper]
    relation = "none"
    if FIVE_ELEMENTS_CONTROLS[lower_element] == upper_element:
        relation = "lower_controls_upper"
    elif FIVE_ELEMENTS_CONTROLS[upper_element] == lower_element:
        relation = "upper_controls_lower"
    return {
        "sequence": sequence,
        "lower": lower,
        "upper": upper,
        "lower_element": lower_element,
        "upper_element": upper_element,
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
    seen = set()
    for lesson in lessons:
        if lesson["relation"] == relation and lesson["upper"] not in seen:
            seen.add(lesson["upper"])
            result.append(lesson["upper"])
    return result


def _three_transmissions(day_pillar, plate, lessons):
    path = None
    candidates = _unique_candidates(lessons, "lower_controls_upper")
    if candidates:
        path = "贼克"
    else:
        candidates = _unique_candidates(lessons, "upper_controls_lower")
        if candidates:
            path = "克"

    selected = None
    selection = path
    if len(candidates) == 1:
        selected = candidates[0]
    elif len(candidates) > 1:
        matching = [branch for branch in candidates if polarity(branch) == polarity(day_pillar[0])]
        if len(matching) == 1:
            selected = matching[0]
            selection = "比用"

    if selected:
        middle = plate[selected]
        final = plate[middle]
        return {
            "status": "completed",
            "lesson_type": selection,
            "source_path": path,
            "candidates": candidates,
            "transmissions": [selected, middle, final],
        }

    offset = (EARTHLY_BRANCHES.index(next(iter(plate.values()))) - EARTHLY_BRANCHES.index(EARTHLY_BRANCHES[0])) % 12
    if offset == 0:
        pending = "伏吟"
    elif offset == 6:
        pending = "返吟"
    elif len(candidates) > 1:
        pending = "涉害"
    else:
        pending = "遥克、昴星或特殊课式"
    return {
        "status": "unsupported_rule_path",
        "lesson_type": None,
        "source_path": path,
        "candidates": candidates,
        "pending_path": pending,
        "transmissions": [],
    }


def _heavenly_generals(day_stem, plate, hour, day_period):
    noble_branch = NOBLE_BRANCHES[day_stem][0 if day_period == "day" else 1]
    noble_ground = next(ground for ground, heaven in plate.items() if heaven == noble_branch)
    start = EARTHLY_BRANCHES.index(noble_ground)
    direction = 1 if noble_ground in ("亥", "子", "丑", "寅", "卯", "辰") else -1
    by_ground = {}
    for offset, general in enumerate(HEAVENLY_GENERALS):
        by_ground[EARTHLY_BRANCHES[(start + direction * offset) % 12]] = general
    return {
        "period": day_period,
        "civil_hour": hour,
        "noble_branch": noble_branch,
        "noble_ground": noble_ground,
        "distribution_direction": "顺布" if direction == 1 else "逆布",
        "by_ground": by_ground,
    }


def _cast(local_datetime, timezone, occupation_branch=None, occupation_number=None, longitude=None, use_true_solar_time=False):
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
    warnings = ["大六壬月将、天地盘、四课和天将采用工程基线，尚待专家与标准案例签署。"]
    if transmissions["status"] != "completed":
        warnings.append("本课进入首版未覆盖的{}路径，系统未生成三传猜测值。".format(transmissions["pending_path"]))
    return {
        "schema_version": "1.0",
        "system": "liuren",
        "school": "mvp-engineering-baseline",
        "engine_version": ENGINE_VERSION,
        "rule_version": RULE_VERSION,
        "facts": {
            "method": method,
            "day_pillar": day_pillar,
            "actual_time_branch": actual_branch,
            "occupation_time": {"branch": selected_branch, "number": EARTHLY_BRANCHES.index(selected_branch) + 1, "input_number": occupation_number},
            "month_general": month_general,
            "earth_plate": list(EARTHLY_BRANCHES),
            "heaven_plate": plate,
            "four_lessons": lessons,
            "three_transmissions": transmissions,
            "heavenly_generals": generals,
            "xun": xun,
        },
        "steps": [
            {
                "sequence": 1,
                "operation": "derive_month_general_and_occupation_time",
                "inputs": {"local_datetime": local_datetime, "occupation_number": occupation_number},
                "output": {"month_general": month_general, "occupation_branch": selected_branch},
                "rule_ids": ["LR-MONTH-GENERAL-001", "LR-HOUR-001" if occupation_number is None else "LR-NUMBER-001"],
            },
            {
                "sequence": 2,
                "operation": "derive_heaven_plate_and_four_lessons",
                "inputs": {"month_general": month_general["branch"], "occupation_branch": selected_branch, "day_pillar": day_pillar},
                "output": {"heaven_plate": plate, "four_lessons": lessons},
                "rule_ids": ["LR-PLATE-001", "LR-LESSON-001"],
            },
            {
                "sequence": 3,
                "operation": "derive_transmissions_generals_and_void",
                "inputs": {"four_lessons": lessons, "day_pillar": day_pillar},
                "output": {"three_transmissions": transmissions, "heavenly_generals": generals, "xun": xun},
                "rule_ids": ["LR-TRANSMISSION-001", "LR-GENERAL-001", "CYCLE-XUN-001"],
            },
        ],
        "evidence": [],
        "judgements": [],
        "warnings": warnings,
    }


def time_cast(local_datetime, timezone, longitude=None, use_true_solar_time=False):
    return _cast(local_datetime, timezone, longitude=longitude, use_true_solar_time=use_true_solar_time)


def number_cast(number, local_datetime, timezone, longitude=None, use_true_solar_time=False):
    source = int(number)
    branch = EARTHLY_BRANCHES[(source - 1) % 12]
    return _cast(
        local_datetime, timezone, occupation_branch=branch, occupation_number=source,
        longitude=longitude, use_true_solar_time=use_true_solar_time,
    )
