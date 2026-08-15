from .constants import (
    HEXAGRAM_NAMES,
    KING_WEN_MATRIX,
    TRIGRAM_BY_LINES,
    TRIGRAMS,
    moving_line_number,
    trigram_number,
)


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
