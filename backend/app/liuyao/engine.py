from app.calendar import calendar_analysis
from app.common.casting import derive_coin_lines, nonce_hash
from app.common.five_elements import FIVE_ELEMENTS_CONTROLS, FIVE_ELEMENTS_GENERATES
from app.common.ganzhi import BRANCH_ELEMENTS, EARTHLY_BRANCHES, xun_info
from app.common.serialization import derive_hexagram_facts
from app.common.trigrams import get_trigram_by_number, trigram_to_bits

from .models import SixLineInput, ThreeCoinInput
from .rules import NAJIA, PALACE_BY_LINES, SIX_SPIRITS, SIX_SPIRIT_START


ENGINE_VERSION = "liuyao-engine-2.0.0"
RULE_VERSION = "liuyao-engineering-baseline-2.0.0"


def trigram_number(value):
    source = int(value)
    remainder = source % 8
    return 8 if remainder == 0 else remainder


def moving_line_number(value):
    source = int(value)
    remainder = source % 6
    return 6 if remainder == 0 else remainder


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
    palace_model = PALACE_BY_LINES[bits]
    palace = palace_model.to_dict()
    lower = NAJIA[original["lower_trigram"]["name"]]
    upper = NAJIA[original["upper_trigram"]["name"]]
    stems = (lower[0],) * 3 + (upper[1],) * 3
    branches = lower[2] + upper[3]
    spirit_start = SIX_SPIRIT_START[day_pillar[0]]
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


def _line_bits(line_values):
    request = SixLineInput(tuple(line_values))
    bits = tuple(1 if value in (7, 9) else 0 for value in request.lines)
    moving_lines = [position for position, value in enumerate(request.lines, 1) if value in (6, 9)]
    return request, bits, moving_lines


def _result(hexagrams, calendar, method, method_facts, method_step, calculation_trace):
    day_pillar = calendar["pillars"]["day"]
    palace, xun, lines = _decorate(hexagrams, day_pillar)
    line_values = method_facts.get("input_lines") or [
        (9 if line["is_moving"] else 7) if line["yin_yang"] == "阳" else (6 if line["is_moving"] else 8)
        for line in lines
    ]
    line_types = {6: "老阴", 7: "少阳", 8: "少阴", 9: "老阳"}
    for line, value in zip(lines, line_values):
        line["line_value"] = value
        line["line_type"] = line_types[value]
        line["changed_yin_yang"] = (
            "阴" if line["yin_yang"] == "阳" else "阳"
        ) if line["is_moving"] else line["yin_yang"]
    coverage = {
        "status": "pending_rule_selection",
        "hidden_spirits": [],
        "flying_spirits": [],
        "reason": "伏神飞神取法和标准案例尚未完成规则签署",
    }
    return {
        "schema_version": "2.0",
        "system": "liuyao",
        "school": "jingfang-eight-palace-engineering-baseline",
        "engine_version": ENGINE_VERSION,
        "algorithm_version": ENGINE_VERSION,
        "rule_version": RULE_VERSION,
        "input": method_facts.get("input", {}),
        "normalized_input": method_facts.get("normalized_input", {}),
        "facts": {
            "method": method,
            **{key: value for key, value in method_facts.items() if key not in ("input", "normalized_input")},
            **hexagrams,
            "day_pillar": day_pillar,
            "month_branch": calendar["month_branch"],
            "day_branch": {"name": day_pillar[1], "number": EARTHLY_BRANCHES.index(day_pillar[1]) + 1},
            "palace": palace,
            "xun": xun,
            "line_chart": lines,
            "hidden_flying_spirits": coverage,
        },
        "calculation_trace": calculation_trace + [
            "map original hexagram to {} palace {}".format(palace["name"], palace["stage"]),
            "set host line {} and response line {}".format(palace["host_line"], palace["response_line"]),
            "decorate six lines with Na Jia, relatives and six spirits",
            "derive {} and empty branches {}".format(xun["name"], "、".join(xun["empty_branches"])),
        ],
        "steps": [
            method_step,
            {
                "sequence": 2, "operation": "derive_eight_palace_and_najia",
                "inputs": {"original_lines": hexagrams["original"]["lines"]},
                "output": {"palace": palace, "line_chart": lines},
                "rule_ids": ["LY-PALACE-001", "LY-NAJIA-001", "LY-RELATIVE-001"],
            },
            {
                "sequence": 3, "operation": "derive_month_day_spirits_and_void",
                "inputs": {"month_branch": calendar["month_branch"], "day_pillar": day_pillar},
                "output": {"month_branch": calendar["month_branch"], "xun": xun,
                           "six_spirits": [line["six_spirit"] for line in lines]},
                "rule_ids": ["LY-SPIRIT-001", "CYCLE-XUN-001", "CAL-CYCLE-001"],
            },
            {
                "sequence": 4, "operation": "report_hidden_flying_spirit_coverage",
                "inputs": {"palace": palace["name"], "line_relatives": [line["six_relative"] for line in lines]},
                "output": coverage,
                "rule_ids": ["LY-HIDDEN-FLYING-COVERAGE-001"],
            },
        ],
        "evidence": [],
        "judgements": [],
        "warnings": [
            "六爻纳甲采用京房八宫工程基线，月建日辰旺衰和事项断语尚待专家规则与案例签署。",
            "伏神飞神规则尚未签署，本结果明确不生成推测值。",
        ],
    }


