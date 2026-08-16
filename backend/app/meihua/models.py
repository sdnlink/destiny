from dataclasses import dataclass


def _validate_integer(value, name):
    if type(value) is not int:
        raise ValueError("{} must be an integer".format(name))


@dataclass(frozen=True)
class TwoNumberInput:
    upper_number: int
    lower_number: int

    def __post_init__(self) -> None:
        _validate_integer(self.upper_number, "upper_number")
        _validate_integer(self.lower_number, "lower_number")


@dataclass(frozen=True)
class ThreeNumberInput:
    upper_number: int
    lower_number: int
    moving_number: int

    def __post_init__(self) -> None:
        _validate_integer(self.upper_number, "upper_number")
        _validate_integer(self.lower_number, "lower_number")
        _validate_integer(self.moving_number, "moving_number")
