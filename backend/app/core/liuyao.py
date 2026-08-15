from .calendar import calendar_analysis
from .constants import (
    EARTHLY_BRANCHES,
    FIVE_ELEMENTS_CONTROLS,
    FIVE_ELEMENTS_GENERATES,
    TRIGRAMS,
    moving_line_number,
    trigram_number,
)
from .cyclical import BRANCH_ELEMENTS, xun_info
from .iching import derive_hexagrams


ENGINE_VERSION = "liuyao-engine-1.0.0"
RULE_VERSION = "liuyao-engineering-baseline-1.0.0"

NAJIA = {
    "乾": {"inner_stem": "甲", "outer_stem": "壬", "inner": ("子", "寅", "辰"), "outer": ("午", "申", "戌")},
    "坤": {"inner_stem": "乙", "outer_stem": "癸", "inner": ("未", "巳", "卯"), "outer": ("丑", "亥", "酉")},
    "震": {"inner_stem": "庚", "outer_stem": "庚", "inner": ("子", "寅", "辰"), "outer": ("午", "申", "戌")},
    "巽": {"inner_stem": "辛", "outer_stem": "辛", "inner": ("丑", "亥", "酉"), "outer": ("未", "巳", "卯")},
    "坎": {"inner_stem": "戊", "outer_stem": "戊", "inner": ("寅", "辰", "午"), "outer": ("申", "戌", "子")},
    "离": {"inner_stem": "己", "outer_stem": "己", "inner": ("卯", "丑", "亥"), "outer": ("酉", "未", "巳")},
    "艮": {"inner_stem": "丙", "outer_stem": "丙", "inner": ("辰", "午", "申"), "outer": ("戌", "子", "寅")},
    "兑": {"inner_stem": "丁", "outer_stem": "丁", "inner": ("巳", "卯", "丑"), "outer": ("亥", "酉", "未")},
}

SIX_SPIRITS = ("青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武")
SIX_SPIRIT_START = {
    "甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2,
    "己": 3, "庚": 4, "辛": 4, "壬": 5, "癸": 5,
}
PALACE_STAGES = (
    ("本宫", (), 6),
    ("一世", (1,), 1),
    ("二世", (1, 2), 2),
    ("三世", (1, 2, 3), 3),
    ("四世", (1, 2, 3, 4), 4),
    ("五世", (1, 2, 3, 4, 5), 5),
    ("游魂", (1, 2, 3, 5), 4),
    ("归魂", (5,), 3),
)


def _palace_index():
    result = {}
    for trigram in TRIGRAMS.values():
        pure = tuple(trigram["lines"] + trigram["lines"])
        for stage, changes, host_line in PALACE_STAGES:
            bits = tuple(1 - bit if position in changes else bit for position, bit in enumerate(pure, 1))
            result[bits] = {
                "name": trigram["name"],
                "element": trigram["element"],
                "stage": stage,
                "host_line": host_line,
                "response_line": ((host_line + 2) % 6) + 1,
            }
    return result


PALACE_BY_LINES = _palace_index()


def _six_relative(palace_element, line_element):
    if palace_element == line_element:
        return "兄弟"
    if FIVE_ELEMENTS_GENERATES[line_element] == palace_element:
        return "父母"
    if FIVE_ELEMENTS_GENERATES[palace_element] == line_element:
        return "子孙"
    if FIVE_ELEMENTS_CONTROLS[line_element] == palace_element:
        return "官鬼"
    if FIVE_ELEMENTS_CONTROLS[palace_element] == line_element:
        return "妻财"
    raise ValueError("unknown five-element relationship")


def _decorate(hexagrams, day_pillar):
    original = hexagrams["original"]
    bits = tuple(original["lines"])
    palace = PALACE_BY_LINES[bits]
    lower = NAJIA[original["lower_trigram"]["name"]]
    upper = NAJIA[original["upper_trigram"]["name"]]
    stems = (lower["inner_stem"],) * 3 + (upper["outer_stem"],) * 3
    branches = lower["inner"] + upper["outer"]
    day_stem = day_pillar[0]
    spirit_start = SIX_SPIRIT_START[day_stem]
    xun = xun_info(day_pillar)
    moving = set(hexagrams["moving_lines"])
    lines = []
    for index, (bit, stem, branch) in enumerate(zip(bits, stems, branches), 1):
        element = BRANCH_ELEMENTS[branch]
        roles = []
        if index == palace["host_line"]:
            roles.append("世")
        if index == palace["response_line"]:
            roles.append("应")
        lines.append({
            "position": index,
            "yin_yang": "阳" if bit else "阴",
            "is_moving": index in moving,
            "najia_stem": stem,
            "najia_branch": branch,
            "element": element,
            "six_relative": _six_relative(palace["element"], element),
            "six_spirit": SIX_SPIRITS[(spirit_start + index - 1) % 6],
            "is_void": branch in xun["empty_branches"],
            "roles": roles,
        })
    return palace, xun, lines


