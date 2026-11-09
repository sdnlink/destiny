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

    def test_host_response_are_two_lines_apart_for_all_64(self):
        # 京房八宫世应诀：世应恒相隔二爻（应 = (世+2) % 6 + 1）。
        for bits, palace in PALACE_BY_LINES.items():
            self.assertIn(palace.host_line, range(1, 7))
            self.assertEqual(palace.response_line, (palace.host_line + 2) % 6 + 1)

    def test_jiji_kan_third_stage_najia(self):
        # 水火既济：离(3)下 坎(6)上 -> 坎宫三世（世三应六）。
        # 纳甲：离内卦卯丑亥、坎外卦申戌子；六亲以坎宫水为「我」。
        result = number_cast(3, 6, **REQUEST_TIME)
        facts = result["facts"]
        self.assertEqual(facts["original"]["name"], "既济")
        self.assertEqual(facts["palace"]["name"], "坎")
        self.assertEqual(facts["palace"]["stage"], "三世")
        self.assertEqual(facts["palace"]["host_line"], 3)
        self.assertEqual(facts["palace"]["response_line"], 6)
        self.assertEqual(
            [line["najia_branch"] for line in facts["line_chart"]],
            ["卯", "丑", "亥", "申", "戌", "子"],
        )
        self.assertEqual(
            [line["six_relative"] for line in facts["line_chart"]],
            ["子孙", "官鬼", "兄弟", "父母", "官鬼", "兄弟"],
        )


if __name__ == "__main__":
    unittest.main()

