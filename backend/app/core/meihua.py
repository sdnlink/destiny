from app.common.serialization import derive_hexagram_facts
from app.calendar import calendar_analysis

from .constants import (
    FIVE_ELEMENTS_CONTROLS,
    FIVE_ELEMENTS_GENERATES,
    TRIGRAMS,
    moving_line_number,
    trigram_number,
)
from .casting import derive_integer, nonce_hash


ENGINE_VERSION = "meihua-engine-1.0.0"
RULE_VERSION = "meihua-mvp-baseline-1.0.0"


def five_element_relation(body_element, use_element):
    if body_element == use_element:
        return {"code": "same_element", "label": "体用比和"}
    if FIVE_ELEMENTS_GENERATES[use_element] == body_element:
        return {"code": "use_generates_body", "label": "用生体"}
    if FIVE_ELEMENTS_GENERATES[body_element] == use_element:
        return {"code": "body_generates_use", "label": "体生用"}
    if FIVE_ELEMENTS_CONTROLS[use_element] == body_element:
        return {"code": "use_controls_body", "label": "用克体"}
    if FIVE_ELEMENTS_CONTROLS[body_element] == use_element:
        return {"code": "body_controls_use", "label": "体克用"}
    raise ValueError("unknown five-element relationship")


def _cast_from_numbers(upper_source, lower_source, moving_source, input_facts, steps):
    upper_number = trigram_number(upper_source)
    lower_number = trigram_number(lower_source)
    moving_line = moving_line_number(moving_source)
    upper = TRIGRAMS[upper_number]
    lower = TRIGRAMS[lower_number]
    lines = lower["lines"] + upper["lines"]
    hexagrams = derive_hexagram_facts(lines, [moving_line])

    use_position = "lower" if moving_line <= 3 else "upper"
    body_position = "upper" if use_position == "lower" else "lower"
    body_trigram = hexagrams["original"][f"{body_position}_trigram"]
    use_trigram = hexagrams["original"][f"{use_position}_trigram"]
    changed_use_trigram = hexagrams["changed"][f"{use_position}_trigram"]
    original_relation = five_element_relation(body_trigram["element"], use_trigram["element"])
    changed_relation = five_element_relation(body_trigram["element"], changed_use_trigram["element"])

    return {
        "schema_version": "1.0",
        "system": "meihua",
        "school": "mvp-engineering-baseline",
        "engine_version": ENGINE_VERSION,
        "rule_version": RULE_VERSION,
        "facts": {
            **input_facts,
            "upper_trigram_number": upper_number,
            "lower_trigram_number": lower_number,
            "moving_line": moving_line,
            **hexagrams,
            "body_use": {
                "body_position": body_position,
                "use_position": use_position,
                "body_trigram": body_trigram,
                "use_trigram": use_trigram,
                "changed_use_trigram": changed_use_trigram,
            },
        },
        "steps": steps + [
            {
                "sequence": len(steps) + 1,
                "operation": "derive_body_and_use",
                "inputs": {"moving_line": moving_line},
                "output": {"body_position": body_position, "use_position": use_position},
                "rule_ids": ["MH-BODYUSE-001"],
            }
        ],
        "evidence": [
            {
                "evidence_id": "MH-EVIDENCE-BODY-USE-ORIGINAL",
                "stage": "original",
                "body_element": body_trigram["element"],
                "use_element": use_trigram["element"],
                **original_relation,
                "rule_ids": ["MH-FIVE-ELEMENT-001"],
            },
            {
                "evidence_id": "MH-EVIDENCE-BODY-USE-CHANGED",
                "stage": "changed",
                "body_element": body_trigram["element"],
                "use_element": changed_use_trigram["element"],
                **changed_relation,
                "rule_ids": ["MH-FIVE-ELEMENT-001"],
            },
        ],
        "judgements": [],
        "warnings": ["旺衰、应期和事项断语尚未经过专家签署，本结果只包含起卦与体用关系事实。"],
    }


