from app.common.hexagrams import HEXAGRAM_NAMES, KING_WEN_MATRIX
from app.common.ganzhi import EARTHLY_BRANCHES, EARTHLY_BRANCH_NUMBER
from app.common.five_elements import FIVE_ELEMENTS_CONTROLS, FIVE_ELEMENTS_GENERATES
from app.common.trigrams import TRIGRAM_CATALOG, trigram_to_bits


# Compatibility dictionaries for existing API serializers. Authoritative,
# immutable domain models live in app.common.
TRIGRAMS = {
    trigram.number: {
        "name": trigram.name,
        "symbol": trigram.symbol,
        "lines": trigram_to_bits(trigram),
        "element": trigram.element,
        "direction": trigram.direction,
    }
    for trigram in TRIGRAM_CATALOG
}

TRIGRAM_BY_LINES = {value["lines"]: {"number": key, **value} for key, value in TRIGRAMS.items()}
TRIGRAM_BY_NAME = {value["name"]: {"number": key, **value} for key, value in TRIGRAMS.items()}

def trigram_number(value):
    remainder = int(value) % 8
    return 8 if remainder == 0 else remainder


def moving_line_number(value):
    remainder = int(value) % 6
    return 6 if remainder == 0 else remainder
