import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.liuren import number_cast, time_cast


REQUEST_TIME = {"local_datetime": "2026-08-15T16:00:00", "timezone": "Asia/Shanghai"}


class LiurenTests(unittest.TestCase):
    def test_time_chart_contains_required_facts(self):
        result = time_cast(**REQUEST_TIME)
        facts = result["facts"]
        self.assertEqual(facts["day_pillar"], "辛酉")
        self.assertEqual(facts["month_general"]["branch"], "午")
        self.assertEqual(facts["month_general"]["boundary_term"], "大暑")
        self.assertEqual(facts["occupation_time"]["branch"], "申")
        self.assertEqual(facts["heaven_plate"]["申"], "午")
        self.assertEqual(len(facts["four_lessons"]), 4)
        self.assertEqual(facts["three_transmissions"]["transmissions"], ["午", "辰", "寅"])
        self.assertEqual(facts["xun"]["empty_branches"], ["子", "丑"])
        self.assertEqual(len(facts["heavenly_generals"]["by_ground"]), 12)

    def test_number_maps_to_occupation_branch(self):
        result = number_cast(12, **REQUEST_TIME)
        self.assertEqual(result["facts"]["occupation_time"], {"branch": "亥", "number": 12, "input_number": 12})
        self.assertEqual(result["facts"]["actual_time_branch"], "申")

    def test_number_remainder_zero_and_negative_are_deterministic(self):
        self.assertEqual(number_cast(24, **REQUEST_TIME)["facts"]["occupation_time"]["branch"], "亥")
        self.assertEqual(number_cast(-1, **REQUEST_TIME)["facts"]["occupation_time"]["branch"], "戌")


if __name__ == "__main__":
    unittest.main()

