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
from .models import Hexagram, Line, LinePolarity, Trigram
from .trigrams import get_trigram_by_bits, get_trigram_by_number, trigram_to_bits


__all__ = (
    "ChangeResult",
    "Hexagram",
    "Line",
    "LinePolarity",
    "Trigram",
    "change_hexagram",
    "get_hexagram_by_lines",
    "get_hexagram_by_ordinal",
    "get_trigram_by_bits",
    "get_trigram_by_number",
    "hexagram_to_bits",
    "trigram_to_bits",
)
