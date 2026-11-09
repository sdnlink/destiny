from app.calendar import calendar_analysis
from app.common.casting import derive_integer, nonce_hash
from app.common.five_elements import (
    element_relation,
)
from app.common.serialization import derive_hexagram_facts
from app.common.trigrams import get_trigram_by_number, trigram_to_bits

from .models import ThreeNumberInput, TwoNumberInput


ENGINE_VERSION = "meihua-engine-2.0.0"
RULE_VERSION = "meihua-mvp-baseline-1.0.0"
THREE_NUMBER_RULE_VERSION = "meihua-three-number-v1.0.0"


def trigram_number(value):
    if type(value) is not int:
        raise ValueError("trigram source must be an integer")
    remainder = value % 8
    return 8 if remainder == 0 else remainder


def moving_line_number(value):
    if type(value) is not int:
        raise ValueError("moving-line source must be an integer")
    remainder = value % 6
    return 6 if remainder == 0 else remainder


def five_element_relation(body_element, use_element):
    """体用五行关系，统一实现见 app.common.five_elements.element_relation。"""
    return element_relation(body_element, use_element)


def _cast_from_sources(
    upper_source, lower_source, moving_source, input_payload, input_facts, steps,
    calculation_trace, rule_version=RULE_VERSION,
):
    upper_number = trigram_number(upper_source)
    lower_number = trigram_number(lower_source)
    moving_line = moving_line_number(moving_source)
    upper = get_trigram_by_number(upper_number)
    lower = get_trigram_by_number(lower_number)
    lines = trigram_to_bits(lower) + trigram_to_bits(upper)
    hexagrams = derive_hexagram_facts(lines, [moving_line])

    use_position = "lower" if moving_line <= 3 else "upper"
    body_position = "upper" if use_position == "lower" else "lower"
    body_trigram = hexagrams["original"]["{}_trigram".format(body_position)]
    use_trigram = hexagrams["original"]["{}_trigram".format(use_position)]
    changed_use_trigram = hexagrams["changed"]["{}_trigram".format(use_position)]
    original_relation = five_element_relation(body_trigram["element"], use_trigram["element"])
    changed_relation = five_element_relation(body_trigram["element"], changed_use_trigram["element"])
    body_use = {
        "body_position": body_position,
        "use_position": use_position,
        "body_trigram": body_trigram,
        "use_trigram": use_trigram,
        "changed_use_trigram": changed_use_trigram,
    }

    return {
        "schema_version": "2.0",
        "system": "meihua",
        "school": "mvp-engineering-baseline",
        "engine_version": ENGINE_VERSION,
        "algorithm_version": ENGINE_VERSION,
        "rule_version": rule_version,
        "input": input_payload,
        "normalized_input": {
            "upper_source": upper_source,
            "lower_source": lower_source,
            "moving_source": moving_source,
        },
        "facts": {
            **input_facts,
            "upper_trigram_number": upper_number,
            "lower_trigram_number": lower_number,
            "upper_trigram": hexagrams["original"]["upper_trigram"],
            "lower_trigram": hexagrams["original"]["lower_trigram"],
            "moving_line": moving_line,
            **hexagrams,
            "body_use": body_use,
            "body_use_relation": {"original": original_relation, "changed": changed_relation},
        },
        "calculation_trace": calculation_trace + [
            "combine lower {} and upper {} -> {}".format(lower.name, upper.name, hexagrams["original"]["name"]),
            "moving line {} sets {} as use and {} as body".format(moving_line, use_position, body_position),
            "change line {} -> {}".format(moving_line, hexagrams["changed"]["name"]),
        ],
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
                "stage": "original", "body_element": body_trigram["element"],
                "use_element": use_trigram["element"], **original_relation,
                "rule_ids": ["MH-FIVE-ELEMENT-001"],
            },
            {
                "evidence_id": "MH-EVIDENCE-BODY-USE-CHANGED",
                "stage": "changed", "body_element": body_trigram["element"],
                "use_element": changed_use_trigram["element"], **changed_relation,
                "rule_ids": ["MH-FIVE-ELEMENT-001"],
            },
        ],
        "judgements": [],
        "warnings": ["旺衰、应期和事项断语尚未经过专家签署，本结果只包含起卦与体用关系事实。"],
    }


