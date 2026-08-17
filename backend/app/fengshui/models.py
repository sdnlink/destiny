import math
from dataclasses import dataclass
from typing import Optional, Tuple


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("{} must be a finite number".format(label))
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("{} must be a finite number".format(label))
    return number


@dataclass(frozen=True)
class DirectionInput:
    facing_degree: float
    input_reference: str = "magnetic"
    magnetic_declination: float = 0.0
    measurement_error: float = 0.0
    declination_source: Optional[str] = None
    measurement_method: Optional[str] = None

    def __post_init__(self):
        facing = _finite_number(self.facing_degree, "facing degree")
        declination = _finite_number(self.magnetic_declination, "magnetic declination")
        error = _finite_number(self.measurement_error, "measurement error")
        if self.input_reference not in ("magnetic", "true"):
            raise ValueError("input reference must be magnetic or true")
        if error < 0 or error > 180:
            raise ValueError("measurement error must be between 0 and 180 degrees")
        for value, label in (
            (self.declination_source, "declination source"),
            (self.measurement_method, "measurement method"),
        ):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError("{} must be a non-empty string".format(label))
        object.__setattr__(self, "facing_degree", facing)
        object.__setattr__(self, "magnetic_declination", declination)
        object.__setattr__(self, "measurement_error", error)
        if self.declination_source is not None:
            object.__setattr__(self, "declination_source", self.declination_source.strip())
        if self.measurement_method is not None:
            object.__setattr__(self, "measurement_method", self.measurement_method.strip())


@dataclass(frozen=True)
class MeasurementBatchInput:
    measurements: Tuple[DirectionInput, ...]

    def __post_init__(self):
        if not isinstance(self.measurements, tuple):
            raise ValueError("measurements must be an immutable sequence")
        if not 3 <= len(self.measurements) <= 12:
            raise ValueError("measurement batch must contain between 3 and 12 readings")
        if not all(isinstance(value, DirectionInput) for value in self.measurements):
            raise ValueError("every measurement must be a direction input")
