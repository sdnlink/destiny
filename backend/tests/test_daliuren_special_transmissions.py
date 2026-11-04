import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.common.ganzhi import EARTHLY_BRANCHES
from app.daliuren.engine import (
    _four_lessons, _lesson, _remote_transmissions, _three_transmissions,
)


STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
SEXAGENARY_CYCLE = [STEMS[index % 10] + BRANCHES[index % 12] for index in range(60)]


def plate(offset):
    return {
        ground: EARTHLY_BRANCHES[(index + offset) % 12]
        for index, ground in enumerate(EARTHLY_BRANCHES)
    }


def transmissions(day_pillar, offset):
    heaven_plate = plate(offset)
    lessons = _four_lessons(day_pillar, heaven_plate)
    return _three_transmissions(day_pillar, heaven_plate, lessons)


def test_shehai_counts_harm_before_returning_home_from_classic_example():
    result = transmissions("丁卯", 10)
    assert result["lesson_type"] == "涉害"
    assert result["transmissions"] == ["亥", "酉", "未"]
    assert [(item["upper"], item["depth"]) for item in result["candidate_depths"]] == [("丑", 1), ("亥", 5)]
    assert [(row["ground"], row["symbol"]) for row in result["candidate_depths"][1]["encounters"]] == [
        ("辰", "辰"), ("巳", "戊"), ("未", "未"), ("未", "己"), ("戌", "戌"),
    ]


def test_shehai_equal_depth_uses_meng_ground_from_classic_example():
    result = transmissions("甲午", 2)
    assert result["lesson_type"] == "涉害"
    assert result["source_path"] == "见机"
    assert result["transmissions"] == ["辰", "午", "申"]
    assert [item["depth"] for item in result["candidate_depths"]] == [1, 1]


@pytest.mark.parametrize(
    "day_pillar,offset,source_path,expected",
    (
        ("丙辰", 1, "刚日干合", ["亥", "午", "午"]),
        ("丁酉", 10, "柔日支前三合", ["丑", "巳", "巳"]),
    ),
)
def test_bieze_uses_stem_combination_or_branch_trine(day_pillar, offset, source_path, expected):
    result = transmissions(day_pillar, offset)
    assert result["lesson_type"] == "别责"
    assert result["source_path"] == source_path
    assert result["transmissions"] == expected


@pytest.mark.parametrize(
    "day_pillar,offset,source_path,expected",
    (
        ("甲寅", 9, "阳日顺数三位", ["丑", "亥", "亥"]),
        ("丁未", 3, "阴日逆数三位", ["亥", "戌", "戌"]),
    ),
)
def test_bazhuan_counts_three_positions_in_day_direction(day_pillar, offset, source_path, expected):
    result = transmissions(day_pillar, offset)
    assert result["lesson_type"] == "八专"
    assert result["source_path"] == source_path
    assert result["transmissions"] == expected


@pytest.mark.parametrize(
    "day_pillar,source_path,expected",
    (
        ("癸丑", "伏吟有克", ["丑", "戌", "未"]),
        ("丙辰", "自任", ["巳", "申", "寅"]),
        ("壬辰", "杜传", ["亥", "辰", "戌"]),
        ("丁卯", "杜传", ["卯", "子", "午"]),
    ),
)
def test_fuyin_uses_control_punishment_and_clash_rules(day_pillar, source_path, expected):
    result = transmissions(day_pillar, 0)
    assert result["lesson_type"] == "伏吟"
    assert result["source_path"] == source_path
    assert result["transmissions"] == expected


@pytest.mark.parametrize(
    "day_pillar,expected",
    (
        ("丁未", ["巳", "丑", "丑"]),
        ("己未", ["巳", "丑", "丑"]),
        ("辛未", ["巳", "丑", "辰"]),
        ("丁丑", ["亥", "未", "丑"]),
        ("己丑", ["亥", "未", "丑"]),
        ("辛丑", ["亥", "未", "辰"]),
    ),
)
def test_fanyin_well_railing_covers_all_six_no_control_days(day_pillar, expected):
    result = transmissions(day_pillar, 6)
    assert result["lesson_type"] == "返吟"
    assert result["source_path"] == "井栏射"
    assert result["transmissions"] == expected


def test_remote_control_with_ambiguous_polarity_falls_back_to_shehai():
    """遥克比用后仍多候选时继续按涉害取深，不再返回 pending。"""
    identity_plate = {branch: branch for branch in EARTHLY_BRANCHES}
    lessons = [
        _lesson(1, "甲", "辰"),
        _lesson(2, "甲", "戌"),
        _lesson(3, "丙", "午"),
        _lesson(4, "丙", "亥"),
    ]
    result = _remote_transmissions(("甲", "子"), identity_plate, lessons)
    assert result["status"] == "completed"
    assert result["lesson_type"] == "涉害"
    assert len(result["transmissions"]) == 3
    assert result["remote_control"]["path"] == "遥克"
    assert result["remote_control"]["source_path"] == "弹射"
    assert result["remote_control"]["candidates"] == ["辰", "戌"]
    assert any("转涉害取深" in line for line in result["trace"])


def test_all_seven_hundred_twenty_day_plate_combinations_finish_deterministically():
    lesson_types = set()
    for day_pillar in SEXAGENARY_CYCLE:
        for offset in range(12):
            result = transmissions(day_pillar, offset)
            assert result["status"] == "completed", (day_pillar, offset, result)
            assert len(result["transmissions"]) == 3
            lesson_types.add(result["lesson_type"])
    assert lesson_types == {"贼克", "克", "比用", "涉害", "遥克", "昴星", "别责", "八专", "伏吟", "返吟"}