def number_cast(upper_number, lower_number):
    request = TwoNumberInput(upper_number, lower_number)
    moving_source = request.upper_number + request.lower_number
    return _cast_from_sources(
        request.upper_number,
        request.lower_number,
        moving_source,
        {"upper_number": request.upper_number, "lower_number": request.lower_number},
        {"method": "two_numbers", "input_numbers": {"upper": request.upper_number, "lower": request.lower_number}},
        [{
            "sequence": 1,
            "operation": "two_numbers_to_trigrams_and_moving_line",
            "inputs": {"upper": request.upper_number, "lower": request.lower_number},
            "output": {
                "upper_remainder": trigram_number(request.upper_number),
                "lower_remainder": trigram_number(request.lower_number),
                "moving_source": moving_source,
                "moving_line": moving_line_number(moving_source),
            },
            "rule_ids": ["MH-NUMBER-001"],
        }],
        [
            "{} % 8 -> upper trigram index {}".format(request.upper_number, trigram_number(request.upper_number)),
            "{} % 8 -> lower trigram index {}".format(request.lower_number, trigram_number(request.lower_number)),
            "({} + {}) % 6 -> moving line {}".format(
                request.upper_number, request.lower_number, moving_line_number(moving_source),
            ),
        ],
    )


def three_number_cast(upper_number, lower_number, moving_number):
    request = ThreeNumberInput(upper_number, lower_number, moving_number)
    return _cast_from_sources(
        request.upper_number,
        request.lower_number,
        request.moving_number,
        {
            "upper_number": request.upper_number,
            "lower_number": request.lower_number,
            "moving_number": request.moving_number,
        },
        {
            "method": "three_numbers",
            "input_numbers": {
                "upper": request.upper_number,
                "lower": request.lower_number,
                "moving": request.moving_number,
            },
        },
        [{
            "sequence": 1,
            "operation": "three_numbers_to_trigrams_and_moving_line",
            "inputs": {
                "upper": request.upper_number,
                "lower": request.lower_number,
                "moving": request.moving_number,
            },
            "output": {
                "upper_remainder": trigram_number(request.upper_number),
                "lower_remainder": trigram_number(request.lower_number),
                "moving_line": moving_line_number(request.moving_number),
            },
            "rule_ids": ["MH-THREE-NUMBER-001"],
        }],
        [
            "{} % 8 -> upper trigram index {}".format(request.upper_number, trigram_number(request.upper_number)),
            "{} % 8 -> lower trigram index {}".format(request.lower_number, trigram_number(request.lower_number)),
            "{} % 6 -> moving line {}".format(request.moving_number, moving_line_number(request.moving_number)),
        ],
        rule_version=THREE_NUMBER_RULE_VERSION,
    )