def line_cast(lines, local_datetime, timezone, longitude=None, use_true_solar_time=False):
    request, bits, moving_lines = _line_bits(lines)
    calendar = calendar_analysis(local_datetime, timezone, longitude, use_true_solar_time)
    return _result(
        derive_hexagram_facts(bits, moving_lines),
        calendar,
        "six_lines",
        {
            "input": {"lines": list(request.lines), "local_datetime": local_datetime, "timezone": timezone,
                      "longitude": longitude, "use_true_solar_time": use_true_solar_time},
            "normalized_input": {"lines": list(request.lines), "binary_lines": list(bits),
                                 "moving_lines": moving_lines, "line_order": "bottom_to_top"},
            "input_lines": list(request.lines),
        },
        {
            "sequence": 1, "operation": "normalize_six_line_values",
            "inputs": {"lines": list(request.lines), "line_order": "bottom_to_top"},
            "output": {"binary_lines": list(bits), "moving_lines": moving_lines},
            "rule_ids": ["LY-LINES-001"],
        },
        [
            "read six line values from first line to top line: {}".format(list(request.lines)),
            "map 6/8 to yin, 7/9 to yang: {}".format(list(bits)),
            "mark 6 and 9 as moving lines: {}".format(moving_lines),
        ],
    )


def coin_cast(rounds, local_datetime, timezone, longitude=None, use_true_solar_time=False):
    request = ThreeCoinInput(tuple(tuple(coins) for coins in rounds))
    line_values = request.line_values
    result = line_cast(line_values, local_datetime, timezone, longitude, use_true_solar_time)
    coin_rounds = [
        {"line": position, "coins": list(coins), "value": value}
        for position, (coins, value) in enumerate(zip(request.rounds, line_values), 1)
    ]
    result["facts"]["method"] = "three_coins"
    result["facts"]["coin_rounds"] = coin_rounds
    result["input"] = {"coins": [list(coins) for coins in request.rounds], "local_datetime": local_datetime,
                       "timezone": timezone, "longitude": longitude, "use_true_solar_time": use_true_solar_time}
    result["normalized_input"]["coin_rounds"] = coin_rounds
    result["calculation_trace"] = [
        "line {} coins {} sum to {}".format(row["line"], row["coins"], row["value"])
        for row in coin_rounds
    ] + result["calculation_trace"][1:]
    result["steps"][0] = {
        "sequence": 1, "operation": "sum_six_three_coin_rounds",
        "inputs": {"rounds": [list(coins) for coins in request.rounds], "line_order": "bottom_to_top"},
        "output": {"coin_rounds": coin_rounds, "line_values": list(line_values),
                   "moving_lines": result["facts"]["moving_lines"]},
        "rule_ids": ["LY-COINS-001", "LY-LINES-001"],
    }
    return result


