"""据库内古籍原文 + 历法逆行计算修复的八项算法回归护栏。

原典依据（均可在 data/generated/wikisource-corpus 检索）：
- 《六壬指南》：月将按中气换将（「正月雨水后日躔娵訾之次入亥宫，乃登明将」）。
- 《紫微斗數全書·安大限诀》：「阳男阴女从命前一宫起顺行，是父母宫；
  阴男阳女从命后一宫起逆行，是兄弟宫」。
- 《沈氏玄空學·論起星》：「兼一二分者，无须寻替；若兼三四分者，当用替星」；
  起星图实例「八之天元为艮，艮丙辛位位是破军，故以七入中」。
- 《遁甲演義》：「直使在五官，寄坤二官」。
- 《卜筮正宗·旬空论第十》：「不过待其出旬、值日…填补之法」；
  占验「应于丑日者出旬之日也」「后果验未月者实空之月也」。
- 《卜筮正宗·伏神正传第六》「伏待出露」、黄金策「空下伏神易于引拔」、
  飞伏生克吉凶歌「伏克飞神为出暴，飞来克伏反伤身」。
- 《卜筮正宗》「合待冲开」「墓中人，不冲不发」。
"""
import unittest

from app.bazi.engine import calculate_bazi
from app.common.ganzhi import xun_info
from app.daliuren.engine import time_cast as liuren_cast
from app.fengshui.xuankong import calculate_xuankong
from app.liuyao import advanced
from app.liuyao.engine import _branch_structures, line_cast, void_fill_prospects
from app.qimen.engine import time_cast as qimen_cast
from app.ziwei.engine import calculate_ziwei_chart

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
CYCLE = [STEMS[i % 10] + BRANCHES[i % 12] for i in range(60)]


class MonthGeneralTests(unittest.TestCase):
    def test_zhongqi_boundary_from_classic(self):
        # 《六壬指南》春分后改用河魁(戌)将，之前仍登明(亥)将
        for dt, name, term in (
            ("2026-02-18 12:00", "登明", "雨水"),
            ("2026-03-19 12:00", "登明", "雨水"),
            ("2026-03-21 12:00", "河魁", "春分"),
        ):
            mg = liuren_cast(dt, "Asia/Shanghai")["facts"]["month_general"]
            self.assertEqual((mg["name"], mg["boundary_term"]), (name, term))

    def test_uses_solar_term_reference_time(self):
        mg = liuren_cast("2026-02-19 23:30:00", "Asia/Shanghai",
                         longitude=75.0, use_true_solar_time=True)["facts"]["month_general"]
        # 真太阳时修正后参考时应早于原始 23:30，且中气基准与四柱同源
        self.assertIn("reference_datetime", mg)
        self.assertLess(mg["reference_datetime"][11:19], "23:30:00")


class BaziSourceConsistencyTests(unittest.TestCase):
    def test_true_solar_time_uses_effective_datetime(self):
        # 2026-02-19 01:00 在东经 75° 真太阳时下回退约 3 小时跨到前一日，
        # 距节令天数改变 → 起运岁数 4 → 5。早先按未修正时刻重建，两者会相同。
        plain = calculate_bazi("2026-02-19 01:00:00", "Asia/Shanghai")
        true_solar = calculate_bazi("2026-02-19 01:00:00", "Asia/Shanghai",
                                    longitude=75.0, use_true_solar_time=True)
        self.assertEqual(plain["facts"]["luck_start_info"]["start_age"], 4)
        self.assertEqual(true_solar["facts"]["luck_start_info"]["start_age"], 5)


class TiPuBoundaryTests(unittest.TestCase):
    def test_three_degrees_is_in_ti_pu_region(self):
        # 《論起星》兼三四分当用替星：恰 3.0 度边界归属起替
        for degree, expected in ((0.0, False), (7.5, True), (10.5, True), (180.0, False)):
            tp = calculate_xuankong("午", period=9, sitting_degree=degree)["facts"]["ti_pu"]
            self.assertEqual(tp["in_ti_pu_region"], expected, degree)

    def test_degree_mountain_consistency(self):
        tp = calculate_xuankong("午", period=9, sitting_degree=180.0)["facts"]["ti_pu"]
        self.assertEqual(tp["degree_mountain"], "午")
        self.assertTrue(tp["degree_matches_sitting_mountain"])
        bad = calculate_xuankong("午", period=9, sitting_degree=90.0)
        self.assertFalse(bad["facts"]["ti_pu"]["degree_matches_sitting_mountain"])
        self.assertTrue(any("复测" in w for w in bad["warnings"]))


class QimenMiddlePalaceTests(unittest.TestCase):
    def test_zhi_shi_never_lands_in_middle_palace(self):
        # 《遁甲演義》中五寄坤二：值使门不得落中五宫
        for day in range(1, 29):
            for hour in (0, 6, 12, 18):
                f = qimen_cast("2026-04-%02d %02d:00:00" % (day, hour),
                               "Asia/Shanghai")["facts"]
                self.assertNotEqual(f["zhi_shi_palace"], 5)
                self.assertIn(f["zhi_shi_palace"], (1, 2, 3, 4, 6, 7, 8, 9))


