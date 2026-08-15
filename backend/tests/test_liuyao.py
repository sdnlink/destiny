import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.liuyao import PALACE_BY_LINES, number_cast, time_cast


REQUEST_TIME = {"local_datetime": "2026-08-15T16:00:00", "timezone": "Asia/Shanghai"}


class LiuyaoTests(unittest.TestCase):
    def test_palace_index_contains_all_hexagrams(self):
        self.assertEqual(len(PALACE_BY_LINES), 64)

    def test_pure_qian_najia_chart(self):
        result = number_cast(1, 1, **REQUEST_TIME)
        facts = result["facts"]
        self.assertEqual(facts["original"]["name"], "乾")
        self.assertEqual(facts["palace"]["name"], "乾")
        self.assertEqual(facts["palace"]["host_line"], 6)
        self.assertEqual(facts["palace"]["response_line"], 3)
        self.assertEqual([line["najia_branch"] for line in facts["line_chart"]], ["子", "寅", "辰", "午", "申", "戌"])
        self.assertEqual(facts["line_chart"][0]["six_relative"], "子孙")
        self.assertEqual(facts["line_chart"][0]["six_spirit"], "白虎")
        self.assertTrue(facts["line_chart"][0]["is_void"])

    def test_returning_soul_palace_stage(self):
        result = number_cast(1, 3, **REQUEST_TIME)
        self.assertEqual(result["facts"]["original"]["name"], "大有")
        self.assertEqual(result["facts"]["palace"]["stage"], "归魂")
        self.assertEqual(result["facts"]["palace"]["name"], "乾")

    def test_time_cast_is_deterministic(self):
        first = time_cast(**REQUEST_TIME)
        second = time_cast(**REQUEST_TIME)
        self.assertEqual(first["facts"], second["facts"])
        self.assertEqual(first["facts"]["original"]["name"], "履")


if __name__ == "__main__":
    unittest.main()

