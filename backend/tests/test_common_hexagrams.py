import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.common.hexagrams import (
    HEXAGRAM_CATALOG,
    change_hexagram,
    get_hexagram_by_lines,
    get_hexagram_by_ordinal,
    hexagram_to_bits,
)
from app.common.models import Line, LinePolarity
from app.common.trigrams import (
    TRIGRAM_CATALOG,
    get_trigram_by_bits,
    get_trigram_by_number,
    trigram_to_bits,
)


EXPECTED_TRIGRAMS = (
    (1, "乾", (1, 1, 1)),
    (2, "兑", (1, 1, 0)),
    (3, "离", (1, 0, 1)),
    (4, "震", (1, 0, 0)),
    (5, "巽", (0, 1, 1)),
    (6, "坎", (0, 1, 0)),
    (7, "艮", (0, 0, 1)),
    (8, "坤", (0, 0, 0)),
)


@pytest.mark.parametrize("number,name,bits", EXPECTED_TRIGRAMS)
def test_all_trigram_number_and_binary_mappings(number, name, bits):
    trigram = get_trigram_by_number(number)
    assert trigram.name == name
    assert trigram_to_bits(trigram) == bits
    assert get_trigram_by_bits(bits) == trigram


def test_line_model_is_immutable_and_changes_polarity():
    yin = Line.from_bit(0)
    assert yin.polarity is LinePolarity.YIN
    assert yin.changed().polarity is LinePolarity.YANG
    with pytest.raises(Exception):
        yin.polarity = LinePolarity.YANG


@pytest.mark.parametrize("invalid", (-1, 2, "1", None, True, False))
def test_line_rejects_non_binary_values(invalid):
    with pytest.raises(ValueError):
        Line.from_bit(invalid)


def test_catalogs_are_complete_and_unique():
    assert len(TRIGRAM_CATALOG) == 8
    assert len({trigram_to_bits(item) for item in TRIGRAM_CATALOG}) == 8
    assert len(HEXAGRAM_CATALOG) == 64
    assert {item.ordinal for item in HEXAGRAM_CATALOG} == set(range(1, 65))
    assert len({hexagram_to_bits(item) for item in HEXAGRAM_CATALOG}) == 64


@pytest.mark.parametrize("ordinal", range(1, 65))
def test_every_hexagram_round_trips_between_ordinal_and_lines(ordinal):
    hexagram = get_hexagram_by_ordinal(ordinal)
    bits = hexagram_to_bits(hexagram)
    assert get_hexagram_by_lines(bits) == hexagram
    assert tuple(line.bit for line in hexagram.lines) == bits


@pytest.mark.parametrize(
    "invalid",
    ((), (1, 1, 1), (1, 1, 1, 1, 1, 2), (1, 1, 1, 1, 1, "0")),
)
def test_hexagram_rejects_invalid_binary_lines(invalid):
    with pytest.raises(ValueError):
        get_hexagram_by_lines(invalid)


def test_change_hexagram_uses_bottom_to_top_line_positions():
    qian = (1, 1, 1, 1, 1, 1)
    first_line = change_hexagram(qian, [1])
    top_line = change_hexagram(qian, [6])
    assert first_line.changed_bits == (0, 1, 1, 1, 1, 1)
    assert top_line.changed_bits == (1, 1, 1, 1, 1, 0)
    assert first_line.changed.name == "姤"
    assert top_line.changed.name == "夬"


def test_change_hexagram_deduplicates_and_sorts_moving_lines():
    result = change_hexagram((0, 0, 0, 0, 0, 0), [6, 1, 6])
    assert result.moving_lines == (1, 6)
    assert result.changed_bits == (1, 0, 0, 0, 0, 1)


@pytest.mark.parametrize("moving_lines", ([0], [7], [1, "2"], [True]))
def test_change_hexagram_rejects_invalid_positions(moving_lines):
    with pytest.raises(ValueError):
        change_hexagram((1, 1, 1, 1, 1, 1), moving_lines)


def test_fixed_acceptance_cui_top_line_changes_to_pi_with_trace():
    cui = get_hexagram_by_ordinal(45)
    assert cui.name == "萃"
    assert cui.lower_trigram.name == "坤"
    assert cui.upper_trigram.name == "兑"

    result = change_hexagram(hexagram_to_bits(cui), [6])

    assert result.original.name == "萃"
    assert result.moving_lines == (6,)
    assert result.changed.name == "否"
    assert result.changed.ordinal == 12
    assert result.calculation_trace == (
        "normalize lines bottom-to-top: [0, 0, 0, 1, 1, 0]",
        "change moving line positions: [6]",
        "changed lines bottom-to-top: [0, 0, 0, 1, 1, 1]",
        "King Wen mapping: 萃 -> 否",
    )
