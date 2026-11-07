"""八字神煞补全测试：三煞（劫煞/灾煞/岁煞）、亡神、空亡（旬空）。

验证范围为确定性口诀推导（非吉凶断语）：
- 劫煞/灾煞/岁煞/亡神随年支或日支的三合局元素定位；
- 空亡（旬空）随日柱干支所在旬定位。
用例干支均按通行口诀手工核对。
"""
import unittest

from app.bazi.engine import _calculate_shensha, _kong_wang_branches


class BaZiShenshaSupplementTests(unittest.TestCase):
    # 年甲子 / 月丙寅 / 日庚午 / 时辛巳
    # 年支子→水局(劫巳/灾午/岁未/亡亥)；日支午→火局(劫亥/灾子/岁丑/亡巳)
    def test_three_sha_and_wang_shen(self):
        sh = _calculate_shensha("庚", "甲", "丙", "辛", "子", "寅", "午", "巳")
        # 时支巳：水局劫煞 + 火局亡神
        self.assertIn("劫煞", sh["hour"])
        self.assertIn("亡神", sh["hour"])
        # 日支午：水局灾煞 + 火局将星
        self.assertIn("灾煞", sh["day"])
        self.assertIn("将星", sh["day"])
        # 年支子：水局将星 + 火局灾煞
        self.assertIn("灾煞", sh["year"])
        self.assertIn("将星", sh["year"])
        # 岁煞按三合局落点（水局岁未、火局岁丑）不应出现在巳/午/子
        self.assertNotIn("岁煞", sh["hour"])
        self.assertNotIn("岁煞", sh["day"])
        self.assertNotIn("岁煞", sh["year"])

    def test_kong_wang(self):
        # 甲子旬戌亥空；甲戌旬申酉空；庚午同在甲子旬（戌亥空）
        self.assertEqual(_kong_wang_branches("甲子"), {"戌", "亥"})
        self.assertEqual(_kong_wang_branches("甲戌"), {"申", "酉"})
        self.assertEqual(_kong_wang_branches("庚午"), {"戌", "亥"})

    def test_kong_wang_integration(self):
        # 日柱甲子（旬空戌亥），年支亥 -> 年柱空亡
        sh = _calculate_shensha("甲", "甲", "丙", "辛", "亥", "寅", "子", "巳")
        self.assertIn("空亡", sh["year"])


if __name__ == "__main__":
    unittest.main()
