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


def test_hidden_spirits_are_derived_from_palace_pure_hexagram():
    facts = line_cast([7, 8, 7, 8, 7, 8], **CALENDAR)["facts"]
    coverage = facts["hidden_flying_spirits"]
    assert coverage["status"] == "completed"
    assert coverage["palace_pure_hexagram"] == facts["palace"]["name"]
    # 本卦已出现的六亲不取伏神，缺失六亲必须逐一补出
    assert set(coverage["missing_relatives"]) == {item["six_relative"] for item in coverage["hidden_spirits"]}
    assert not set(coverage["present_relatives"]) & set(coverage["missing_relatives"])
    for item in coverage["hidden_spirits"]:
        host = facts["line_chart"][item["position"] - 1]
        assert item["flying_spirit"]["position"] == item["position"]
        assert item["flying_spirit"]["six_relative"] == host["six_relative"]
        assert item["flying_spirit"]["najia_branch"] == host["najia_branch"]
        assert item["relation"] in ("飞生伏", "伏生飞", "飞克伏", "伏克飞", "飞伏比和")


def test_pure_hexagram_has_no_missing_relatives():
    from app.liuyao.engine import number_cast

    facts = number_cast(1, 1, **CALENDAR)["facts"]
    coverage = facts["hidden_flying_spirits"]
    assert facts["original"]["name"] == "乾"
    assert coverage["missing_relatives"] == []
    assert coverage["hidden_spirits"] == []
    assert len(coverage["present_relatives"]) == 5


def test_branch_structures_need_all_members_from_pool():
    from app.liuyao.engine import _branch_structures

    # 动爻子、申 + 月建辰 + 日辰子 → 申子辰水局齐备
    result = _branch_structures(["子", "申"], "辰", "子")
    assert len(result["sanhe"]) == 1
    structure = result["sanhe"][0]
    assert structure["element"] == "水"
    assert structure["branches"] == ["申", "子", "辰"]
    sources = {item["branch"]: item["sources"] for item in structure["members"]}
    assert sources["申"] == ["动爻"]
    assert sources["辰"] == ["月建"]
    assert sources["子"] == ["动爻", "日辰"]
    # 池内没有六合对时为空
    assert result["liuhe"] == []

    # 动爻丑 + 月建子 + 日辰午 → 子丑六合，不成三合局
    result2 = _branch_structures(["丑"], "子", "午")
    assert result2["sanhe"] == []
    assert len(result2["liuhe"]) == 1
    pair = result2["liuhe"][0]
    assert pair["branches"] == ["丑", "子"]
    pair_sources = {item["branch"]: item["sources"] for item in pair["members"]}
    assert pair_sources["子"] == ["月建"]
    assert pair_sources["丑"] == ["动爻"]

    # 只有部分成员时不成局
    assert _branch_structures(["子"], "申", "午")["sanhe"] == []


def test_changed_hexagram_gets_najia_and_advance_retreat_flags():
    from app.common.ganzhi import BRANCH_ELEMENTS
    from app.liuyao.engine import ADVANCE_BRANCH, RETREAT_BRANCH, _advance_retreat
    from app.liuyao.rules import NAJIA

    assert _advance_retreat("亥", "子") == "进神"
    assert _advance_retreat("子", "亥") == "退神"
    assert _advance_retreat("子", "丑") == ""
    assert set(RETREAT_BRANCH) == set(ADVANCE_BRANCH.values())

    facts = line_cast([9, 7, 7, 7, 7, 7], **CALENDAR)["facts"]
    changed = facts["changed"]
    lower, upper = NAJIA[changed["lower_trigram"]["name"]], NAJIA[changed["upper_trigram"]["name"]]
    expected_branches = list(lower[2] + upper[3])
    assert [line["najia_branch"] for line in facts["changed_line_chart"]] == expected_branches
    for line, changed_line in zip(facts["line_chart"], facts["changed_line_chart"]):
        assert changed_line["element"] == BRANCH_ELEMENTS[changed_line["najia_branch"]]
        assert line["changed_najia_branch"] == changed_line["najia_branch"]
        if line["is_moving"]:
            assert line["advance_retreat"] == _advance_retreat(line["najia_branch"], changed_line["najia_branch"])
        else:
            assert line["advance_retreat"] == ""


def test_line_month_day_derivations_follow_ganzhi_tables():
    from app.common.ganzhi import BRANCH_CLASH, BRANCH_COMBINE

    facts = line_cast([7, 8, 7, 8, 7, 8], **CALENDAR)["facts"]
    month, day = facts["month_branch"]["name"], facts["day_pillar"][1]
    for line in facts["line_chart"]:
        branch = line["najia_branch"]
        assert line["is_month_break"] == (BRANCH_CLASH[month] == branch)
        assert line["is_day_clash"] == (BRANCH_CLASH[day] == branch)
        assert line["is_day_combine"] == (BRANCH_COMBINE[day] == branch)
        # 静爻受日冲：旺相为暗动、休囚为日破，二者互斥
        if line["is_moving"]:
            assert not line["is_dark_move"] and not line["is_day_break"]
            continue
        if not line["is_day_clash"]:
            assert not line["is_dark_move"] and not line["is_day_break"]
            continue
        assert line["is_dark_move"] != line["is_day_break"]
        assert line["is_dark_move"] == (line["month_strength"] in ("旺", "相"))


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
    # 6 条投币 + 装卦 4 步 + 月破日破 1 步 + 变卦纳甲 1 步 + 合局 1 步 + 伏神 1 步
    # + 出伏条件 1 步 + 刑害 1 步 + 三合成局评估 1 步
    assert len(result["calculation_trace"]) == 19
    assert any("month break" in line for line in result["calculation_trace"])
    assert any("advance or retreat" in line for line in result["calculation_trace"])
    assert any("sanhe" in line for line in result["calculation_trace"])
    assert any("pure hexagram" in line for line in result["calculation_trace"])
    assert any("emerge blockers" in line for line in result["calculation_trace"])
    assert any("punishment/harm" in line for line in result["calculation_trace"])
    assert any("assess sanhe completion" in line for line in result["calculation_trace"])
    assert [step["sequence"] for step in result["steps"]] == [1, 2, 3, 4, 5, 6]
    assert result["steps"][0]["rule_ids"] == ["LY-COINS-001", "LY-LINES-001"]
    assert result["steps"][3]["rule_ids"] == ["LY-HIDDEN-FLYING-001"]
    assert result["steps"][4]["rule_ids"] == ["LY-BRANCHSTRUCT-001"]
    assert result["steps"][5]["rule_ids"] == ["LY-XINGHAI-001", "LY-SANHE-COND-001"]
    assert result["judgements"] == []