def number_cast(upper_number, lower_number):
    upper_source = int(upper_number)
    lower_source = int(lower_number)
    moving_source = upper_source + lower_source
    return _cast_from_numbers(
        upper_source,
        lower_source,
        moving_source,
        {"method": "two_numbers", "input_numbers": {"upper": upper_source, "lower": lower_source}},
        [
            {
                "sequence": 1,
                "operation": "numbers_to_trigrams_and_moving_line",
                "inputs": {"upper": upper_source, "lower": lower_source},
                "output": {
                    "upper_remainder": trigram_number(upper_source),
                    "lower_remainder": trigram_number(lower_source),
                    "moving_line": moving_line_number(moving_source),
                },
                "rule_ids": ["MH-NUMBER-001"],
            }
        ],
    )


def time_cast(local_datetime, timezone, longitude=None, use_true_solar_time=False):
    calendar = calendar_analysis(local_datetime, timezone, longitude, use_true_solar_time)
    year_number = calendar["year_branch"]["number"]
    lunar_month = calendar["lunar"]["month"]
    lunar_day = calendar["lunar"]["day"]
    hour_number = calendar["time_branch"]["number"]
    upper_source = year_number + lunar_month + lunar_day
    lower_source = upper_source + hour_number
    result = _cast_from_numbers(
        upper_source,
        lower_source,
        lower_source,
        {
            "method": "lunar_time",
            "calendar": calendar,
            "source_numbers": {
                "year_branch": year_number,
                "lunar_month": lunar_month,
                "lunar_day": lunar_day,
                "hour_branch": hour_number,
                "upper_sum": upper_source,
                "lower_sum": lower_source,
            },
        },
        [
            {
                "sequence": 1,
                "operation": "normalize_calendar_input",
                "inputs": {
                    "local_datetime": local_datetime,
                    "timezone": timezone,
                    "longitude": longitude,
                    "use_true_solar_time": use_true_solar_time,
                },
                "output": {
                    "effective_local_datetime": calendar["time"]["effective_local_datetime"],
                    "lunar": calendar["lunar"],
                    "year_branch": calendar["year_branch"],
                    "time_branch": calendar["time_branch"],
                },
                "rule_ids": ["CAL-NORMALIZE-001", "MH-TIME-001"],
            },
            {
                "sequence": 2,
                "operation": "lunar_time_to_trigrams_and_moving_line",
                "inputs": {
                    "year_branch": year_number,
                    "lunar_month": lunar_month,
                    "lunar_day": lunar_day,
                    "hour_branch": hour_number,
                },
                "output": {
                    "upper_sum": upper_source,
                    "lower_sum": lower_source,
                    "upper_trigram": trigram_number(upper_source),
                    "lower_trigram": trigram_number(lower_source),
                    "moving_line": moving_line_number(lower_source),
                },
                "rule_ids": ["MH-TIME-001"],
            },
        ],
    )
    if calendar["lunar"]["is_leap_month"]:
        result["warnings"].append("当前日期位于闰月，MVP基线按月份绝对值取数。")
    return result


def auto_cast(cast_nonce, local_datetime, timezone, longitude=None, use_true_solar_time=False):
    calendar = calendar_analysis(local_datetime, timezone, longitude, use_true_solar_time)
    year_number = calendar["year_branch"]["number"]
    lunar_month = calendar["lunar"]["month"]
    lunar_day = calendar["lunar"]["day"]
    hour_number = calendar["time_branch"]["number"]
    personal_number = derive_integer("meihua-personal-number-v1", cast_nonce, 1, 1, 64)
    upper_source = year_number + lunar_month + lunar_day + personal_number
    lower_source = upper_source + hour_number
    return _cast_from_numbers(
        upper_source,
        lower_source,
        lower_source,
        {
            "method": "personalized_lunar_time",
            "cast_nonce_hash": nonce_hash(cast_nonce),
            "personal_number": personal_number,
            "calendar": calendar,
            "source_numbers": {
                "year_branch": year_number, "lunar_month": lunar_month, "lunar_day": lunar_day,
                "personal_number": personal_number, "hour_branch": hour_number,
                "upper_sum": upper_source, "lower_sum": lower_source,
            },
        },
        [{
            "sequence": 1, "operation": "personalize_lunar_time_numbers",
            "inputs": {"cast_nonce_hash": nonce_hash(cast_nonce), "domain": "meihua-personal-number-v1"},
            "output": {"personal_number": personal_number, "upper_sum": upper_source, "lower_sum": lower_source, "moving_line": moving_line_number(lower_source)},
            "rule_ids": ["MH-AUTO-PERSONAL-001"],
        }],
    )
