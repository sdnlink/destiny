from typing import Iterable

from .hexagrams import change_hexagram, get_hexagram_by_lines, hexagram_to_bits
from .trigrams import trigram_to_bits


def trigram_to_dict(trigram):
    return {
        "number": trigram.number,
        "name": trigram.name,
        "symbol": trigram.symbol,
        "lines": trigram_to_bits(trigram),
        "element": trigram.element,
        "direction": trigram.direction,
    }


def hexagram_to_dict(hexagram):
    return {
        "ordinal": hexagram.ordinal,
        "name": hexagram.name,
        "symbol": hexagram.symbol,
        "lines": list(hexagram_to_bits(hexagram)),
        "lower_trigram": trigram_to_dict(hexagram.lower_trigram),
        "upper_trigram": trigram_to_dict(hexagram.upper_trigram),
    }


def derive_hexagram_facts(lines: Iterable[int], moving_lines: Iterable[int]):
    normalized = tuple(lines)
    change = change_hexagram(normalized, moving_lines)
    mutual = (normalized[1], normalized[2], normalized[3], normalized[2], normalized[3], normalized[4])
    opposite = tuple(1 - value for value in normalized)
    reversed_lines = tuple(reversed(normalized))
    return {
        "original": hexagram_to_dict(change.original),
        "changed": hexagram_to_dict(change.changed),
        "mutual": hexagram_to_dict(get_hexagram_by_lines(mutual)),
        "opposite": hexagram_to_dict(get_hexagram_by_lines(opposite)),
        "reversed": hexagram_to_dict(get_hexagram_by_lines(reversed_lines)),
        "moving_lines": list(change.moving_lines),
    }
