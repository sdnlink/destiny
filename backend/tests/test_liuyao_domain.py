from dataclasses import FrozenInstanceError
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.liuyao import auto_cast, coin_cast, line_cast
from app.liuyao.models import SixLineInput, ThreeCoinInput
from app.liuyao.rules import PALACE_BY_LINES


CALENDAR = {"local_datetime": "2026-08-15T16:00:00", "timezone": "Asia/Shanghai"}


def test_input_models_are_immutable_and_bottom_to_top():
    lines = SixLineInput((9, 7, 7, 7, 7, 7))
    coins = ThreeCoinInput(((3, 3, 3), (3, 2, 2), (3, 2, 2), (3, 2, 2), (3, 2, 2), (3, 2, 2)))
    assert coins.line_values == lines.lines
    with pytest.raises(FrozenInstanceError):
        lines.lines = (7, 7, 7, 7, 7, 7)


@pytest.mark.parametrize("lines", ((7, 7, 7), (7, 7, 7, 7, 7, 5), (7, 7, 7, 7, 7, True)))
def test_line_input_rejects_wrong_length_value_or_type(lines):
    with pytest.raises(ValueError):
        line_cast(lines, **CALENDAR)


@pytest.mark.parametrize(
    "rounds",
    (
        ((3, 2, 2),) * 5,
        ((3, 2),) * 6,
        ((3, 2, 4),) * 6,
        ((3, 2, True),) * 6,
    ),
)
def test_coin_input_requires_six_rounds_of_three_values_two_or_three(rounds):
    with pytest.raises(ValueError):
        coin_cast(rounds, **CALENDAR)


def test_three_coin_rounds_generate_lines_from_first_to_top():
    rounds = [[3, 3, 3]] + [[3, 2, 2]] * 5
    result = coin_cast(rounds, **CALENDAR)
    facts = result["facts"]
    assert facts["method"] == "three_coins"
    assert facts["input_lines"] == [9, 7, 7, 7, 7, 7]
    assert facts["moving_lines"] == [1]
    assert facts["original"]["name"] == "乾"
    assert facts["changed"]["name"] == "姤"
    assert facts["coin_rounds"][0] == {"line": 1, "coins": [3, 3, 3], "value": 9}


def test_six_line_chart_contains_original_and_changed_line_states():
    facts = line_cast([9, 8, 7, 6, 8, 9], **CALENDAR)["facts"]
    assert facts["moving_lines"] == [1, 4, 6]
    assert [line["line_value"] for line in facts["line_chart"]] == [9, 8, 7, 6, 8, 9]
    assert [line["line_type"] for line in facts["line_chart"]] == ["老阳", "少阴", "少阳", "老阴", "少阴", "老阳"]
    assert facts["line_chart"][0]["changed_yin_yang"] == "阴"
    assert facts["line_chart"][1]["changed_yin_yang"] == "阴"
    assert facts["line_chart"][3]["changed_yin_yang"] == "阳"


def test_chart_includes_palace_host_response_najia_relatives_spirits_and_calendar():
    facts = line_cast([7, 7, 7, 7, 7, 7], **CALENDAR)["facts"]
    assert facts["palace"] == {
        "name": "乾", "element": "金", "stage": "本宫", "host_line": 6, "response_line": 3,
    }
    assert [line["najia_branch"] for line in facts["line_chart"]] == ["子", "寅", "辰", "午", "申", "戌"]
    assert [line["roles"] for line in facts["line_chart"]] == [[], [], ["应"], [], [], ["世"]]
    assert facts["line_chart"][0]["six_relative"] == "子孙"
    assert facts["line_chart"][0]["six_spirit"] == "白虎"
    assert facts["month_branch"]["name"] == "申"
    assert facts["day_pillar"] == "辛酉"
    assert facts["xun"]["empty_branches"] == ["子", "丑"]


def test_all_sixty_four_hexagrams_have_one_eight_palace_assignment():
    assert len(PALACE_BY_LINES) == 64
    assert all(1 <= palace.host_line <= 6 and 1 <= palace.response_line <= 6 for palace in PALACE_BY_LINES.values())


def test_hidden_and_flying_spirits_are_explicitly_not_fabricated():
    coverage = line_cast([7, 8, 7, 8, 7, 8], **CALENDAR)["facts"]["hidden_flying_spirits"]
    assert coverage["status"] == "pending_rule_selection"
    assert coverage["hidden_spirits"] == []
    assert coverage["flying_spirits"] == []


def test_personalized_auto_cast_is_replayable_and_uses_coin_rounds():
    nonce = "person-0000000000000001"
    first = auto_cast(nonce, **CALENDAR)
    second = auto_cast(nonce, **CALENDAR)
    assert first == second
    assert first["facts"]["method"] == "personalized_three_coin"
    assert len(first["facts"]["coin_rounds"]) == 6
    assert nonce not in str(first)


def test_trace_and_rules_are_complete_without_judgements():
    result = coin_cast([[3, 2, 2]] * 6, **CALENDAR)
    assert len(result["calculation_trace"]) == 12
    assert [step["sequence"] for step in result["steps"]] == [1, 2, 3, 4]
    assert result["steps"][0]["rule_ids"] == ["LY-COINS-001", "LY-LINES-001"]
    assert result["judgements"] == []
