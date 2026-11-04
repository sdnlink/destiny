"""钉住"由已有盘面数据确定推出"的派生结论。

覆盖：奇门时旬空落宫与驿马、紫微三方四正、八字财星喜忌。
这些结论只依赖排盘结果与固定对照表，不涉及断语取舍。
"""
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.bazi.engine import calculate_bazi
from app.bazi.rules import ELEMENT_OVERCOMING
from app.common.ganzhi import EARTHLY_BRANCHES, triple_group_of
from app.qimen.engine import calculate_qimen_chart
from app.qimen.rules import HORSE_STAR, PALACE_BRANCHES
from app.ziwei.engine import calculate_ziwei_chart
from app.ziwei.rules import XIAN_CHI_TABLE


MOMENT = "2026-08-15T16:00:00"
TIMEZONE = "Asia/Shanghai"


class QimenDerivedConclusionTests(unittest.TestCase):
    def setUp(self):
        self.result = calculate_qimen_chart(MOMENT, TIMEZONE)

    def test_xun_and_void_palaces_are_consistent(self):
        xun = self.result["xun"]
        void = self.result["void"]
        self.assertEqual(void["empty_branches"], xun["empty_branches"])
        expected = [
            palace for palace, branches in PALACE_BRANCHES.items()
            if any(branch in xun["empty_branches"] for branch in branches)
        ]
        self.assertEqual(void["palace_numbers"], expected)
        for palace in self.result["palaces"].values():
            self.assertEqual(palace["is_void"], palace["palace_number"] in expected)

    def test_horse_star_follows_hour_branch_triple_group(self):
        hour_branch = self.result["ganzhi"]["hour"][1]
        horse = self.result["horse_star"]
        self.assertEqual(horse["branch"], HORSE_STAR[hour_branch])
        # 驿马取三合局的对冲位，必然不落在本局三支之内
        self.assertNotIn(horse["branch"], triple_group_of(hour_branch))
        self.assertEqual(
            horse["palace_numbers"],
            [palace for palace, branches in PALACE_BRANCHES.items() if horse["branch"] in branches],
        )
        for palace in self.result["palaces"].values():
            self.assertEqual(palace["is_horse"], palace["palace_number"] in horse["palace_numbers"])

    def test_void_and_horse_never_land_on_center_palace(self):
        self.assertNotIn(5, self.result["void"]["palace_numbers"])
        self.assertNotIn(5, self.result["horse_star"]["palace_numbers"])


class ZiweiDerivedConclusionTests(unittest.TestCase):
    def setUp(self):
        self.result = calculate_ziwei_chart(MOMENT, TIMEZONE, "男")
        self.palaces = self.result["palaces_by_order"]

    def test_every_palace_has_self_plus_trine_and_opposition(self):
        branches = [palace["earthly_branch"] for palace in self.palaces]
        self.assertEqual(len(set(branches)), 12)
        for palace in self.palaces:
            index = EARTHLY_BRANCHES.index(palace["earthly_branch"])
            expected_trine = [
                palace["earthly_branch"],
                EARTHLY_BRANCHES[(index + 4) % 12],
                EARTHLY_BRANCHES[(index + 8) % 12],
            ]
            self.assertEqual(palace["san_fang_branches"], expected_trine)
            self.assertEqual(palace["dui_gong_branch"], EARTHLY_BRANCHES[(index + 6) % 12])
            self.assertEqual(palace["si_zheng_branches"], expected_trine + [palace["dui_gong_branch"]])

    def test_trine_never_contains_self_twice(self):
        for palace in self.palaces:
            self.assertEqual(palace["san_fang_branches"].count(palace["earthly_branch"]), 1)
            self.assertEqual(len(set(palace["si_zheng_branches"])), 4)


class ZiweiMinorStarTests(unittest.TestCase):
    def setUp(self):
        self.result = calculate_ziwei_chart(MOMENT, TIMEZONE, "男")
        self.star_branch = {}
        for palace in self.result["palaces_by_branch"]:
            for star in palace["minor_stars"]:
                self.star_branch[star["name"]] = palace["earthly_branch"]
        self.year_branch = self.result["four_pillars"]["year"][1]
        self.lunar_month = abs(self.result["lunar_calendar"]["lunar_month"])

    def test_five_minor_stars_follow_standard_formulas(self):
        year_index = EARTHLY_BRANCHES.index(self.year_branch)
        expected = {
            "红鸾": EARTHLY_BRANCHES[(3 - year_index) % 12],
            "天喜": EARTHLY_BRANCHES[(3 - year_index + 6) % 12],
            "天刑": EARTHLY_BRANCHES[(9 + self.lunar_month - 1) % 12],
            "天姚": EARTHLY_BRANCHES[(1 + self.lunar_month - 1) % 12],
            "咸池": XIAN_CHI_TABLE[self.year_branch],
        }
        self.assertEqual(self.star_branch, expected)

    def test_tianxi_is_opposite_palace_of_hongluan(self):
        index = EARTHLY_BRANCHES.index(self.star_branch["红鸾"])
        self.assertEqual(EARTHLY_BRANCHES[(index + 6) % 12], self.star_branch["天喜"])


class BaziDerivedConclusionTests(unittest.TestCase):
    def setUp(self):
        self.result = calculate_bazi(MOMENT, TIMEZONE, "男")

    def test_wealth_advisory_uses_controlled_element(self):
        strength = self.result["day_master_strength"]
        wealth_element = ELEMENT_OVERCOMING[strength["element"]]
        advisory = self.result["advisory"]["wealth"]
        self.assertIn("财星属{}".format(wealth_element), advisory)
        self.assertNotEqual(advisory, "求财以稳健为主，命中喜用五行为生财之源，利于把握专业技能与长期积累带来的收益机会。")

    def test_wealth_advisory_reflects_favorable_or_unfavorable(self):
        strength = self.result["day_master_strength"]
        wealth_element = ELEMENT_OVERCOMING[strength["element"]]
        advisory = self.result["advisory"]["wealth"]
        if wealth_element in strength["favorable_elements"]:
            self.assertIn("喜用", advisory)
        elif wealth_element in strength["unfavorable_elements"]:
            self.assertIn("忌神", advisory)
        else:
            self.assertIn("喜忌均不显", advisory)


if __name__ == "__main__":
    unittest.main()
