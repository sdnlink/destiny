from dataclasses import dataclass
from typing import Tuple


LineValues = Tuple[int, int, int, int, int, int]
CoinRound = Tuple[int, int, int]
CoinRounds = Tuple[CoinRound, CoinRound, CoinRound, CoinRound, CoinRound, CoinRound]


@dataclass(frozen=True)
class SixLineInput:
    lines: LineValues

    def __post_init__(self) -> None:
        if len(self.lines) != 6 or any(type(value) is not int or value not in (6, 7, 8, 9) for value in self.lines):
            raise ValueError("lines must contain six integer values 6, 7, 8, or 9 from bottom to top")


@dataclass(frozen=True)
class ThreeCoinInput:
    rounds: CoinRounds

    def __post_init__(self) -> None:
        if len(self.rounds) != 6:
            raise ValueError("coins must contain six rounds from first line to top line")
        for coins in self.rounds:
            if len(coins) != 3 or any(type(value) is not int or value not in (2, 3) for value in coins):
                raise ValueError("each coin round must contain three integer values 2 or 3")

    @property
    def line_values(self) -> LineValues:
        return tuple(sum(coins) for coins in self.rounds)  # type: ignore[return-value]
