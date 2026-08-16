from dataclasses import asdict

from app.common.serialization import derive_hexagram_facts, trigram_to_dict
from app.common.trigrams import trigram_to_bits
from app.core.iching import auto_cast, manual_cast, number_cast, time_cast

from .config import DEFAULT_MAPPING_VERSION, get_mapping
from .models import ThreeNumberInput


THREE_NUMBER_ENGINE_VERSION = "zhouyi-three-number-engine-1.0.0"
THREE_NUMBER_RULE_VERSION = "zhouyi-three-number-v1.0.0"


def _moving_line(source_number):
    remainder = source_number % 6
    return 6 if remainder == 0 else remainder


def three_number_cast(number1, number2, number3, mapping_version=DEFAULT_MAPPING_VERSION):
    request = ThreeNumberInput(number1, number2, number3, mapping_version)
    mapping = get_mapping(request.mapping_version)
    upper_remainder, upper = mapping.resolve(request.number1)
    lower_remainder, lower = mapping.resolve(request.number2)
    moving_remainder = request.number3 % 6
    moving_line = _moving_line(request.number3)
    lines = trigram_to_bits(lower) + trigram_to_bits(upper)
    hexagrams = derive_hexagram_facts(lines, [moving_line])
    calculation_trace = [
        "{} % 8 = {} -> normalize {} -> upper trigram {}".format(
            request.number1, request.number1 % 8, upper_remainder, upper.name,
        ),
        "{} % 8 = {} -> normalize {} -> lower trigram {}".format(
            request.number2, request.number2 % 8, lower_remainder, lower.name,
        ),
        "{} % 6 = {} -> normalize {} -> moving line {}".format(
            request.number3, moving_remainder, moving_line, moving_line,
        ),
        "combine lower {} and upper {} -> {}".format(lower.name, upper.name, hexagrams["original"]["name"]),
        "change line {} -> {}".format(moving_line, hexagrams["changed"]["name"]),
    ]
    facts = {
        "method": "three_numbers",
        "input_numbers": {
            "number1_upper": request.number1,
            "number2_lower": request.number2,
            "number3_moving": request.number3,
        },
        "mapping": {"version": mapping.version, "label": mapping.label},
        "upper_source_index": upper_remainder,
        "lower_source_index": lower_remainder,
        "upper_trigram_number": upper.number,
        "lower_trigram_number": lower.number,
        "upper_trigram": trigram_to_dict(upper),
        "lower_trigram": trigram_to_dict(lower),
        "moving_line": moving_line,
        **hexagrams,
    }
    return {
        "schema_version": "2.0",
        "system": "zhouyi",
        "school": "three-number-engineering-baseline",
        "engine_version": THREE_NUMBER_ENGINE_VERSION,
        "algorithm_version": THREE_NUMBER_ENGINE_VERSION,
        "rule_version": THREE_NUMBER_RULE_VERSION,
        "input": asdict(request),
        "normalized_input": {
            "numbers": list(request.numbers),
            "roles": ["upper_trigram", "lower_trigram", "moving_line"],
            "mapping_version": mapping.version,
        },
        "facts": facts,
        "calculation_trace": calculation_trace,
        "steps": [
            {
                "sequence": 1, "operation": "validate_three_number_input",
                "inputs": {"numbers": list(request.numbers), "mapping_version": request.mapping_version},
                "output": {"roles": ["upper_trigram", "lower_trigram", "moving_line"]},
                "rule_ids": ["YI-3NUM-INPUT-001"],
            },
            {
                "sequence": 2, "operation": "map_upper_trigram",
                "inputs": {"number1": request.number1, "divisor": 8},
                "output": {
                    "raw_remainder": request.number1 % 8, "normalized": upper_remainder,
                    "trigram_number": upper.number, "trigram": upper.name,
                },
                "rule_ids": ["YI-3NUM-MAPPING-001"],
            },
            {
                "sequence": 3, "operation": "map_lower_trigram",
                "inputs": {"number2": request.number2, "divisor": 8},
                "output": {
                    "raw_remainder": request.number2 % 8, "normalized": lower_remainder,
                    "trigram_number": lower.number, "trigram": lower.name,
                },
                "rule_ids": ["YI-3NUM-MAPPING-001"],
            },
            {
                "sequence": 4, "operation": "derive_moving_line",
                "inputs": {"number3": request.number3, "divisor": 6},
                "output": {"raw_remainder": moving_remainder, "moving_line": moving_line},
                "rule_ids": ["YI-3NUM-MOVING-001"],
            },
            {
                "sequence": 5, "operation": "derive_hexagram_change",
                "inputs": {"binary_lines": list(lines), "moving_line": moving_line},
                "output": {
                    "original": hexagrams["original"]["ordinal"],
                    "changed": hexagrams["changed"]["ordinal"],
                },
                "rule_ids": ["YI-RELATION-001"],
            },
        ],
        "evidence": [],
        "judgements": [],
        "warnings": ["周易三数起卦为待专家签署的版本化工程基线，不生成事项吉凶。"],
    }


__all__ = ("auto_cast", "manual_cast", "number_cast", "three_number_cast", "time_cast")