class ZiweiDecadeDirectionTests(unittest.TestCase):
    def test_forward_starts_at_parents_palace(self):
        # 阳男顺行：命宫第一限，父母宫第二限，兄弟宫最后一限
        r = calculate_ziwei_chart("2024-02-10T10:00:00", gender="男")
        self.assertTrue(r["is_forward_decade"])
        p = {x["name"]: x for x in r["palaces_by_order"]}
        self.assertEqual(p["父母宫"]["major_limit_start"], p["命宫"]["major_limit_start"] + 10)
        self.assertEqual(p["兄弟宫"]["major_limit_start"], p["命宫"]["major_limit_start"] + 110)

    def test_backward_starts_at_siblings_palace(self):
        # 阴男逆行：命宫第一限，兄弟宫第二限，父母宫最后一限
        r = calculate_ziwei_chart("2025-05-15T14:00:00", gender="男")
        self.assertFalse(r["is_forward_decade"])
        p = {x["name"]: x for x in r["palaces_by_order"]}
        self.assertEqual(p["兄弟宫"]["major_limit_start"], p["命宫"]["major_limit_start"] + 10)
        self.assertEqual(p["父母宫"]["major_limit_start"], p["命宫"]["major_limit_start"] + 110)


class VoidFillProspectTests(unittest.TestCase):
    def test_classic_case_chou_day_is_xun_exit(self):
        # 《卜筮正宗》「应于丑日者出旬之日也」：癸亥(甲寅旬,空子丑)
        # → 甲子(1日)、乙丑(2日)
        x = xun_info("癸亥")
        self.assertEqual(x["empty_branches"], ["子", "丑"])
        pr = void_fill_prospects("癸亥", x["empty_branches"])
        self.assertEqual([e["fill_day_pillar"] for e in pr], ["甲子", "乙丑"])
        self.assertEqual([e["days_from_now"] for e in pr], [1, 2])

    def test_all_sixty_pillars_have_exit_fill(self):
        for pillar in CYCLE:
            x = xun_info(pillar)
            pr = void_fill_prospects(pillar, x["empty_branches"])
            self.assertEqual(len(pr), 2)
            for e in pr:
                self.assertEqual(e["phase"], "出旬值日")
                self.assertIsNotNone(e["fill_day_pillar"])
                self.assertTrue(1 <= e["days_from_now"] <= 12, (pillar, e))
                # 值日必须已出旬：不早于下一旬首
                self.assertGreaterEqual(e["days_from_now"], 10 - (CYCLE.index(pillar) % 10))

    def test_no_fake_tianshi_state(self):
        r = line_cast([9, 7, 7, 7, 7, 7], "2026-02-19 12:00:00", "Asia/Shanghai")
        self.assertFalse(any(line["void_state"] == "填实" for line in r["facts"]["line_chart"]))
        self.assertEqual(len(r["facts"]["void_fill_prospects"]), 2)


class HiddenEmergeTests(unittest.TestCase):
    def test_blockers_based_on_hidden_and_flying_relation(self):
        r = line_cast([9, 7, 7, 7, 7, 7], "2026-02-19 12:00:00", "Asia/Shanghai")
        cov = r["facts"]["hidden_flying_spirits"]
        for hidden in cov["hidden_spirits"]:
            self.assertIn("emerge_blockers", hidden)
            self.assertIn("can_emerge", hidden)
            # blocker 类型只应是伏神自身状态或飞伏关系，不得出现旧的暗动/日克伪描述
            for b in hidden["emerge_blockers"]:
                self.assertIn(b["type"], ("旬空", "月破", "日破", "月克",
                                         "飞克伏", "伏生飞", "引出"))

    def test_void_host_easy_to_draw_out(self):
        # 《黄金策》「空下伏神易于引拔」：飞神值旬空应给出「引出」而非阻碍
        coverage = {"hidden_spirits": [{
            "najia_branch": "午", "element": "火", "position": 2,
            "flying_spirit": {"najia_branch": "戌", "najia_stem": "甲", "element": "土"},
            "relation": "伏生飞",
        }]}
        advanced.annotate_hidden_emerge(coverage, [], "卯", "子", "木", ["戌", "亥"])
        types = [b["type"] for b in coverage["hidden_spirits"][0]["emerge_blockers"]]
        self.assertIn("引出", types)


class SanheTombTests(unittest.TestCase):
    @staticmethod
    def _lines(branches, moving_all=True):
        return [
            {"position": i, "najia_branch": b, "is_moving": moving_all,
             "void_state": "", "is_month_break": False, "is_dark_move": False,
             "month_strength": "旺"}
            for i, b in enumerate(branches, 1)
        ]

    def test_full_moving_has_no_pending_stir(self):
        lines = self._lines(("申", "子", "辰", "午", "戌", "寅"))
        st = _branch_structures(["申", "子", "辰"], "巳", "酉")
        a = advanced.assess_sanhe_conditions(st, lines)
        self.assertEqual(a[0]["status"], "成局")
        self.assertFalse(any("待冲开" in c for c in a[0]["conditions"]))

    def test_static_tomb_member_needs_stir(self):
        lines = self._lines(("申", "子", "辰", "午", "戌", "寅"))
        lines[2]["is_moving"] = False
        st = _branch_structures(["申", "子"], "辰", "酉")
        a = advanced.assess_sanhe_conditions(st, lines)
        self.assertTrue(any("待冲开" in c for c in a[0]["conditions"]))


if __name__ == "__main__":
    unittest.main()
