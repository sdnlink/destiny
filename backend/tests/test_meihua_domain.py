from dataclasses import FrozenInstanceError
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.meihua import auto_cast, number_cast, three_number_cast, time_cast
from app.meihua.models import ThreeNumberInput, TwoNumberInput


def test_input_models_are_typed_and_immutable():
    two = TwoNumberInput(25, 38)
    three = ThreeNumberInput(25, 38, 5)
    with pytest.raises(FrozenInstanceError):
        two.upper_number = 1
    with pytest.raises(FrozenInstanceError):
        three.moving_number = 1
    for values in ((True, 2), (1.0, 2), (1, "2")):
        with pytest.raises(ValueError):
            TwoNumberInput(*values)


def test_two_number_method_uses_sum_for_moving_line():
    result = number_cast(1, 2)
    facts = result["facts"]
    assert facts["method"] == "two_numbers"
    assert facts["original"]["name"] == "履"
    assert facts["moving_line"] == 3
    assert result["steps"][0]["rule_ids"] == ["MH-NUMBER-001"]


def test_three_number_method_keeps_all_three_roles_independent():
    result = three_number_cast(25, 38, 5)
    facts = result["facts"]
    assert facts["method"] == "three_numbers"
    assert facts["upper_trigram"]["name"] == "乾"
    assert facts["lower_trigram"]["name"] == "坎"
    assert facts["moving_line"] == 5
    assert facts["original"]["name"] == "讼"
    assert facts["mutual"]["name"] == "家人"
    assert facts["changed"]["name"] == "未济"
    assert result["rule_version"] == "meihua-three-number-v1.0.0"


def test_three_number_moving_value_changes_body_use_without_changing_original():
    lower_moving = three_number_cast(1, 2, 3)["facts"]
    upper_moving = three_number_cast(1, 2, 4)["facts"]
    assert lower_moving["original"] == upper_moving["original"]
    assert lower_moving["body_use"]["use_position"] == "lower"
    assert lower_moving["body_use"]["body_position"] == "upper"
    assert upper_moving["body_use"]["use_position"] == "upper"
    assert upper_moving["body_use"]["body_position"] == "lower"
    assert "host_line" not in lower_moving
    assert "response_line" not in lower_moving


def test_body_use_relations_are_structured_for_original_and_changed_stages():
    relations = three_number_cast(25, 38, 5)["facts"]["body_use_relation"]
    assert relations["original"] == {"code": "use_generates_body", "label": "用生体"}
    assert relations["changed"] == {"code": "body_controls_use", "label": "体克用"}


def test_zero_remainders_map_to_kun_and_top_line():
    facts = three_number_cast(0, 0, 0)["facts"]
    assert facts["upper_trigram_number"] == facts["lower_trigram_number"] == 8
    assert facts["moving_line"] == 6
    assert facts["original"]["name"] == "坤"
    assert facts["changed"]["name"] == "剥"


def test_signed_integer_compatibility_is_deterministic_but_not_coerced():
    first = three_number_cast(-1, -2, -3)
    second = three_number_cast(-1, -2, -3)
    assert first == second
    assert first["facts"]["original"]["name"] == "蒙"
    with pytest.raises(ValueError):
        three_number_cast(1, 2, False)


def test_time_method_keeps_calendar_trace_and_leap_month_warning():
    regular = time_cast("2026-08-15T16:00:00", "Asia/Shanghai")
    leap = time_cast("2023-03-22T12:00:00", "Asia/Shanghai")
    assert regular["facts"]["source_numbers"]["upper_sum"] == 17
    assert len(regular["calculation_trace"]) == 5
    assert leap["facts"]["calendar"]["lunar"]["is_leap_month"] is True
    assert any("闰月" in warning for warning in leap["warnings"])


def test_personalized_auto_method_is_replayable_and_hides_raw_nonce():
    nonce = "person-0000000000000001"
    first = auto_cast(nonce, "2026-08-15T16:00:00", "Asia/Shanghai")
    second = auto_cast(nonce, "2026-08-15T16:00:00", "Asia/Shanghai")
    assert first == second
    assert first["facts"]["method"] == "personalized_lunar_time"
    assert nonce not in str(first)


def test_three_number_trace_and_rule_steps_are_complete():
    result = three_number_cast(25, 38, 5)
    assert len(result["calculation_trace"]) == 6
    assert [step["sequence"] for step in result["steps"]] == [1, 2]
    assert result["steps"][0]["rule_ids"] == ["MH-THREE-NUMBER-001"]
    assert result["steps"][1]["rule_ids"] == ["MH-BODYUSE-001"]
    assert result["judgements"] == []
