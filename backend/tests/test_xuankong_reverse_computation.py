"""替星表与中宫五的「逆行计算」回归护栏。

依据库内《沈氏玄空學》「起星图二百一十六局」原文（data/generated/
wikisource-corpus/corpus_chunks.jsonl）解析出的 422 条「到星→入中星」实例。
下表为原典统计（同一到星在不同元龙下可有不同入中星）：

    到星1 -> {1, 2}      子/癸贪狼1、壬巨门2
    到星2 -> {2, 1}      坤/未巨门2、申贪狼1
    到星3 -> {2, 1}      卯/乙巨门2、甲贪狼1
    到星4 -> {6}         辰巽巳武曲6
    到星5 -> {5}         48 例「无替可寻」→ 不替、仍五入中
    到星6 -> {6}         戌乾亥武曲6
    到星7 -> {7, 9}      酉/辛破军7、庚弼星9
    到星8 -> {7, 9}      艮/丑破军7、寅弼星9
    到星9 -> {9, 7}      午/丁弼星9、丙破军7

关键裁定：到星 7/8/9 中「入中9」的 14/15/32 例只能由寅午庚丁=9（右弼）
产生；若误用工程草稿 8（左辅），实现将出现原典没有的「入中8」组合。
"""
import unittest
from collections import defaultdict

from app.fengshui.rules import MOUNTAINS
from app.fengshui.xuankong import TIHUA_STAR, calculate_xuankong

# 库内起星图 216 局逆行统计（原典明文频次；OCR 缺字导致的少量缺额在实现侧补全）
CLASSIC_ENTERING = {
    1: {1, 2}, 2: {2, 1}, 3: {2, 1}, 4: {6}, 5: {5},
    6: {6}, 7: {7, 9}, 8: {7, 9}, 9: {9, 7},
}


class ReverseComputationTests(unittest.TestCase):
    def _observed(self):
        observed = defaultdict(lambda: defaultdict(int))
        no_sub = 0
        for mountain in MOUNTAINS:
            for period in range(1, 10):
                t = calculate_xuankong(mountain.name, period=period,
                                       include_tihua_chart=True)["facts"]["tihua_chart"]
                for side in ("sitting", "facing"):
                    e = t[side]
                    self.assertEqual(e["status"], "completed")
                    observed[e["arriving_star"]][e["tihua_star"]] += 1
                    if e.get("no_substitute"):
                        no_sub += 1
        return observed, no_sub

    def test_every_implemented_pair_exists_in_classic_cases(self):
        observed, _ = self._observed()
        for arriving, targets in observed.items():
            self.assertEqual(set(targets), CLASSIC_ENTERING[arriving],
                             "到星%s 的入中星集合与原典不符" % arriving)

    def test_no_left_auxiliary_8_in_entering_results(self):
        # 原典 216 局从未出现「入中8」；工程草稿误值 8 会立刻暴露
        observed, _ = self._observed()
        for arriving, targets in observed.items():
            self.assertNotIn(8, targets, "到星%s 出现原典没有的入中8" % arriving)

    def test_frequency_structure_matches_classic(self):
        # 原典频次结构：每组主/次约 32/16（五与六恒 48），实现为 24山×9运×2路
        observed, no_sub = self._observed()
        self.assertEqual(no_sub, 48)  # 到星5 共 48 例，全部不替
        for arriving in (4, 5, 6):
            self.assertEqual(observed[arriving], {CLASSIC_ENTERING[arriving].copy().pop(): 48})
        for arriving in (1, 2, 3, 7, 8, 9):
            counts = sorted(observed[arriving].values())
            self.assertEqual(counts, [16, 32], "到星%s 频次异常" % arriving)

    def test_tihua_star_table_is_classic_bishop_nine(self):
        for name in ("寅", "午", "庚", "丁"):
            self.assertEqual(TIHUA_STAR[name], 9)
        self.assertEqual(set(TIHUA_STAR.values()), {1, 2, 6, 7, 9})
        self.assertNotIn(8, TIHUA_STAR.values())


if __name__ == "__main__":
    unittest.main()
