from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class LinePolarity(str, Enum):
    YIN = "yin"
    YANG = "yang"


@dataclass(frozen=True)
class Line:
    """One immutable yin/yang line; 0 is yin and 1 is yang."""

    polarity: LinePolarity

    def __post_init__(self) -> None:
        if not isinstance(self.polarity, LinePolarity):
            raise ValueError("line polarity must be a LinePolarity value")

    @classmethod
    def from_bit(cls, bit: int) -> "Line":
        if type(bit) is not int or bit not in (0, 1):
            raise ValueError("line bit must be 0 (yin) or 1 (yang)")
        return cls(LinePolarity.YANG if bit == 1 else LinePolarity.YIN)

    @property
    def bit(self) -> int:
        return 1 if self.polarity is LinePolarity.YANG else 0

    def changed(self) -> "Line":
        return Line.from_bit(1 - self.bit)


@dataclass(frozen=True)
class Trigram:
    number: int
    name: str
    symbol: str
    lines: Tuple[Line, Line, Line]
    element: str
    direction: str

    def __post_init__(self) -> None:
        if not 1 <= self.number <= 8:
            raise ValueError("trigram number must be between 1 and 8")
        if len(self.lines) != 3:
            raise ValueError("trigram must contain three lines from bottom to top")
        if any(not isinstance(line, Line) for line in self.lines):
            raise ValueError("trigram lines must contain Line values")


@dataclass(frozen=True)
class Hexagram:
    ordinal: int
    name: str
    symbol: str
    lower_trigram: Trigram
    upper_trigram: Trigram

    def __post_init__(self) -> None:
        if not 1 <= self.ordinal <= 64:
            raise ValueError("hexagram ordinal must be between 1 and 64")
        if not isinstance(self.lower_trigram, Trigram) or not isinstance(self.upper_trigram, Trigram):
            raise ValueError("hexagram must contain lower and upper trigrams")

    @property
    def lines(self) -> Tuple[Line, Line, Line, Line, Line, Line]:
        return self.lower_trigram.lines + self.upper_trigram.lines
