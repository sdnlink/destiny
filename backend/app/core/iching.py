from .constants import (
    HEXAGRAM_NAMES,
    KING_WEN_MATRIX,
    TRIGRAM_BY_LINES,
    TRIGRAMS,
    moving_line_number,
    trigram_number,
)
from .calendar import calendar_analysis
from .casting import derive_coin_lines, nonce_hash


ENGINE_VERSION = "yi-engine-1.0.0"
RULE_VERSION = "yi-mvp-baseline-1.0.0"


def _line_bits(line_values):
    if len(line_values) != 6:
        raise ValueError("exactly six lines are required from first to top")
    invalid = [value for value in line_values if value not in (6, 7, 8, 9)]
    if invalid:
        raise ValueError("line values must be 6, 7, 8, or 9")
    return tuple(1 if value in (7, 9) else 0 for value in line_values)


def _trigram(lines):
    try:
        return TRIGRAM_BY_LINES[tuple(lines)]
    except KeyError:
        raise ValueError("trigram lines must contain exactly three binary values")


def hexagram_from_bits(lines):
    if len(lines) != 6 or any(value not in (0, 1) for value in lines):
        raise ValueError("hexagram lines must contain six binary values from first to top")
    lower = _trigram(lines[:3])
    upper = _trigram(lines[3:])
    ordinal = KING_WEN_MATRIX[upper["number"] - 1][lower["number"] - 1]
    return {
        "ordinal": ordinal,
        "name": HEXAGRAM_NAMES[ordinal - 1],
        "symbol": chr(0x4DBF + ordinal),
        "lines": list(lines),
        "lower_trigram": lower,
        "upper_trigram": upper,
    }


def derive_hexagrams(lines, moving_lines):
    moving_set = set(moving_lines)
    if any(index < 1 or index > 6 for index in moving_set):
        raise ValueError("moving line positions must be between 1 and 6")
    changed = tuple(1 - value if index in moving_set else value for index, value in enumerate(lines, 1))
    mutual = (lines[1], lines[2], lines[3], lines[2], lines[3], lines[4])
    opposite = tuple(1 - value for value in lines)
    reversed_lines = tuple(reversed(lines))
    return {
        "original": hexagram_from_bits(tuple(lines)),
        "changed": hexagram_from_bits(changed),
        "mutual": hexagram_from_bits(mutual),
        "opposite": hexagram_from_bits(opposite),
        "reversed": hexagram_from_bits(reversed_lines),
        "moving_lines": sorted(moving_set),
    }


def manual_cast(line_values):
    lines = _line_bits(line_values)
    moving_lines = [index for index, value in enumerate(line_values, 1) if value in (6, 9)]
    facts = derive_hexagrams(lines, moving_lines)
    return {
        "schema_version": "1.0",
        "system": "zhouyi",
        "school": "mvp-engineering-baseline",
        "engine_version": ENGINE_VERSION,
        "rule_version": RULE_VERSION,
        "facts": {"input_lines": list(line_values), **facts},
        "steps": [
            {
                "sequence": 1,
                "operation": "normalize_manual_lines",
                "inputs": {"line_values": list(line_values)},
                "output": {"binary_lines": list(lines), "moving_lines": moving_lines},
                "rule_ids": ["YI-MANUAL-001"],
            },
            {
                "sequence": 2,
                "operation": "derive_related_hexagrams",
                "inputs": {"binary_lines": list(lines), "moving_lines": moving_lines},
                "output": {key: value["ordinal"] for key, value in facts.items() if isinstance(value, dict)},
                "rule_ids": ["YI-RELATION-001"],
            },
        ],
        "evidence": [],
        "judgements": [],
        "warnings": ["流派解释和事项吉凶尚未经过专家签署，本结果只包含确定性卦象事实。"],
    }


def number_cast(lower_number, upper_number):
    lower_index = trigram_number(lower_number)
    upper_index = trigram_number(upper_number)
    moving_line = moving_line_number(int(lower_number) + int(upper_number))
    lines = TRIGRAMS[lower_index]["lines"] + TRIGRAMS[upper_index]["lines"]
    facts = derive_hexagrams(lines, [moving_line])
    return {
        "schema_version": "1.0",
        "system": "zhouyi",
        "school": "mvp-engineering-baseline",
        "engine_version": ENGINE_VERSION,
        "rule_version": RULE_VERSION,
        "facts": {
            "input_numbers": {"lower": int(lower_number), "upper": int(upper_number)},
            "lower_trigram_number": lower_index,
            "upper_trigram_number": upper_index,
            **facts,
        },
        "steps": [
            {
                "sequence": 1,
                "operation": "numbers_to_trigrams",
                "inputs": {"lower": int(lower_number), "upper": int(upper_number)},
                "output": {"lower_trigram": lower_index, "upper_trigram": upper_index},
                "rule_ids": ["YI-NUMBER-001"],
            },
            {
                "sequence": 2,
                "operation": "derive_moving_line",
                "inputs": {"sum": int(lower_number) + int(upper_number)},
                "output": {"moving_line": moving_line},
                "rule_ids": ["YI-NUMBER-002"],
            },
        ],
        "evidence": [],
        "judgements": [],
        "warnings": ["数字起卦采用MVP工程基线；事项断语尚未经过专家签署。"],
    }


