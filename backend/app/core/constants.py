from app.common.hexagrams import HEXAGRAM_NAMES, KING_WEN_MATRIX
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

FIVE_ELEMENTS_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
FIVE_ELEMENTS_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

EARTHLY_BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
EARTHLY_BRANCH_NUMBER = {name: index for index, name in enumerate(EARTHLY_BRANCHES, 1)}


def trigram_number(value):
    remainder = int(value) % 8
    return 8 if remainder == 0 else remainder


def moving_line_number(value):
    remainder = int(value) % 6
    return 6 if remainder == 0 else remainder