def number_cast(lower_number, upper_number, local_datetime, timezone, longitude=None, use_true_solar_time=False):
    lower_source, upper_source = int(lower_number), int(upper_number)
    lower_index, upper_index = trigram_number(lower_source), trigram_number(upper_source)
    moving_line = moving_line_number(lower_source + upper_source)
    bits = trigram_to_bits(get_trigram_by_number(lower_index)) + trigram_to_bits(get_trigram_by_number(upper_index))
    calendar = calendar_analysis(local_datetime, timezone, longitude, use_true_solar_time)
    return _result(
        derive_hexagram_facts(bits, [moving_line]), calendar, "two_numbers",
        {"input_numbers": {"lower": lower_source, "upper": upper_source}},
        {"sequence": 1, "operation": "numbers_to_hexagram",
         "inputs": {"lower": lower_source, "upper": upper_source},
         "output": {"lower_trigram": lower_index, "upper_trigram": upper_index, "moving_line": moving_line},
         "rule_ids": ["LY-NUMBER-001"]},
        ["map two numbers to lower {}, upper {}, moving line {}".format(lower_index, upper_index, moving_line)],
    )


def time_cast(local_datetime, timezone, longitude=None, use_true_solar_time=False):
    calendar = calendar_analysis(local_datetime, timezone, longitude, use_true_solar_time)
    upper_source = calendar["year_branch"]["number"] + calendar["lunar"]["month"] + calendar["lunar"]["day"]
    lower_source = upper_source + calendar["time_branch"]["number"]
    upper_index, lower_index = trigram_number(upper_source), trigram_number(lower_source)
    moving_line = moving_line_number(lower_source)
    bits = trigram_to_bits(get_trigram_by_number(lower_index)) + trigram_to_bits(get_trigram_by_number(upper_index))
    return _result(
        derive_hexagram_facts(bits, [moving_line]), calendar, "lunar_time",
        {"calendar": {"lunar": calendar["lunar"], "pillars": calendar["pillars"],
                      "year_branch": calendar["year_branch"], "time_branch": calendar["time_branch"]},
         "upper_source": upper_source, "lower_source": lower_source},
        {"sequence": 1, "operation": "calendar_to_hexagram", "inputs": {"calendar": calendar["input"]},
         "output": {"upper_trigram": upper_index, "lower_trigram": lower_index, "moving_line": moving_line},
         "rule_ids": ["LY-TIME-001"]},
        ["calendar numbers -> upper {}, lower {}, moving line {}".format(upper_source, lower_source, moving_line)],
    )


def auto_cast(cast_nonce, local_datetime, timezone, longitude=None, use_true_solar_time=False):
    line_values, coin_rows = derive_coin_lines("liuyao-auto-coins-v1", cast_nonce)
    rounds = [row["coins"] for row in coin_rows]
    result = coin_cast(rounds, local_datetime, timezone, longitude, use_true_solar_time)
    result["facts"]["method"] = "personalized_three_coin"
    result["facts"]["cast_nonce_hash"] = nonce_hash(cast_nonce)
    result["input"] = {"cast_nonce_hash": nonce_hash(cast_nonce), "local_datetime": local_datetime,
                       "timezone": timezone, "longitude": longitude, "use_true_solar_time": use_true_solar_time}
    result["steps"][0]["operation"] = "derive_personalized_three_coin_lines"
    result["steps"][0]["inputs"] = {"cast_nonce_hash": nonce_hash(cast_nonce), "domain": "liuyao-auto-coins-v1"}
    result["steps"][0]["rule_ids"] = ["LY-AUTO-COIN-001", "LY-COINS-001"]
    return result


__all__ = (
    "PALACE_BY_LINES", "auto_cast", "coin_cast", "line_cast", "number_cast", "time_cast",
)
