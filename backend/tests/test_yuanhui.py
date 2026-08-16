import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.calendar import calendar_analysis
from app.core.meihua import number_cast
from app.core.yuanhui import analyze_yuan_hui_yun_shi, cycle_position


class YuanHuiTests(unittest.TestCase):
    def test_2026_engineering_baseline(self):
        facts = cycle_position(2026)
        self.assertEqual(facts["yuan"]["index"], 1)
        self.assertEqual(facts["hui"]["index"], 7)
        self.assertEqual(facts["hui"]["branch"], "午")
        self.assertEqual(facts["yun"]["index"], 12)
        self.assertEqual(facts["shi"]["index"], 10)
        self.assertEqual(facts["shi"]["year_in_shi"], 13)

    def test_relations_are_facts_without_polarity(self):
        modules = [
            {"module": "calendar", "method": "analyze", "result": calendar_analysis("2026-08-15T16:00:00", "Asia/Shanghai")},
            {"module": "meihua", "method": "numbers", "result": number_cast(1, 2)},
        ]
        output = analyze_yuan_hui_yun_shi(modules)
        self.assertEqual(len(output["evidence"]), 2)
        self.assertTrue(all("polarity" not in item for item in output["evidence"]))


if __name__ == "__main__":
    unittest.main()

