"""Shared immutable facts used by divination systems.

This package contains only mathematical representations. System-specific
rules such as Meihua body/use and Liuyao host/response do not belong here.
"""

from .hexagrams import (
    ChangeResult,
    change_hexagram,
    get_hexagram_by_lines,
    get_hexagram_by_ordinal,
    hexagram_to_bits,
)
from .ganzhi import EARTHLY_BRANCHES, HEAVENLY_STEMS, pillar_details, sexagenary_index, xun_info
from .models import Hexagram, Line, LinePolarity, Trigram
from .trigrams import get_trigram_by_bits, get_trigram_by_number, trigram_to_bits


__all__ = (
    "ChangeResult",
    "Hexagram",
    "EARTHLY_BRANCHES",
    "HEAVENLY_STEMS",
    "Line",
    "LinePolarity",
    "Trigram",
    "change_hexagram",
    "get_hexagram_by_lines",
    "get_hexagram_by_ordinal",
    "get_trigram_by_bits",
    "get_trigram_by_number",
    "hexagram_to_bits",
    "pillar_details",
    "sexagenary_index",
    "trigram_to_bits",
    "xun_info",
)