def time_cast(local_datetime, timezone, longitude=None, use_true_solar_time=False):
    calendar = calendar_analysis(local_datetime, timezone, longitude, use_true_solar_time)
    year_number = calendar["year_branch"]["number"]
    lunar_month = calendar["lunar"]["month"]
    lunar_day = calendar["lunar"]["day"]
    hour_number = calendar["time_branch"]["number"]
    upper_source = year_number + lunar_month + lunar_day
    lower_source = upper_source + hour_number
    result = _cast_from_sources(
        upper_source,
        lower_source,
        lower_source,
        {
            "local_datetime": local_datetime, "timezone": timezone, "longitude": longitude,
            "use_true_solar_time": use_true_solar_time,
        },
        {
            "method": "lunar_time", "calendar": calendar,
            "source_numbers": {
                "year_branch": year_number, "lunar_month": lunar_month, "lunar_day": lunar_day,
                "hour_branch": hour_number, "upper_sum": upper_source, "lower_sum": lower_source,
            },
        },
        [
            {
                "sequence": 1, "operation": "normalize_calendar_input",
                "inputs": {"local_datetime": local_datetime, "timezone": timezone, "longitude": longitude,
                           "use_true_solar_time": use_true_solar_time},
                "output": {
                    "effective_local_datetime": calendar["time"]["effective_local_datetime"],
                    "lunar": calendar["lunar"], "year_branch": calendar["year_branch"],
                    "time_branch": calendar["time_branch"],
                },
                "rule_ids": ["CAL-NORMALIZE-001", "MH-TIME-001"],
            },
            {
                "sequence": 2, "operation": "lunar_time_to_trigrams_and_moving_line",
                "inputs": {"year_branch": year_number, "lunar_month": lunar_month,
                           "lunar_day": lunar_day, "hour_branch": hour_number},
                "output": {
                    "upper_sum": upper_source, "lower_sum": lower_source,
                    "upper_trigram": trigram_number(upper_source),
                    "lower_trigram": trigram_number(lower_source),
                    "moving_line": moving_line_number(lower_source),
                },
                "rule_ids": ["MH-TIME-001"],
            },
        ],
        [
            "year branch {} + lunar month {} + lunar day {} = upper source {}".format(
                year_number, lunar_month, lunar_day, upper_source,
            ),
            "upper source {} + hour branch {} = lower and moving source {}".format(
                upper_source, hour_number, lower_source,
            ),
        ],
    )
    if calendar["lunar"]["is_leap_month"]:
        result["warnings"].append("当前日期位于闰月，工程基线按月份绝对值取数。")
    lunar_year_branch_number = ((calendar["lunar"]["year"] - 4) % 12) + 1
    if lunar_year_branch_number != year_number:
        result["warnings"].append(
            "年支取立春年柱（{}），农历年为 {}（对应年支编号 {}）；"
            "梅花年支存在立春/春节两种口径，本盘按立春口径取数，未混算。".format(
                calendar["year_branch"]["name"], calendar["lunar"]["year"], lunar_year_branch_number,
            )
        )
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
    result = _cast_from_sources(
        upper_source,
        lower_source,
        lower_source,
        {
            "cast_nonce_hash": nonce_hash(cast_nonce), "local_datetime": local_datetime,
            "timezone": timezone, "longitude": longitude, "use_true_solar_time": use_true_solar_time,
        },
        {
            "method": "personalized_lunar_time", "cast_nonce_hash": nonce_hash(cast_nonce),
            "personal_number": personal_number, "calendar": calendar,
            "source_numbers": {
                "year_branch": year_number, "lunar_month": lunar_month, "lunar_day": lunar_day,
                "personal_number": personal_number, "hour_branch": hour_number,
                "upper_sum": upper_source, "lower_sum": lower_source,
            },
        },
        [{
            "sequence": 1, "operation": "personalize_lunar_time_numbers",
            "inputs": {"cast_nonce_hash": nonce_hash(cast_nonce), "domain": "meihua-personal-number-v1"},
            "output": {"personal_number": personal_number, "upper_sum": upper_source,
                       "lower_sum": lower_source, "moving_line": moving_line_number(lower_source)},
            "rule_ids": ["MH-AUTO-PERSONAL-001"],
        }],
        [
            "derive personal number {} from replayable credential".format(personal_number),
            "year/month/day plus personal number -> upper source {}".format(upper_source),
            "upper source plus hour branch -> lower and moving source {}".format(lower_source),
        ],
    )
    if calendar["lunar"]["is_leap_month"]:
        result["warnings"].append("当前日期位于闰月，工程基线按月份绝对值取数。")
    return result


__all__ = ("auto_cast", "five_element_relation", "number_cast", "three_number_cast", "time_cast")
