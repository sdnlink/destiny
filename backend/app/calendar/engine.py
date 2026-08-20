from dataclasses import asdict

import pytz
from lunar_python import Solar

from app.common.ganzhi import BRANCH_ZODIAC, EARTHLY_BRANCH_NUMBER, pillar_details, xun_info

from .models import CalendarInput
from .solar_terms import MONTH_JIE_BRANCH, REFERENCE_TIMEZONE, solar_term_context
from .timezone import (
    MAX_YEAR, MIN_YEAR, apply_true_solar_time, equation_of_time_minutes, parse_local_datetime,
)


ENGINE_VERSION = "calendar-engine-2.0.0+lunar-python-1.4.8"
RULE_VERSION = "calendar-domain-baseline-2.0.0"


def _solar_from_datetime(value):
    return Solar.fromYmdHms(value.year, value.month, value.day, value.hour, value.minute, value.second)


class CalendarEngine:
    """Deterministic Chinese calendar engine with explicit timezone boundaries."""

    def calculate(self, calendar_input=None, **kwargs):
        if calendar_input is not None and kwargs:
            raise TypeError("provide either calendar_input or keyword fields, not both")
        request = calendar_input if calendar_input is not None else CalendarInput(**kwargs)
        if not isinstance(request, CalendarInput):
            raise TypeError("calendar_input must be a CalendarInput")

        original = parse_local_datetime(request.local_datetime, request.timezone)
        if request.use_true_solar_time:
            if request.longitude is None:
                raise ValueError("longitude is required when true solar time is enabled")
            effective, correction = apply_true_solar_time(original, float(request.longitude))
        else:
            effective = original
            correction = {
                "enabled": False,
                "longitude": request.longitude,
                "total_correction_minutes": 0.0,
                "corrected_local_datetime": original.isoformat(),
            }

        reference_time = effective.astimezone(REFERENCE_TIMEZONE)
        reference_lunar = _solar_from_datetime(reference_time).getLunar()
        local_lunar = _solar_from_datetime(effective).getLunar()

        reference_eight_char = reference_lunar.getEightChar()
        reference_eight_char.setSect(1)
        local_eight_char = local_lunar.getEightChar()
        local_eight_char.setSect(1)

        year_pillar = reference_eight_char.getYear()
        month_pillar = reference_eight_char.getMonth()
        day_pillar = local_eight_char.getDay()
        time_pillar = local_eight_char.getTime()
        time_branch = local_lunar.getTimeZhi()
        lunar_month = reference_lunar.getMonth()
        terms = solar_term_context(reference_lunar, effective.tzinfo)
        day_xun = xun_info(day_pillar)
        pillars = {
            "year": year_pillar,
            "month": month_pillar,
            "day": day_pillar,
            "time": time_pillar,
            "year_boundary": "立春",
            "month_boundary": "节令",
            "day_boundary": "子初23:00",
        }
        ganzhi = {
            "year": pillar_details(year_pillar),
            "month": pillar_details(month_pillar),
            "day": pillar_details(day_pillar),
            "hour": pillar_details(time_pillar),
        }
        boundary_name = terms["previous_month_boundary"]["name"]
        expected_month_branch = MONTH_JIE_BRANCH.get(boundary_name)
        if expected_month_branch != month_pillar[1]:
            raise RuntimeError("month pillar branch conflicts with the active solar-term boundary")
        month_branch = {
            "name": month_pillar[1],
            "number": EARTHLY_BRANCH_NUMBER[month_pillar[1]],
            "boundary_name": boundary_name,
            "boundary_term": terms["previous_month_boundary"],
            "next_boundary_term": terms["next_month_boundary"],
        }
        zodiac = {"name": BRANCH_ZODIAC[year_pillar[1]], "branch": year_pillar[1], "boundary": "立春"}
        lunar_month_name = reference_lunar.getMonthInChinese()
        if lunar_month < 0 and lunar_month_name.startswith("闰"):
            lunar_month_name = lunar_month_name[1:]
        lunar = {
            "year": reference_lunar.getYear(),
            "month": abs(lunar_month),
            "day": reference_lunar.getDay(),
            "is_leap_month": lunar_month < 0,
            "month_name": lunar_month_name,
            "day_name": reference_lunar.getDayInChinese(),
        }
        trace = [
            "normalize local datetime and IANA timezone",
            "apply configured civil-time or true-solar-time standard",
            "convert effective instant to Asia/Shanghai solar-term reference time",
            "derive lunar date and adjacent exact solar-term moments",
            "derive year/month pillars by solar terms and day/hour pillars by effective local time",
            "derive month branch, zodiac, xun and empty branches",
        ]

        return {
            "schema_version": "2.0",
            "system": "calendar",
            "school": "mvp-engineering-baseline",
            "engine_version": ENGINE_VERSION,
            "rule_version": RULE_VERSION,
            "input": asdict(request),
            "normalized_input": {
                "local_datetime": original.isoformat(),
                "timezone": request.timezone,
                "effective_local_datetime": effective.isoformat(),
                "solar_term_reference_datetime": reference_time.isoformat(),
            },
            "time": {
                "original_local_datetime": original.isoformat(),
                "utc_datetime": original.astimezone(pytz.UTC).isoformat(),
                "effective_local_datetime": effective.isoformat(),
                "solar_term_reference_datetime": reference_time.isoformat(),
                "correction": correction,
            },
            "solar": {
                "year": effective.year, "month": effective.month, "day": effective.day,
                "hour": effective.hour, "minute": effective.minute, "second": effective.second,
            },
            "lunar": lunar,
            "pillars": pillars,
            "ganzhi": ganzhi,
            "month_branch": month_branch,
            "zodiac": zodiac,
            "time_branch": {"name": time_branch, "number": EARTHLY_BRANCH_NUMBER[time_branch]},
            "year_branch": {"name": year_pillar[1], "number": EARTHLY_BRANCH_NUMBER[year_pillar[1]]},
            "xun": day_xun,
            "xun_kong": list(day_xun["empty_branches"]),
            "solar_term": terms,
            "solar_terms": terms,
            "almanac": {
                "duty_officer": reference_lunar.getZhiXing(),
                "twenty_eight_mansion": {
                    "name": reference_lunar.getXiu(),
                    "luck": reference_lunar.getXiuLuck(),
                    "song": reference_lunar.getXiuSong(),
                },
                "day_tian_shen": {
                    "name": reference_lunar.getDayTianShen(),
                    "type": reference_lunar.getDayTianShenType(),
                    "luck": reference_lunar.getDayTianShenLuck(),
                },
                "day_nine_star": str(reference_lunar.getDayNineStar()),
                "favorable_activities": list(reference_lunar.getDayYi()),
                "unfavorable_activities": list(reference_lunar.getDayJi()),
                "lucky_directions": {
                    "joy_deity": reference_lunar.getDayPositionXiDesc(),
                    "wealth_deity": reference_lunar.getDayPositionCaiDesc(),
                    "blessing_deity": reference_lunar.getDayPositionFuDesc(),
                    "yang_noble": reference_lunar.getDayPositionYangGuiDesc(),
                    "yin_noble": reference_lunar.getDayPositionYinGuiDesc(),
                },
                "auspicious_spirits": list(reference_lunar.getDayJiShen()),
                "inauspicious_spirits": list(reference_lunar.getDayXiongSha()),
                "pengzu": {
                    "gan": reference_lunar.getPengZuGan(),
                    "zhi": reference_lunar.getPengZuZhi(),
                },
            },
            "calculation_trace": trace,
            "steps": [
                {
                    "sequence": 1, "operation": "normalize_local_datetime",
                    "inputs": {"local_datetime": request.local_datetime, "timezone": request.timezone},
                    "output": {
                        "local_datetime": original.isoformat(),
                        "utc_datetime": original.astimezone(pytz.UTC).isoformat(),
                    },
                    "rule_ids": ["CAL-NORMALIZE-001"],
                },
                {
                    "sequence": 2, "operation": "apply_time_standard",
                    "inputs": {"use_true_solar_time": request.use_true_solar_time, "longitude": request.longitude},
                    "output": {"effective_local_datetime": effective.isoformat(), "correction": correction},
                    "rule_ids": ["CAL-SOLAR-TIME-001"],
                },
                {
                    "sequence": 3, "operation": "normalize_solar_term_reference",
                    "inputs": {"effective_local_datetime": effective.isoformat()},
                    "output": {"reference_datetime": reference_time.isoformat()},
                    "rule_ids": ["CAL-TERM-TZ-001"],
                },
                {
                    "sequence": 4, "operation": "derive_lunar_and_solar_terms",
                    "inputs": {"reference_datetime": reference_time.isoformat()},
                    "output": {"lunar": lunar, "solar_terms": terms},
                    "rule_ids": ["CAL-CONVERSION-001", "CAL-TERM-001"],
                },
                {
                    "sequence": 5, "operation": "derive_four_pillars",
                    "inputs": {
                        "reference_datetime": reference_time.isoformat(),
                        "effective_local_datetime": effective.isoformat(),
                    },
                    "output": {"pillars": pillars, "ganzhi": ganzhi},
                    "rule_ids": ["CAL-PILLARS-001"],
                },
                {
                    "sequence": 6, "operation": "derive_calendar_cycles",
                    "inputs": {"year_pillar": year_pillar, "month_pillar": month_pillar, "day_pillar": day_pillar},
                    "output": {
                        "month_branch": month_branch, "zodiac": zodiac,
                        "xun": day_xun, "xun_kong": day_xun["empty_branches"],
                    },
                    "rule_ids": ["CAL-CYCLE-001", "CYCLE-XUN-001"],
                },
            ],
            "evidence": [], "judgements": [], "warnings": [],
        }


def calendar_analysis(local_datetime, timezone, longitude=None, use_true_solar_time=False):
    return CalendarEngine().calculate(CalendarInput(
        local_datetime=local_datetime, timezone=timezone, longitude=longitude,
        use_true_solar_time=use_true_solar_time,
    ))


__all__ = (
    "CalendarEngine", "CalendarInput", "ENGINE_VERSION", "MAX_YEAR", "MIN_YEAR", "RULE_VERSION",
    "apply_true_solar_time", "calendar_analysis", "equation_of_time_minutes", "parse_local_datetime",
)
