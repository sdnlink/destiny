from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class OccupationNumberInput:
    value: int

    def __post_init__(self) -> None:
        if type(self.value) is not int:
            raise ValueError("occupation number must be an integer")


@dataclass(frozen=True)
class PlateInput:
    heaven_branches: Tuple[str, ...]

    def __post_init__(self) -> None:
        if len(self.heaven_branches) != 12 or len(set(self.heaven_branches)) != 12:
            raise ValueError("heaven plate must contain twelve unique branches")
