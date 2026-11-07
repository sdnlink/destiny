"""确定性算法缺陷修复的回归护栏。

覆盖（均为纯工程/确定性缺陷，不涉及流派口径或吉凶断语）：
- 三元九运 180 年一轮回（2044 起复归上元一运），不再恒为九运；
- period 函数级 1..9 校验与 GET 端点范围约束，拒绝非法星盘/KeyError；
- 格局条件未满足时也输出带 note 的条件项，四条结构一致；
- 起运 0 岁为合法值，不被 `or 3` 吞掉；
- 神煞按 (年支, 日支) 固定顺序，输出跨进程可复现；
- 旬空委托 app.common.ganzhi.xun_info 单一真源，六十甲子逐项一致；
- 紫微纳音非法干支显式报错，不再伪装成五行局名。
"""
import unittest
from unittest import mock

from fastapi.testclient import TestClient

from app.bazi.engine import _calculate_shensha, _kong_wang_branches
from app.common.ganzhi import EARTHLY_BRANCHES, xun_info
from app.fengshui.xuankong import calculate_xuankong, period_for_year
from app.main import app
from app.ziwei.rules import get_ganzhi_nayin

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
SEXAGENARY_CYCLE = [STEMS[i % 10] + BRANCHES[i % 12] for i in range(60)]


class PeriodCycleTests(unittest.TestCase):
    def test_180_year_cycle(self):
        # 上元一运 1864 起，每运 20 年，九运 180 年后复归
        self.assertEqual(period_for_year(1864), 1)
        self.assertEqual(period_for_year(1984), 7)
        self.assertEqual(period_for_year(2026), 9)
        self.assertEqual(period_for_year(2043), 9)
        self.assertEqual(period_for_year(2044), 1)  # 新一轮上元一运
        self.assertEqual(period_for_year(2063), 1)
        self.assertEqual(period_for_year(2064), 2)
        self.assertEqual(period_for_year(2100), 3)
        self.assertEqual(period_for_year(2044 + 180), 1)

    def test_pre_1864_still_rejected(self):
        with self.assertRaises(ValueError):
            period_for_year(1863)

    def test_cycle_matches_declared_periods(self):
        from app.fengshui.xuankong import PERIODS
        for number, start, end in PERIODS:
            self.assertEqual(period_for_year(start), number)
            self.assertEqual(period_for_year(end), number)

    def test_period_validation(self):
        for bad in (0, 10, -1, 1.5, "9", True):
            with self.assertRaises(ValueError):
                calculate_xuankong("子", period=bad)
        for good in range(1, 10):
            self.assertEqual(calculate_xuankong("子", period=good)["facts"]["period"], good)

    def test_get_endpoint_range_validation(self):
        client = TestClient(app)
        self.assertEqual(client.get("/v1/fengshui/xuankong",
                                    params={"sitting_mountain": "子", "period": 10}).status_code, 422)
        self.assertEqual(client.get("/v1/fengshui/xuankong",
                                    params={"sitting_mountain": "子", "year": 2101}).status_code, 422)
        ok = client.get("/v1/fengshui/xuankong",
                        params={"sitting_mountain": "子", "year": 2044})
        self.assertEqual(ok.status_code, 200)
        self.assertEqual(ok.json()["data"]["facts"]["period"], 1)


class XuankongConditionStructureTests(unittest.TestCase):
    def test_all_four_conditions_always_present(self):
        from app.fengshui.rules import MOUNTAINS
        expected = {"旺山旺向", "上山下水", "双星到坐", "双星到向"}
        for mountain in MOUNTAINS:
            for period in range(1, 10):
                conditions = calculate_xuankong(mountain.name, period=period)["facts"]["conditions"]
                self.assertEqual({c["name"] for c in conditions}, expected)
                for c in conditions:
                    if not c["met"]:
                        self.assertIn("note", c)


class BaziDeterminismTests(unittest.TestCase):
    def test_shensha_order_is_stable(self):
        # 年支/日支分属不同三合局时，输出顺序必须按 (年支, 日支) 固定，而非 set 迭代
        first = _calculate_shensha("甲", "甲", "丙", "辛", "申", "寅", "寅", "巳")
        for _ in range(20):
            self.assertEqual(
                _calculate_shensha("甲", "甲", "丙", "辛", "申", "寅", "寅", "巳"), first
            )

    def test_kong_wang_matches_single_source(self):
        for pillar in SEXAGENARY_CYCLE:
            self.assertEqual(_kong_wang_branches(pillar),
                             set(xun_info(pillar)["empty_branches"]))
        self.assertEqual(_kong_wang_branches("甲子"), {"戌", "亥"})
        self.assertEqual(_kong_wang_branches("甲戌"), {"申", "酉"})
        self.assertTrue(_kong_wang_branches("甲子") <= set(EARTHLY_BRANCHES))


class YunStartZeroTests(unittest.TestCase):
    def test_zero_start_year_is_preserved(self):
        """真实调用 calculate_bazi：getStartYear() 返回 0 时不得被 `or 3` 改成 3。"""
        import app.bazi.engine as bazi

        class FakeYun:
            def getStartYear(self):
                return 0

            def getStartMonth(self):
                return 0

        class FakeEightChar:
            def setSect(self, _):
                return None

            def getYun(self, _):
                return FakeYun()

        class FakeLunar:
            def getEightChar(self):
                return FakeEightChar()

        class FakeSolar:
            @staticmethod
            def fromYmdHms(*args, **kwargs):
                class Inst:
                    def getLunar(self):
                        return FakeLunar()
                return Inst()

        # CalendarEngine 使用自己 import 的 Solar，故只影响起运重建路径
        with mock.patch.object(bazi, "Solar", FakeSolar):
            result = bazi.calculate_bazi("2026-02-19 12:00:00", "Asia/Shanghai")
        self.assertEqual(result["facts"]["luck_start_info"]["start_age"], 0)
        self.assertEqual(result["facts"]["luck_pillars"][0]["start_age"], 0)
        self.assertEqual(result["facts"]["luck_pillars"][1]["start_age"], 10)


class ZiweiNayinTests(unittest.TestCase):
    def test_valid_ganzhi_returns_nayin_name(self):
        self.assertEqual(get_ganzhi_nayin("甲", "子"), "海中金")
        self.assertEqual(get_ganzhi_nayin("癸", "亥"), "大海水")
        for pillar in SEXAGENARY_CYCLE:
            value = get_ganzhi_nayin(pillar[0], pillar[1])
            self.assertNotIn("局", value)  # 不得把五行局名当纳音名返回

    def test_invalid_ganzhi_raises(self):
        for stem, branch in (("X", "子"), ("甲", "Y"), ("甲", "丑")):
            with self.assertRaises(ValueError):
                get_ganzhi_nayin(stem, branch)


if __name__ == "__main__":
    unittest.main()
