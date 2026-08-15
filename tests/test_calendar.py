import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.calendar import calendar_analysis, parse_local_datetime


class CalendarTests(unittest.TestCase):
    def test_chinese_new_year_2024(self):
        result = calendar_analysis("2024-02-10T12:00:00", "Asia/Shanghai")
        self.assertEqual(
            (result["lunar"]["year"], result["lunar"]["month"], result["lunar"]["day"]),
            (2024, 1, 1),
        )
        self.assertEqual(result["pillars"]["year"], "甲辰")

    def test_known_2026_pillars(self):
        result = calendar_analysis("2026-08-15T16:00:00", "Asia/Shanghai")
        self.assertEqual(result["pillars"], {
            "year": "丙午", "month": "丙申", "day": "辛酉", "time": "丙申",
            "year_boundary": "立春", "month_boundary": "节令", "day_boundary": "子初23:00",
        })
        self.assertEqual(result["solar_terms"]["previous"]["name"], "立秋")
        self.assertEqual(result["solar_terms"]["next"]["name"], "处暑")

    def test_day_pillar_changes_at_23(self):
        before = calendar_analysis("2026-08-15T22:59:59", "Asia/Shanghai")
        after = calendar_analysis("2026-08-15T23:00:00", "Asia/Shanghai")
        self.assertEqual(before["pillars"]["day"], "辛酉")
        self.assertEqual(after["pillars"]["day"], "壬戌")

    def test_true_solar_time_requires_longitude(self):
        with self.assertRaises(ValueError):
            calendar_analysis("2026-08-15T12:00:00", "Asia/Shanghai", use_true_solar_time=True)

    def test_true_solar_time_records_components(self):
        result = calendar_analysis(
            "2026-08-15T12:00:00", "Asia/Shanghai", longitude=105, use_true_solar_time=True
        )
        correction = result["time"]["correction"]
        self.assertEqual(correction["standard_meridian"], 120.0)
        self.assertEqual(correction["longitude_correction_minutes"], -60.0)
        self.assertLess(correction["total_correction_minutes"], -50)

    def test_invalid_timezone_and_dst_gap_are_rejected(self):
        with self.assertRaises(ValueError):
            parse_local_datetime("2026-08-15T12:00:00", "Unknown/Zone")
        with self.assertRaises(ValueError):
            parse_local_datetime("2026-03-08T02:30:00", "America/New_York")


if __name__ == "__main__":
    unittest.main()
