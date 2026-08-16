import math
from datetime import datetime, timedelta

import pytz
from pytz.exceptions import AmbiguousTimeError, NonExistentTimeError, UnknownTimeZoneError


MIN_YEAR = 1900
MAX_YEAR = 2100


def parse_local_datetime(value, timezone_name):
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("local_datetime must be an ISO-8601 date and time")
    if parsed.tzinfo is not None:
        raise ValueError("local_datetime must not contain an offset; provide timezone separately")
    if parsed.year < MIN_YEAR or parsed.year > MAX_YEAR:
        raise ValueError("supported year range is {} through {}".format(MIN_YEAR, MAX_YEAR))
    try:
        timezone = pytz.timezone(timezone_name)
    except (AttributeError, UnknownTimeZoneError):
        raise ValueError("timezone must be a valid IANA timezone name")
    try:
        return timezone.localize(parsed, is_dst=None)
    except AmbiguousTimeError:
        raise ValueError("local_datetime is ambiguous because of a daylight-saving transition")
    except NonExistentTimeError:
        raise ValueError("local_datetime does not exist because of a daylight-saving transition")


def equation_of_time_minutes(value):
    day_of_year = value.timetuple().tm_yday
    angle = 2 * math.pi * (day_of_year - 81) / 364
    return 9.87 * math.sin(2 * angle) - 7.53 * math.cos(angle) - 1.5 * math.sin(angle)


def apply_true_solar_time(local_time, longitude):
    if longitude < -180 or longitude > 180:
        raise ValueError("longitude must be between -180 and 180")
    daylight_minutes = local_time.dst().total_seconds() / 60 if local_time.dst() else 0.0
    standard_offset = local_time.utcoffset() - (local_time.dst() or timedelta(0))
    standard_offset_hours = standard_offset.total_seconds() / 3600
    standard_meridian = standard_offset_hours * 15
    longitude_minutes = 4 * (longitude - standard_meridian)
    equation_minutes = equation_of_time_minutes(local_time)
    daylight_correction = -daylight_minutes
    total_minutes = daylight_correction + longitude_minutes + equation_minutes
    corrected = local_time.tzinfo.normalize(local_time + timedelta(minutes=total_minutes))
    return corrected, {
        "enabled": True,
        "longitude": round(longitude, 6),
        "standard_meridian": round(standard_meridian, 6),
        "daylight_saving_correction_minutes": round(daylight_correction, 6),
        "longitude_correction_minutes": round(longitude_minutes, 6),
        "equation_of_time_minutes": round(equation_minutes, 6),
        "total_correction_minutes": round(total_minutes, 6),
        "corrected_local_datetime": corrected.isoformat(),
        "algorithm": "NOAA-style equation-of-time approximation",
    }
