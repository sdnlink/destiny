from dataclasses import FrozenInstanceError
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.zhouyi import three_number_cast
from app.zhouyi.config.hexagram_mapping import MAPPINGS, get_mapping
from app.zhouyi.models import ThreeNumberInput


EXPECTED_MAPPING = (
    (1, "乾"), (2, "兑"), (3, "离"), (4, "震"),
    (5, "巽"), (6, "坎"), (7, "艮"), (8, "坤"),
)


@pytest.mark.parametrize("number,name", EXPECTED_MAPPING)
def test_versioned_mapping_contains_all_eight_trigrams(number, name):
    normalized, trigram = get_mapping().resolve(number)
    assert normalized == number
    assert trigram.number == number
    assert trigram.name == name


def test_mapping_configuration_and_input_are_immutable():
    request = ThreeNumberInput(23, 47, 5)
    with pytest.raises(FrozenInstanceError):
        request.number1 = 1
    with pytest.raises(TypeError):
        MAPPINGS["replacement"] = get_mapping()


def test_three_numbers_have_independent_upper_lower_and_moving_roles():
    result = three_number_cast(23, 47, 5)
    facts = result["facts"]
    assert facts["method"] == "three_numbers"
    assert facts["upper_trigram"]["name"] == "艮"
    assert facts["lower_trigram"]["name"] == "艮"
    assert facts["original"]["name"] == "艮"
    assert facts["moving_line"] == 5
    assert facts["changed"]["name"] == "渐"
    assert result["normalized_input"]["roles"] == ["upper_trigram", "lower_trigram", "moving_line"]


def test_known_qian_over_kan_example_changes_third_line():
    result = three_number_cast(25, 38, 3)
    facts = result["facts"]
    assert (facts["upper_trigram"]["name"], facts["lower_trigram"]["name"]) == ("乾", "坎")
    assert (facts["original"]["ordinal"], facts["original"]["name"]) == (6, "讼")
    assert (facts["changed"]["ordinal"], facts["changed"]["name"]) == (44, "姤")


def test_zero_remainders_normalize_to_kun_and_top_line():
    result = three_number_cast(0, 0, 0)
    facts = result["facts"]
    assert facts["upper_source_index"] == facts["lower_source_index"] == 8
    assert facts["upper_trigram"]["name"] == facts["lower_trigram"]["name"] == "坤"
    assert facts["moving_line"] == 6
    assert facts["original"]["name"] == "坤"
    assert facts["changed"]["name"] == "剥"
    assert result["calculation_trace"][:3] == [
        "0 % 8 = 0 -> normalize 8 -> upper trigram 坤",
        "0 % 8 = 0 -> normalize 8 -> lower trigram 坤",
        "0 % 6 = 0 -> normalize 6 -> moving line 6",
    ]


def test_same_input_and_version_are_fully_replayable():
    assert three_number_cast(1025, 2048, 36) == three_number_cast(1025, 2048, 36)


@pytest.mark.parametrize(
    "values",
    ((-1, 2, 3), (1, -2, 3), (1, 2, -3), (True, 2, 3), (1.0, 2, 3), (1, "2", 3)),
)
def test_invalid_or_negative_numbers_are_rejected(values):
    with pytest.raises(ValueError):
        three_number_cast(*values)


def test_unknown_mapping_version_is_rejected_explicitly():
    with pytest.raises(ValueError, match="unsupported trigram mapping version"):
        three_number_cast(1, 2, 3, mapping_version="unpublished-school-v2")


def test_trace_and_steps_are_complete_and_versioned():
    result = three_number_cast(23, 47, 5)
    assert result["algorithm_version"] == "zhouyi-three-number-engine-1.0.0"
    assert result["rule_version"] == "zhouyi-three-number-v1.0.0"
    assert result["facts"]["mapping"]["version"] == "earlier-heaven-number-v1"
    assert len(result["calculation_trace"]) == 5
    assert [step["sequence"] for step in result["steps"]] == [1, 2, 3, 4, 5]
    assert result["judgements"] == []
