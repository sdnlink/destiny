from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class CalendarInput:
    local_datetime: str
    timezone: str
    longitude: Optional[float] = None
    use_true_solar_time: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.local_datetime, str) or not self.local_datetime.strip():
            raise ValueError("local_datetime must be a non-empty string")
        if not isinstance(self.timezone, str) or not self.timezone.strip():
            raise ValueError("timezone must be a non-empty IANA timezone name")
        if type(self.use_true_solar_time) is not bool:
            raise ValueError("use_true_solar_time must be boolean")
        if self.longitude is not None and (type(self.longitude) not in (int, float) or not -180 <= self.longitude <= 180):
            raise ValueError("longitude must be a number between -180 and 180")
