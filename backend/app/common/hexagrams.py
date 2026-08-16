from dataclasses import dataclass
from typing import Iterable, Optional, Tuple, cast

from .models import Hexagram
from .trigrams import TRIGRAM_CATALOG, get_trigram_by_bits, trigram_to_bits


HEXAGRAM_NAMES = tuple(
    "乾 坤 屯 蒙 需 讼 师 比 小畜 履 泰 否 同人 大有 谦 豫 随 蛊 临 观 噬嗑 贲 剥 复 "
    "无妄 大畜 颐 大过 坎 离 咸 恒 遁 大壮 晋 明夷 家人 睽 蹇 解 损 益 夬 姤 萃 升 困 "
    "井 革 鼎 震 艮 渐 归妹 丰 旅 巽 兑 涣 节 中孚 小过 既济 未济".split()
)

# Rows are upper trigrams and columns are lower trigrams, both 乾兑离震巽坎艮坤.
KING_WEN_MATRIX = (
    (1, 10, 13, 25, 44, 6, 33, 12),
    (43, 58, 49, 17, 28, 47, 31, 45),
    (14, 38, 30, 21, 50, 64, 56, 35),
    (34, 54, 55, 51, 32, 40, 62, 16),
    (9, 61, 37, 42, 57, 59, 53, 20),
    (5, 60, 63, 3, 48, 29, 39, 8),
    (26, 41, 22, 27, 18, 4, 52, 23),
    (11, 19, 36, 24, 46, 7, 15, 2),
)


def _build_catalog() -> Tuple[Hexagram, ...]:
    by_ordinal = [None] * 64  # type: list[Optional[Hexagram]]
    for upper_index, row in enumerate(KING_WEN_MATRIX, 1):
        for lower_index, ordinal in enumerate(row, 1):
            by_ordinal[ordinal - 1] = Hexagram(
                ordinal=ordinal,
                name=HEXAGRAM_NAMES[ordinal - 1],
                symbol=chr(0x4DBF + ordinal),
                lower_trigram=TRIGRAM_CATALOG[lower_index - 1],
                upper_trigram=TRIGRAM_CATALOG[upper_index - 1],
            )
    if any(item is None for item in by_ordinal):
        raise RuntimeError("King Wen matrix does not define all 64 hexagrams")
    return cast(Tuple[Hexagram, ...], tuple(by_ordinal))


HEXAGRAM_CATALOG = _build_catalog()


def _normalize_hexagram_bits(bits: Iterable[int]) -> Tuple[int, int, int, int, int, int]:
    normalized = tuple(bits)
    if len(normalized) != 6 or any(bit not in (0, 1) for bit in normalized):
        raise ValueError("hexagram bits must contain six binary values from bottom to top")
    return cast(Tuple[int, int, int, int, int, int], normalized)


def hexagram_to_bits(hexagram: Hexagram) -> Tuple[int, int, int, int, int, int]:
    return trigram_to_bits(hexagram.lower_trigram) + trigram_to_bits(hexagram.upper_trigram)


def get_hexagram_by_ordinal(ordinal: int) -> Hexagram:
    if type(ordinal) is not int or not 1 <= ordinal <= 64:
        raise ValueError("hexagram ordinal must be between 1 and 64")
    return HEXAGRAM_CATALOG[ordinal - 1]


def get_hexagram_by_lines(bits: Iterable[int]) -> Hexagram:
    normalized = _normalize_hexagram_bits(bits)
    lower = get_trigram_by_bits(normalized[:3])
    upper = get_trigram_by_bits(normalized[3:])
    ordinal = KING_WEN_MATRIX[upper.number - 1][lower.number - 1]
    return get_hexagram_by_ordinal(ordinal)


@dataclass(frozen=True)
class ChangeResult:
    original: Hexagram
    changed: Hexagram
    moving_lines: Tuple[int, ...]
    original_bits: Tuple[int, int, int, int, int, int]
    changed_bits: Tuple[int, int, int, int, int, int]
    calculation_trace: Tuple[str, ...]


def change_hexagram(bits: Iterable[int], moving_lines: Iterable[int]) -> ChangeResult:
    original_bits = _normalize_hexagram_bits(bits)
    raw_positions = tuple(moving_lines)
    if any(type(position) is not int or position < 1 or position > 6 for position in raw_positions):
        raise ValueError("moving line positions must be between 1 and 6")
    positions = tuple(sorted(set(raw_positions)))
    moving_set = frozenset(positions)
    changed_bits = tuple(
        1 - bit if position in moving_set else bit
        for position, bit in enumerate(original_bits, 1)
    )
    original = get_hexagram_by_lines(original_bits)
    changed = get_hexagram_by_lines(changed_bits)
    trace = (
        "normalize lines bottom-to-top: {}".format(list(original_bits)),
        "change moving line positions: {}".format(list(positions)),
        "changed lines bottom-to-top: {}".format(list(changed_bits)),
        "King Wen mapping: {} -> {}".format(original.name, changed.name),
    )
    return ChangeResult(
        original=original,
        changed=changed,
        moving_lines=positions,
        original_bits=original_bits,
        changed_bits=cast(Tuple[int, int, int, int, int, int], changed_bits),
        calculation_trace=trace,
    )
