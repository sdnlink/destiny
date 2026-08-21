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

        # 计算当日十二时辰吉凶时序轮盘
        hourly_timeline = []
        hour_samples = [
            (0, "23:00 - 01:00"), (2, "01:00 - 03:00"), (4, "03:00 - 05:00"),
            (6, "05:00 - 07:00"), (8, "07:00 - 09:00"), (10, "09:00 - 11:00"),
            (12, "11:00 - 13:00"), (14, "13:00 - 15:00"), (16, "15:00 - 17:00"),
            (18, "17:00 - 19:00"), (20, "19:00 - 21:00"), (22, "21:00 - 23:00"),
        ]
        for h_sample, time_range in hour_samples:
            try:
                sample_solar = Solar.fromYmdHms(effective.year, effective.month, effective.day, h_sample, 0, 0)
                sample_lunar = sample_solar.getLunar()
                hourly_timeline.append({
                    "hour": h_sample,
                    "branch": sample_lunar.getTimeZhi(),
                    "time_range": time_range,
                    "ganzhi": sample_lunar.getTimeInGanZhi(),
                    "tian_shen": {
                        "name": sample_lunar.getTimeTianShen(),
                        "type": sample_lunar.getTimeTianShenType(),
                        "luck": sample_lunar.getTimeTianShenLuck(),
                    },
                    "clash": {
                        "animal": sample_lunar.getTimeChongShengXiao(),
                        "direction": sample_lunar.getTimeSha(),
                    },
                    "favorable_activities": list(sample_lunar.getTimeYi())[:6],
                    "unfavorable_activities": list(sample_lunar.getTimeJi())[:4],
                })
            except Exception:
                pass

        # 28宿与四象对应
        xiu_name = reference_lunar.getXiu()
        mansion_beast_map = {
            "角": "角木蛟", "亢": "亢金龙", "氐": "氐土貉", "房": "房日兔", "心": "心月狐", "尾": "尾火虎", "箕": "箕水豹",
            "斗": "斗木獬", "牛": "牛金牛", "女": "女土蝠", "虚": "虚日鼠", "危": "危月燕", "室": "室火猪", "壁": "壁水貐",
            "奎": "奎木狼", "娄": "娄金狗", "胃": "胃土雉", "昴": "昴日鸡", "毕": "毕月乌", "觜": "觜火猴", "参": "参水猿",
            "井": "井木犴", "鬼": "鬼金羊", "柳": "柳土獐", "星": "星日马", "张": "张月鹿", "翼": "翼火蛇", "轸": "轸水蚓",
        }
        mansion_quad_map = {
            "角": "东方苍龙", "亢": "东方苍龙", "氐": "东方苍龙", "房": "东方苍龙", "心": "东方苍龙", "尾": "东方苍龙", "箕": "东方苍龙",
            "斗": "北方玄武", "牛": "北方玄武", "女": "北方玄武", "虚": "北方玄武", "危": "北方玄武", "室": "北方玄武", "壁": "北方玄武",
            "奎": "西方白虎", "娄": "西方白虎", "胃": "西方白虎", "昴": "西方白虎", "毕": "西方白虎", "觜": "西方白虎", "参": "西方白虎",
            "井": "南方朱雀", "鬼": "南方朱雀", "柳": "南方朱雀", "星": "南方朱雀", "张": "南方朱雀", "翼": "南方朱雀", "轸": "南方朱雀",
        }

        # 西周金文四分月相
        lunar_day = reference_lunar.getDay()
        if lunar_day <= 8:
            lunar_phase_regime = {"code": "chuji", "name": "初吉", "description": "新月至上弦，月牙始苏，阳德初升"}
        elif lunar_day <= 15:
            lunar_phase_regime = {"code": "jishengba", "name": "既生霸", "description": "上弦至满月，月魄渐生，光明充盈"}
        elif lunar_day <= 23:
            lunar_phase_regime = {"code": "jiwang", "name": "既望", "description": "满月至下弦，月华极盛，圆满始亏"}
        else:
            lunar_phase_regime = {"code": "jisiba", "name": "既死霸", "description": "下弦至晦日，月魄渐隐，归息敛藏"}

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
                    "name": xiu_name,
                    "beast_spirit": mansion_beast_map.get(xiu_name, xiu_name),
                    "quadrant": mansion_quad_map.get(xiu_name, ""),
                    "luck": reference_lunar.getXiuLuck(),
                    "song": reference_lunar.getXiuSong(),
                },
                "lunar_phase_regime": lunar_phase_regime,
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
                "hourly_timeline": hourly_timeline,
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
