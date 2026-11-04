from app.calendar import calendar_analysis
from app.common.casting import derive_coin_lines, nonce_hash
from app.common.five_elements import FIVE_ELEMENTS_CONTROLS, FIVE_ELEMENTS_GENERATES
from app.common.ganzhi import (
    BRANCH_CLASH, BRANCH_COMBINE, BRANCH_ELEMENTS, BRANCH_TRIPLE,
    EARTHLY_BRANCHES, xun_info,
)
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


# 六亲补缺的固定顺序，保证输出稳定可复核
HIDDEN_RELATIVE_ORDER = ("父母", "兄弟", "子孙", "妻财", "官鬼")


def _month_strength(element, month_element):
    """单爻在月建下的旺衰（旺/相/休/囚/死），与用神旺衰同一套五行口径。"""
    if not element or not month_element:
        return ""
    if element == month_element:
        return "旺"
    if FIVE_ELEMENTS_GENERATES.get(month_element) == element:
        return "相"
    if FIVE_ELEMENTS_GENERATES.get(element) == month_element:
        return "休"
    if FIVE_ELEMENTS_CONTROLS.get(month_element) == element:
        return "囚"
    return "死"


def _branch_relation(branch, reference):
    """爻支与参照地支（日辰）的关系。"""
    if not reference or branch not in BRANCH_ELEMENTS or reference not in BRANCH_ELEMENTS:
        return ""
    if branch == reference:
        return "临"
    if BRANCH_CLASH.get(reference) == branch:
        return "冲"
    if BRANCH_COMBINE.get(reference) == branch:
        return "合"
    element, ref_element = BRANCH_ELEMENTS[branch], BRANCH_ELEMENTS[reference]
    if element == ref_element:
        return "同气"
    if FIVE_ELEMENTS_GENERATES.get(ref_element) == element:
        return "受生"
    if FIVE_ELEMENTS_GENERATES.get(element) == ref_element:
        return "泄气"
    if FIVE_ELEMENTS_CONTROLS.get(ref_element) == element:
        return "受克"
    return "克"


def _void_state(branch, empty_branches, day_branch):
    """旬空状态：空亡之爻逢日辰同支为填实，逢日冲为冲空。"""
    if branch not in empty_branches:
        return ""
    if branch == day_branch:
        return "填实"
    if BRANCH_CLASH.get(day_branch) == branch:
        return "冲空"
    return "旬空"


def _pure_palace_chart(palace_name, palace_element):
    """本宫首卦（八纯卦）的纳甲六亲，用于补齐本卦缺失的六亲（伏神来源）。"""
    najia = NAJIA[palace_name]
    stems = (najia[0],) * 3 + (najia[1],) * 3
    branches = najia[2] + najia[3]
    return [
        {
            "position": index,
            "najia_stem": stem,
            "najia_branch": branch,
            "element": BRANCH_ELEMENTS[branch],
            "six_relative": _six_relative(palace_element, BRANCH_ELEMENTS[branch]),
        }
        for index, (stem, branch) in enumerate(zip(stems, branches), 1)
    ]


# 进神：亥化子、寅化卯、巳化午、申化酉、丑化辰、辰化未、未化戌、戌化丑；反向为退神
ADVANCE_BRANCH = {
    "亥": "子", "寅": "卯", "巳": "午", "申": "酉",
    "丑": "辰", "辰": "未", "未": "戌", "戌": "丑",
}
RETREAT_BRANCH = {target: source for source, target in ADVANCE_BRANCH.items()}


def _advance_retreat(original_branch, changed_branch):
    if ADVANCE_BRANCH.get(original_branch) == changed_branch:
        return "进神"
    if RETREAT_BRANCH.get(original_branch) == changed_branch:
        return "退神"
    return ""


def _decorate_changed(hexagrams, palace):
    """给变卦装纳甲，用于动爻的进退神与变爻六亲判断。"""
    changed = hexagrams["changed"]
    lower = NAJIA[changed["lower_trigram"]["name"]]
    upper = NAJIA[changed["upper_trigram"]["name"]]
    stems = (lower[0],) * 3 + (upper[1],) * 3
    branches = lower[2] + upper[3]
    return [
        {
            "position": index,
            "najia_stem": stem,
            "najia_branch": branch,
            "element": BRANCH_ELEMENTS[branch],
            "six_relative": _six_relative(palace["element"], BRANCH_ELEMENTS[branch]),
        }
        for index, (stem, branch) in enumerate(zip(stems, branches), 1)
    ]


