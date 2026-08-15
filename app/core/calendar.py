import math
from datetime import datetime, timedelta

import pytz
from lunar_python import Solar
from pytz.exceptions import AmbiguousTimeError, NonExistentTimeError, UnknownTimeZoneError

from .constants import EARTHLY_BRANCH_NUMBER


ENGINE_VERSION = "calendar-engine-1.0.0+lunar-python-1.4.8"
RULE_VERSION = "calendar-mvp-baseline-1.0.0"
MIN_YEAR = 1900
MAX_YEAR = 2100


def parse_local_datetime(value, timezone_name):
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        raise ValueError("local_datetime must be an ISO-8601 date and time")
    if parsed.tzinfo is not None:
        raise ValueError("local_datetime must not contain an offset; provide timezone separately")
    if parsed.year < MIN_YEAR or parsed.year > MAX_YEAR:
        raise ValueError(f"supported year range is {MIN_YEAR} through {MAX_YEAR}")
    try:
        timezone = pytz.timezone(timezone_name)
    except UnknownTimeZoneError:
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
    corrected = local_time + timedelta(minutes=total_minutes)
    corrected = local_time.tzinfo.normalize(corrected)
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


def _jieqi(value):
    if value is None:
        return None
    solar = value.getSolar()
    return {"name": value.getName(), "datetime": solar.toYmdHms()}


def calendar_analysis(local_datetime, timezone, longitude=None, use_true_solar_time=False):
    original = parse_local_datetime(local_datetime, timezone)
    if use_true_solar_time:
        if longitude is None:
            raise ValueError("longitude is required when true solar time is enabled")
        effective, correction = apply_true_solar_time(original, float(longitude))
    else:
        effective = original
        correction = {
            "enabled": False,
            "longitude": longitude,
            "total_correction_minutes": 0.0,
            "corrected_local_datetime": original.isoformat(),
        }

    solar = Solar.fromYmdHms(
        effective.year, effective.month, effective.day,
        effective.hour, effective.minute, effective.second,
    )
    lunar = solar.getLunar()
    eight_char = lunar.getEightChar()
    eight_char.setSect(1)  # Sect 1 changes the day pillar at 23:00.
    year_pillar = eight_char.getYear()
    month_pillar = eight_char.getMonth()
    day_pillar = eight_char.getDay()
    time_pillar = eight_char.getTime()
    lunar_month = lunar.getMonth()
    time_branch = lunar.getTimeZhi()

    result = {
        "schema_version": "1.0",
        "system": "calendar",
        "school": "mvp-engineering-baseline",
        "engine_version": ENGINE_VERSION,
        "rule_version": RULE_VERSION,
        "input": {
            "local_datetime": local_datetime,
            "timezone": timezone,
            "longitude": longitude,
            "use_true_solar_time": use_true_solar_time,
        },
        "time": {
            "original_local_datetime": original.isoformat(),
            "utc_datetime": original.astimezone(pytz.UTC).isoformat(),
            "effective_local_datetime": effective.isoformat(),
            "correction": correction,
        },
        "solar": {
            "year": effective.year,
            "month": effective.month,
            "day": effective.day,
            "hour": effective.hour,
            "minute": effective.minute,
            "second": effective.second,
        },
        "lunar": {
            "year": lunar.getYear(),
            "month": abs(lunar_month),
            "day": lunar.getDay(),
            "is_leap_month": lunar_month < 0,
            "month_name": lunar.getMonthInChinese(),
            "day_name": lunar.getDayInChinese(),
        },
        "pillars": {
            "year": year_pillar,
            "month": month_pillar,
            "day": day_pillar,
            "time": time_pillar,
            "year_boundary": "立春",
            "month_boundary": "节令",
            "day_boundary": "子初23:00",
        },
        "time_branch": {
            "name": time_branch,
            "number": EARTHLY_BRANCH_NUMBER[time_branch],
        },
        "year_branch": {
            "name": year_pillar[1],
            "number": EARTHLY_BRANCH_NUMBER[year_pillar[1]],
        },
        "solar_terms": {
            "previous": _jieqi(lunar.getPrevJieQi()),
            "current": _jieqi(lunar.getCurrentJieQi()),
            "next": _jieqi(lunar.getNextJieQi()),
        },
        "steps": [
            {
                "sequence": 1,
                "operation": "normalize_local_datetime",
                "inputs": {"local_datetime": local_datetime, "timezone": timezone},
                "output": {
                    "local_datetime": original.isoformat(),
                    "utc_datetime": original.astimezone(pytz.UTC).isoformat(),
                },
                "rule_ids": ["CAL-NORMALIZE-001"],
            },
            {
                "sequence": 2,
                "operation": "apply_time_standard",
                "inputs": {
                    "use_true_solar_time": use_true_solar_time,
                    "longitude": longitude,
                },
                "output": {
                    "effective_local_datetime": effective.isoformat(),
                    "correction": correction,
                },
                "rule_ids": ["CAL-SOLAR-TIME-001"],
            },
            {
                "sequence": 3,
                "operation": "derive_calendar_and_pillars",
                "inputs": {"effective_local_datetime": effective.isoformat()},
                "output": {
                    "lunar": {
                        "year": lunar.getYear(),
                        "month": abs(lunar_month),
                        "day": lunar.getDay(),
                        "is_leap_month": lunar_month < 0,
                    },
                    "pillars": {
                        "year": year_pillar,
                        "month": month_pillar,
                        "day": day_pillar,
                        "time": time_pillar,
                    },
                },
                "rule_ids": ["CAL-CONVERSION-001", "CAL-PILLARS-001"],
            },
        ],
        "evidence": [],
        "judgements": [],
        "warnings": [],
    }
    return result
