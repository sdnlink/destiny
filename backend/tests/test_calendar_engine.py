import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.calendar import CalendarEngine, CalendarInput
from app.calendar.solar_terms import SOLAR_TERM_NAMES


ENGINE = CalendarEngine()
MONTH_BOUNDARIES_2026 = (
    ("2026-01-05 16:23:10", "小寒", "丑"),
    ("2026-02-04 04:02:08", "立春", "寅"),
    ("2026-03-05 21:59:00", "惊蛰", "卯"),
    ("2026-04-05 02:40:00", "清明", "辰"),
    ("2026-05-05 19:48:44", "立夏", "巳"),
    ("2026-06-05 23:48:21", "芒种", "午"),
    ("2026-07-07 09:56:57", "小暑", "未"),
    ("2026-08-07 19:42:43", "立秋", "申"),
    ("2026-09-07 22:41:16", "白露", "酉"),
    ("2026-10-08 14:29:17", "寒露", "戌"),
    ("2026-11-07 17:52:05", "立冬", "亥"),
    ("2026-12-07 10:52:32", "大雪", "子"),
)
PREVIOUS_BRANCH = {"丑": "子", "寅": "丑", "卯": "寅", "辰": "卯", "巳": "辰", "午": "巳",
                   "未": "午", "申": "未", "酉": "申", "戌": "酉", "亥": "戌", "子": "亥"}


def calculate(value, timezone="Asia/Shanghai"):
    return ENGINE.calculate(local_datetime=value, timezone=timezone)


def test_calendar_input_is_typed_and_engine_has_no_required_state():
    request = CalendarInput("2026-08-16T09:30:00", "Asia/Shanghai")
    assert ENGINE.calculate(request)["input"] == {
        "local_datetime": "2026-08-16T09:30:00",
        "timezone": "Asia/Shanghai",
        "longitude": None,
        "use_true_solar_time": False,
    }
    with pytest.raises(TypeError):
        ENGINE.calculate({"local_datetime": request.local_datetime, "timezone": request.timezone})


def test_all_twenty_four_solar_terms_are_declared_once():
    assert len(SOLAR_TERM_NAMES) == 24
    assert len(set(SOLAR_TERM_NAMES)) == 24
    assert {"立春", "立夏", "立秋", "立冬", "春分", "夏至", "秋分", "冬至"} <= set(SOLAR_TERM_NAMES)


def test_exact_solar_term_second_keeps_reference_local_and_utc_evidence():
    term = calculate("2026-02-04T04:02:08")["solar_terms"]["current"]
    assert term == {
        "name": "立春",
        "datetime": "2026-02-04 04:02:08",
        "local_datetime": "2026-02-04T04:02:08+08:00",
        "reference_datetime": "2026-02-04T04:02:08+08:00",
        "utc_datetime": "2026-02-03T20:02:08+00:00",
    }


@pytest.mark.parametrize("boundary_text,term,branch", MONTH_BOUNDARIES_2026)
def test_month_branch_switches_at_each_exact_jie_boundary(boundary_text, term, branch):
    boundary = datetime.strptime(boundary_text, "%Y-%m-%d %H:%M:%S")
    before = calculate((boundary - timedelta(minutes=1)).isoformat())
    after = calculate((boundary + timedelta(minutes=1)).isoformat())

    assert before["month_branch"]["name"] == PREVIOUS_BRANCH[branch]
    assert after["month_branch"]["name"] == branch
    assert after["month_branch"]["boundary_name"] == term
    assert after["month_branch"]["boundary_term"]["name"] == term
    assert after["ganzhi"]["month"]["branch"] == branch


def test_lichun_changes_year_pillar_and_zodiac_before_lunar_new_year():
    before = calculate("2024-02-04T16:26:07")
    after = calculate("2024-02-04T16:28:07")
    assert before["pillars"]["year"] == "癸卯"
    assert before["zodiac"]["name"] == "兔"
    assert after["pillars"]["year"] == "甲辰"
    assert after["zodiac"] == {"name": "龙", "branch": "辰", "boundary": "立春"}
    assert after["lunar"]["year"] == 2023


def test_same_instant_crosses_lichun_in_different_iana_timezones():
    shanghai_before = calculate("2026-02-04T04:01:08", "Asia/Shanghai")
    new_york_before = calculate("2026-02-03T15:01:08", "America/New_York")
    shanghai_after = calculate("2026-02-04T04:03:08", "Asia/Shanghai")
    new_york_after = calculate("2026-02-03T15:03:08", "America/New_York")
    assert (shanghai_before["pillars"]["year"], shanghai_before["pillars"]["month"]) == (
        new_york_before["pillars"]["year"], new_york_before["pillars"]["month"],
    )
    assert (shanghai_after["pillars"]["year"], shanghai_after["pillars"]["month"]) == (
        new_york_after["pillars"]["year"], new_york_after["pillars"]["month"],
    )
    assert shanghai_before["pillars"]["year"] != shanghai_after["pillars"]["year"]


@pytest.mark.parametrize(
    "value,expected_day,expected_hour_branch",
    (
        ("2026-08-15T00:00:00", "辛酉", "子"),
        ("2026-08-15T22:59:59", "辛酉", "亥"),
        ("2026-08-15T23:00:00", "壬戌", "子"),
        ("2026-08-15T23:59:00", "壬戌", "子"),
    ),
)
def test_day_and_hour_boundaries(value, expected_day, expected_hour_branch):
    result = calculate(value)
    assert result["pillars"]["day"] == expected_day
    assert result["time_branch"]["name"] == expected_hour_branch


def test_lunar_new_year_and_leap_month_are_separate_from_solar_term_pillars():
    new_year_eve = calculate("2024-02-09T12:00:00")
    new_year = calculate("2024-02-10T12:00:00")
    leap_month = calculate("2023-03-22T12:00:00")
    assert (new_year_eve["lunar"]["year"], new_year_eve["lunar"]["month"], new_year_eve["lunar"]["day"]) == (2023, 12, 30)
    assert (new_year["lunar"]["year"], new_year["lunar"]["month"], new_year["lunar"]["day"]) == (2024, 1, 1)
    assert new_year_eve["pillars"]["year"] == new_year["pillars"]["year"] == "甲辰"
    assert leap_month["lunar"]["is_leap_month"] is True
    assert leap_month["lunar"]["month"] == 2
    assert leap_month["lunar"]["month_name"] == "二"


def test_structured_ganzhi_xun_and_trace_are_complete():
    result = calculate("2026-08-15T16:00:00")
    assert result["ganzhi"]["day"] == {
        "text": "辛酉", "stem": "辛", "branch": "酉", "stem_element": "金",
        "branch_element": "金", "polarity": "阴", "sexagenary_number": 58,
    }
    assert result["xun"]["name"] == "甲寅旬"
    assert result["xun_kong"] == ["子", "丑"]
    assert len(result["calculation_trace"]) == 6
    assert [step["sequence"] for step in result["steps"]] == list(range(1, 7))
    assert result["solar_terms"]["supported_term_count"] == 24


def test_dst_gap_and_ambiguous_time_are_rejected():
    with pytest.raises(ValueError, match="does not exist"):
        calculate("2026-03-08T02:30:00", "America/New_York")
    with pytest.raises(ValueError, match="ambiguous"):
        calculate("2026-11-01T01:30:00", "America/New_York")
