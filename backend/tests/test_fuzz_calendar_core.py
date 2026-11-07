"""历法/干支核心的模糊与性质测试（测试金字塔：补充「模糊测试缺失」缺口）。

针对最基础、最易回归的干支纪年纯函数 `year_ganzhi` 建立不变式：
- 合法性（落在 60 甲子集合内、干支各自合法）
- 周期性（60 年一循环、干 10 年一循环、支 12 年一循环）
- 锚点（4 年甲子、1984 甲子、2024 甲辰、2026 丙午）
- 任意连续 60 年恰好覆盖全部 60 甲子（无重复、无遗漏）
随机大范围年份采样作为模糊验证（固定种子，可复现）。
"""
import random
import unittest

from app.bazi.liunian import year_ganzhi
from app.bazi.rules import NAYIN_TABLE
from app.common.ganzhi import HEAVENLY_STEMS, EARTHLY_BRANCHES

GANZHI_60 = frozenset(NAYIN_TABLE.keys())
assert len(GANZHI_60) == 60, "NAYIN_TABLE 应恰好覆盖 60 甲子"


class YearGanzhiPropertyTests(unittest.TestCase):
    def test_anchors(self):
        self.assertEqual(year_ganzhi(4), "甲子")
        self.assertEqual(year_ganzhi(1984), "甲子")
        self.assertEqual(year_ganzhi(2024), "甲辰")
        self.assertEqual(year_ganzhi(2025), "乙巳")
        self.assertEqual(year_ganzhi(2026), "丙午")

    def test_validity(self):
        for y in range(1900, 2101):
            gz = year_ganzhi(y)
            self.assertEqual(len(gz), 2)
            self.assertIn(gz[0], HEAVENLY_STEMS)
            self.assertIn(gz[1], EARTHLY_BRANCHES)
            self.assertIn(gz, GANZHI_60)

    def test_periodicity_60(self):
        for y in range(-2000, 3000):
            self.assertEqual(year_ganzhi(y), year_ganzhi(y + 60))

    def test_sub_periodicity(self):
        for y in range(-2000, 3000):
            self.assertEqual(year_ganzhi(y)[0], year_ganzhi(y + 10)[0])
            self.assertEqual(year_ganzhi(y)[1], year_ganzhi(y + 12)[1])

    def test_full_cycle_coverage(self):
        # 任意连续 60 年应恰好覆盖全部 60 甲子，无重复、无遗漏
        for start in range(1900, 2101 - 60):
            window = [year_ganzhi(start + i) for i in range(60)]
            self.assertEqual(len(set(window)), 60)
            self.assertEqual(set(window), GANZHI_60)

    def test_fuzz_random_years(self):
        rng = random.Random(20261107)
        for _ in range(5000):
            y = rng.randint(-100000, 100000)
            gz = year_ganzhi(y)
            self.assertIn(gz, GANZHI_60)
            # 周期性模糊：随机偏移 60 的整数倍不变
            k = rng.randint(-100, 100)
            self.assertEqual(year_ganzhi(y), year_ganzhi(y + 60 * k))


if __name__ == "__main__":
    unittest.main()