def time_cast(local_datetime, timezone, longitude=None, use_true_solar_time=False):
    calendar = calendar_analysis(local_datetime, timezone, longitude, use_true_solar_time)
    upper_source = calendar["year_branch"]["number"] + calendar["lunar"]["month"] + calendar["lunar"]["day"]
    lower_source = upper_source + calendar["time_branch"]["number"]
    upper_index = trigram_number(upper_source)
    lower_index = trigram_number(lower_source)
    moving_line = moving_line_number(lower_source)
    lines = TRIGRAMS[lower_index]["lines"] + TRIGRAMS[upper_index]["lines"]
    facts = derive_hexagrams(lines, [moving_line])
    return {
        "schema_version": "1.0",
        "system": "zhouyi",
        "school": "mvp-engineering-baseline",
        "engine_version": ENGINE_VERSION,
        "rule_version": RULE_VERSION,
        "facts": {
            "method": "lunar_time",
            "calendar": {
                "lunar": calendar["lunar"],
                "pillars": calendar["pillars"],
                "year_branch": calendar["year_branch"],
                "time_branch": calendar["time_branch"],
            },
            "upper_source": upper_source,
            "lower_source": lower_source,
            "upper_trigram_number": upper_index,
            "lower_trigram_number": lower_index,
            "moving_line": moving_line,
            **facts,
        },
        "steps": [
            {
                "sequence": 1,
                "operation": "calendar_to_time_numbers",
                "inputs": {
                    "year_branch_number": calendar["year_branch"]["number"],
                    "lunar_month": calendar["lunar"]["month"],
                    "lunar_day": calendar["lunar"]["day"],
                    "time_branch_number": calendar["time_branch"]["number"],
                },
                "output": {"upper_source": upper_source, "lower_source": lower_source},
                "rule_ids": ["YI-TIME-001"],
            },
            {
                "sequence": 2,
                "operation": "derive_time_hexagrams",
                "inputs": {"upper_source": upper_source, "lower_source": lower_source},
                "output": {"upper_trigram": upper_index, "lower_trigram": lower_index, "moving_line": moving_line},
                "rule_ids": ["YI-TIME-001", "YI-RELATION-001"],
            },
        ],
        "evidence": [],
        "judgements": [],
        "warnings": ["周易自动排盘采用农历时间取数工程基线；该起卦法及事项断语尚待专家签署。"],
    }


def auto_cast(cast_nonce, local_datetime, timezone, longitude=None, use_true_solar_time=False):
    calendar = calendar_analysis(local_datetime, timezone, longitude, use_true_solar_time)
    line_values, coin_rounds = derive_coin_lines("zhouyi-auto-coins-v1", cast_nonce)
    result = manual_cast(line_values)
    result["engine_version"] = ENGINE_VERSION
    result["rule_version"] = RULE_VERSION
    result["facts"].update({
        "method": "personalized_three_coin",
        "cast_nonce_hash": nonce_hash(cast_nonce),
        "coin_rounds": coin_rounds,
        "calendar": {"pillars": calendar["pillars"], "effective_local_datetime": calendar["time"]["effective_local_datetime"]},
    })
    result["steps"] = [
        {
            "sequence": 1, "operation": "derive_personalized_three_coin_lines",
            "inputs": {"cast_nonce_hash": nonce_hash(cast_nonce), "domain": "zhouyi-auto-coins-v1"},
            "output": {"coin_rounds": coin_rounds, "line_values": line_values},
            "rule_ids": ["YI-AUTO-COIN-001"],
        },
        {
            "sequence": 2, "operation": "derive_related_hexagrams",
            "inputs": {"line_values": line_values},
            "output": {"original": result["facts"]["original"]["ordinal"], "changed": result["facts"]["changed"]["ordinal"], "moving_lines": result["facts"]["moving_lines"]},
            "rule_ids": ["YI-MANUAL-001", "YI-RELATION-001"],
        },
    ]
    result["warnings"] = ["个体自动排盘采用可复算三枚铜钱工程法；自然撞卦仍可能发生，事项断语尚待专家签署。"]
    return result