def _branch_structures(moving_branches, month_branch, day_branch):
    """动爻与月建、日辰之间可确定判定的三合局与六合。

    三合局要求三支齐备且每一支都来自动爻或月建日辰；
    六合取池内任意两支成六合者，来源写明月建/日辰/动爻。
    """
    pool = {}
    for branch in moving_branches:
        pool.setdefault(branch, []).append("动爻")
    for branch, source in ((month_branch, "月建"), (day_branch, "日辰")):
        if branch in BRANCH_ELEMENTS:
            pool.setdefault(branch, []).append(source)
    sanhe = []
    for group, element in BRANCH_TRIPLE.items():
        members = [
            {"branch": branch, "sources": sorted(set(pool[branch]))}
            for branch in group if branch in pool
        ]
        if len(members) == 3:
            sanhe.append({"branches": list(group), "element": element, "members": members})
    liuhe = []
    seen = set()
    for first in BRANCH_ELEMENTS:
        second = BRANCH_COMBINE[first]
        key = tuple(sorted((first, second)))
        if key in seen or first not in pool or second not in pool:
            continue
        seen.add(key)
        liuhe.append({
            "branches": sorted((first, second)),
            "members": [
                {"branch": branch, "sources": sorted(set(pool[branch]))}
                for branch in sorted((first, second))
            ],
        })
    return {"sanhe": sanhe, "liuhe": liuhe}


def _flying_hidden_relation(flying_element, hidden_element):
    if flying_element == hidden_element:
        return "飞伏比和"
    if FIVE_ELEMENTS_GENERATES.get(flying_element) == hidden_element:
        return "飞生伏"
    if FIVE_ELEMENTS_GENERATES.get(hidden_element) == flying_element:
        return "伏生飞"
    if FIVE_ELEMENTS_CONTROLS.get(flying_element) == hidden_element:
        return "飞克伏"
    return "伏克飞"


def _hidden_flying_spirits(lines, palace):
    """按八宫首卦补缺取伏神，飞神为本卦同位爻。

    本卦六爻未出现的六亲，到本宫首卦（八纯卦）同一爻位取纳甲干支为伏神，
    该位本卦之爻即飞神。首卦中同一六亲出现两次时取最低爻位，
    另一处写入 alternative_positions，避免静默丢信息。
    """
    present = {line["six_relative"] for line in lines}
    pure = _pure_palace_chart(palace["name"], palace["element"])
    hidden = []
    for relative in HIDDEN_RELATIVE_ORDER:
        if relative in present:
            continue
        positions = [item["position"] for item in pure if item["six_relative"] == relative]
        if not positions:
            continue
        position = positions[0]
        source, host = pure[position - 1], lines[position - 1]
        hidden.append({
            "six_relative": relative,
            "position": position,
            "najia_stem": source["najia_stem"],
            "najia_branch": source["najia_branch"],
            "element": source["element"],
            "source": "本宫首卦{}第{}爻".format(palace["name"], position),
            "alternative_positions": positions[1:],
            "flying_spirit": {
                "position": position,
                "six_relative": host["six_relative"],
                "najia_stem": host["najia_stem"],
                "najia_branch": host["najia_branch"],
                "element": host["element"],
            },
            "relation": _flying_hidden_relation(host["element"], source["element"]),
        })
    flying = [
        dict(item["flying_spirit"], hidden_relative=item["six_relative"], relation=item["relation"])
        for item in hidden
    ]
    return {
        "status": "completed",
        "method": "eight_palace_pure_hexagram",
        "palace_pure_hexagram": palace["name"],
        "present_relatives": [item for item in HIDDEN_RELATIVE_ORDER if item in present],
        "missing_relatives": [item for item in HIDDEN_RELATIVE_ORDER if item not in present],
        "hidden_spirits": hidden,
        "flying_spirits": flying,
        "reason": "",
        "note": "伏神取本宫首卦同位爻，飞神取本卦同位爻；首卦同亲多处出现时取最低爻位并在 alternative_positions 标注。",
    }