def _result(hexagrams, calendar, method, method_facts, method_step):
    day_pillar = calendar["pillars"]["day"]
    palace, xun, lines = _decorate(hexagrams, day_pillar)
    return {
        "schema_version": "1.0",
        "system": "liuyao",
        "school": "mvp-engineering-baseline",
        "engine_version": ENGINE_VERSION,
        "rule_version": RULE_VERSION,
        "facts": {
            "method": method,
            **method_facts,
            **hexagrams,
            "day_pillar": day_pillar,
            "palace": palace,
            "xun": xun,
            "line_chart": lines,
        },
        "steps": [
            method_step,
            {
                "sequence": 2,
                "operation": "derive_eight_palace_and_najia",
                "inputs": {"original_lines": hexagrams["original"]["lines"]},
                "output": {"palace": palace, "line_chart": lines},
                "rule_ids": ["LY-PALACE-001", "LY-NAJIA-001", "LY-RELATIVE-001"],
            },
            {
                "sequence": 3,
                "operation": "derive_day_spirits_and_void",
                "inputs": {"day_pillar": day_pillar},
                "output": {"xun": xun, "six_spirits": [line["six_spirit"] for line in lines]},
                "rule_ids": ["LY-SPIRIT-001", "CYCLE-XUN-001"],
            },
        ],
        "evidence": [],
        "judgements": [],
        "warnings": ["六爻纳甲采用京房八宫工程基线，变爻进退神、月建日辰旺衰和事项断语尚待专家规则与案例签署。"],
    }


def number_cast(lower_number, upper_number, local_datetime, timezone, longitude=None, use_true_solar_time=False):
    lower_source = int(lower_number)
    upper_source = int(upper_number)
    lower_index = trigram_number(lower_source)
    upper_index = trigram_number(upper_source)
    moving_line = moving_line_number(lower_source + upper_source)
    bits = TRIGRAMS[lower_index]["lines"] + TRIGRAMS[upper_index]["lines"]
    hexagrams = derive_hexagrams(bits, [moving_line])
    calendar = calendar_analysis(local_datetime, timezone, longitude, use_true_solar_time)
    return _result(
        hexagrams,
        calendar,
        "two_numbers",
        {"input_numbers": {"lower": lower_source, "upper": upper_source}},
        {
            "sequence": 1,
            "operation": "numbers_to_hexagram",
            "inputs": {"lower": lower_source, "upper": upper_source},
            "output": {"lower_trigram": lower_index, "upper_trigram": upper_index, "moving_line": moving_line},
            "rule_ids": ["LY-NUMBER-001"],
        },
    )


def time_cast(local_datetime, timezone, longitude=None, use_true_solar_time=False):
    calendar = calendar_analysis(local_datetime, timezone, longitude, use_true_solar_time)
    upper_source = calendar["year_branch"]["number"] + calendar["lunar"]["month"] + calendar["lunar"]["day"]
    lower_source = upper_source + calendar["time_branch"]["number"]
    upper_index = trigram_number(upper_source)
    lower_index = trigram_number(lower_source)
    moving_line = moving_line_number(lower_source)
    bits = TRIGRAMS[lower_index]["lines"] + TRIGRAMS[upper_index]["lines"]
    return _result(
        derive_hexagrams(bits, [moving_line]),
        calendar,
        "lunar_time",
        {
            "calendar": {
                "lunar": calendar["lunar"], "pillars": calendar["pillars"],
                "year_branch": calendar["year_branch"], "time_branch": calendar["time_branch"],
            },
            "upper_source": upper_source,
            "lower_source": lower_source,
        },
        {
            "sequence": 1,
            "operation": "calendar_to_hexagram",
            "inputs": {"calendar": calendar["input"]},
            "output": {"upper_trigram": upper_index, "lower_trigram": lower_index, "moving_line": moving_line},
            "rule_ids": ["LY-TIME-001"],
        },
    )
