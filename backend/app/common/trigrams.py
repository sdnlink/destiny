from typing import Iterable, Tuple, cast

from .models import Line, Trigram


def _lines(bits: Iterable[int]) -> Tuple[Line, Line, Line]:
    values = tuple(Line.from_bit(bit) for bit in bits)
    if len(values) != 3:
        raise ValueError("trigram must contain three bits from bottom to top")
    return cast(Tuple[Line, Line, Line], values)


# Immutable Fu Xi binary shapes in the configured Earlier-Heaven number order.
TRIGRAM_CATALOG = (
    Trigram(1, "乾", "☰", _lines((1, 1, 1)), "金", "西北"),
    Trigram(2, "兑", "☱", _lines((1, 1, 0)), "金", "西"),
    Trigram(3, "离", "☲", _lines((1, 0, 1)), "火", "南"),
    Trigram(4, "震", "☳", _lines((1, 0, 0)), "木", "东"),
    Trigram(5, "巽", "☴", _lines((0, 1, 1)), "木", "东南"),
    Trigram(6, "坎", "☵", _lines((0, 1, 0)), "水", "北"),
    Trigram(7, "艮", "☶", _lines((0, 0, 1)), "土", "东北"),
    Trigram(8, "坤", "☷", _lines((0, 0, 0)), "土", "西南"),
)


def trigram_to_bits(trigram: Trigram) -> Tuple[int, int, int]:
    return cast(Tuple[int, int, int], tuple(line.bit for line in trigram.lines))


def get_trigram_by_number(number: int) -> Trigram:
    if type(number) is not int or not 1 <= number <= 8:
        raise ValueError("trigram number must be between 1 and 8")
    return TRIGRAM_CATALOG[number - 1]


def get_trigram_by_bits(bits: Iterable[int]) -> Trigram:
    normalized = tuple(bits)
    if len(normalized) != 3 or any(bit not in (0, 1) for bit in normalized):
        raise ValueError("trigram bits must contain three binary values from bottom to top")
    for trigram in TRIGRAM_CATALOG:
        if trigram_to_bits(trigram) == normalized:
            return trigram
    raise ValueError("unknown trigram bits")