def _decorate(hexagrams, day_pillar, month_branch):
    if isinstance(month_branch, dict):
        month_branch = month_branch.get("name", "")
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
    month_element = BRANCH_ELEMENTS.get(month_branch, "")
    day_branch = day_pillar[1]
    lines = []
    for index, (bit, stem, branch) in enumerate(zip(bits, stems, branches), 1):
        element = BRANCH_ELEMENTS[branch]
        roles = []
        if index == palace["host_line"]:
            roles.append("世")
        if index == palace["response_line"]:
            roles.append("应")
        strength = _month_strength(element, month_element)
        day_clash = BRANCH_CLASH.get(day_branch) == branch
        is_quiet = index not in moving
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
            "void_state": _void_state(branch, xun["empty_branches"], day_branch),
            "month_strength": strength,
            "is_month_break": BRANCH_CLASH.get(month_branch) == branch,
            "day_relation": _branch_relation(branch, day_branch),
            "is_day_clash": day_clash,
            "is_day_combine": BRANCH_COMBINE.get(day_branch) == branch,
            # 静爻受日辰冲：月建旺相为暗动，休囚为日破
            "is_dark_move": is_quiet and day_clash and strength in ("旺", "相"),
            "is_day_break": is_quiet and day_clash and strength not in ("旺", "相"),
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
    palace, xun, lines = _decorate(hexagrams, day_pillar, calendar["month_branch"]["name"])
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
    changed_lines = _decorate_changed(hexagrams, palace)
    for line, changed_line in zip(lines, changed_lines):
        line["changed_najia_stem"] = changed_line["najia_stem"]
        line["changed_najia_branch"] = changed_line["najia_branch"]
        line["changed_element"] = changed_line["element"]
        line["changed_six_relative"] = changed_line["six_relative"]
        line["advance_retreat"] = (
            _advance_retreat(line["najia_branch"], changed_line["najia_branch"])
            if line["is_moving"] else ""
        )
    moving_branches = [line["najia_branch"] for line in lines if line["is_moving"]]
    structures = _branch_structures(moving_branches, calendar["month_branch"]["name"], day_pillar[1])
    coverage = _hidden_flying_spirits(lines, palace)
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
            "changed_line_chart": changed_lines,
            "branch_structures": structures,
            "hidden_flying_spirits": coverage,
        },
        "calculation_trace": calculation_trace + [
            "map original hexagram to {} palace {}".format(palace["name"], palace["stage"]),
            "set host line {} and response line {}".format(palace["host_line"], palace["response_line"]),
            "decorate six lines with Na Jia, relatives and six spirits",
            "derive {} and empty branches {}".format(xun["name"], "、".join(xun["empty_branches"])),
            "mark month break, day clash, dark move and day break per line",
            "decorate changed hexagram with Na Jia and mark advance or retreat branches",
            "collect sanhe and liuhe among moving lines, month and day: {}".format(
                "、".join("{}局".format(item["element"]) for item in structures["sanhe"])
                or "无三合局"
            ),
            "fill missing relatives from {} palace pure hexagram: {}".format(
                palace["name"], "、".join(item["six_relative"] for item in coverage["hidden_spirits"]) or "无缺"
            ),
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
                           "six_spirits": [line["six_spirit"] for line in lines],
                           "month_breaks": [line["position"] for line in lines if line["is_month_break"]],
                           "day_breaks": [line["position"] for line in lines if line["is_day_break"]],
                           "dark_moves": [line["position"] for line in lines if line["is_dark_move"]]},
                "rule_ids": ["LY-SPIRIT-001", "CYCLE-XUN-001", "CAL-CYCLE-001", "LY-DAYMONTH-001"],
            },
            {
                "sequence": 4, "operation": "derive_hidden_flying_spirits",
                "inputs": {"palace": palace["name"], "line_relatives": [line["six_relative"] for line in lines]},
                "output": coverage,
                "rule_ids": ["LY-HIDDEN-FLYING-001"],
            },
            {
                "sequence": 5, "operation": "collect_branch_structures",
                "inputs": {
                    "moving_branches": moving_branches,
                    "month_branch": calendar["month_branch"]["name"],
                    "day_branch": day_pillar[1],
                },
                "output": structures,
                "rule_ids": ["LY-BRANCHSTRUCT-001"],
            },
        ],
        "evidence": [],
        "judgements": [],
        "warnings": [
            "六爻纳甲采用京房八宫工程基线，月建日辰旺衰和事项断语尚待专家规则与案例签署。",
            "伏神按本宫首卦（八纯卦）同位纳甲六亲补缺推导，取法为标准工程基线，断语仍待案例签署。",
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
