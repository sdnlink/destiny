from dataclasses import dataclass
from types import MappingProxyType
from typing import Tuple

from app.common.models import Trigram
from app.common.trigrams import get_trigram_by_number


DEFAULT_MAPPING_VERSION = "earlier-heaven-number-v1"


@dataclass(frozen=True)
class TrigramNumberMapping:
    version: str
    label: str
    trigram_numbers: Tuple[int, int, int, int, int, int, int, int]

    def __post_init__(self) -> None:
        if len(self.trigram_numbers) != 8 or set(self.trigram_numbers) != set(range(1, 9)):
            raise ValueError("trigram mapping must contain each trigram number exactly once")

    def resolve(self, source_number: int) -> Tuple[int, Trigram]:
        if type(source_number) is not int or source_number < 0:
            raise ValueError("source number must be a non-negative integer")
        remainder = source_number % 8
        normalized = 8 if remainder == 0 else remainder
        trigram_number = self.trigram_numbers[normalized - 1]
        return normalized, get_trigram_by_number(trigram_number)


MAPPINGS = MappingProxyType({
    DEFAULT_MAPPING_VERSION: TrigramNumberMapping(
        version=DEFAULT_MAPPING_VERSION,
        label="乾1兑2离3震4巽5坎6艮7坤8",
        trigram_numbers=(1, 2, 3, 4, 5, 6, 7, 8),
    ),
})


def get_mapping(version: str = DEFAULT_MAPPING_VERSION) -> TrigramNumberMapping:
    try:
        return MAPPINGS[version]
    except (KeyError, TypeError):
        raise ValueError("unsupported trigram mapping version: {}".format(version))
