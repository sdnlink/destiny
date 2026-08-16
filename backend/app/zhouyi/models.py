from dataclasses import dataclass

from .config import DEFAULT_MAPPING_VERSION


@dataclass(frozen=True)
class ThreeNumberInput:
    number1: int
    number2: int
    number3: int
    mapping_version: str = DEFAULT_MAPPING_VERSION

    def __post_init__(self) -> None:
        values = (self.number1, self.number2, self.number3)
        if any(type(value) is not int or value < 0 for value in values):
            raise ValueError("three-number inputs must be non-negative integers")
        if not isinstance(self.mapping_version, str) or not self.mapping_version:
            raise ValueError("mapping_version must be a non-empty string")

    @property
    def numbers(self):
        return (self.number1, self.number2, self.number3)
