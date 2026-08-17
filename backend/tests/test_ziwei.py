import unittest
from datetime import datetime
from app.ziwei.engine import calculate_ziwei_chart, time_cast, auto_cast
from app.ziwei.rules import SIHUA_TABLE, NAYIN_ELEMENT_BUREAU, get_ganzhi_nayin


class ZiweiTests(unittest.TestCase):
    def test_standard_ziwei_natal_chart(self):
        # 2024-02-10 10:00 (甲辰年 正月初一 巳时)
        result = calculate_ziwei_chart("2024-02-10T10:00:00", gender="男")
        
        self.assertEqual(result["four_pillars"]["year"], "甲辰")
        self.assertEqual(result["yin_yang_gender"], "阳男")
        self.assertTrue(result["is_forward_decade"])
        
        # 12 palaces present
        self.assertEqual(len(result["palaces_by_order"]), 12)
        self.assertEqual(len(result["palaces_by_branch"]), 12)
        
        # Check Ming and Shen palaces
        ming_palace = next(p for p in result["palaces_by_order"] if p["name"] == "命宫")
        self.assertIsNotNone(ming_palace)
        self.assertIn(ming_palace["earthly_branch"], ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"])
        
        # Bureau present
        self.assertIn("局", result["bureau"]["name"])
        self.assertIn(result["bureau"]["number"], [2, 3, 4, 5, 6])
        
        # Si Hua of Jia year: 廉贞禄, 破军权, 武曲科, 太阳忌
        self.assertEqual(result["si_hua"]["化禄"], "廉贞")
        self.assertEqual(result["si_hua"]["化权"], "破军")
        self.assertEqual(result["si_hua"]["化科"], "武曲")
        self.assertEqual(result["si_hua"]["化忌"], "太阳")

    def test_gender_polarity_and_decade_direction(self):
        # 乙巳年 (阴年)
        chart_female = calculate_ziwei_chart("2025-05-15T14:00:00", gender="女")
        self.assertEqual(chart_female["yin_yang_gender"], "阴女")
        self.assertTrue(chart_female["is_forward_decade"])  # 阴女顺行

        chart_male = calculate_ziwei_chart("2025-05-15T14:00:00", gender="男")
        self.assertEqual(chart_male["yin_yang_gender"], "阴男")
        self.assertFalse(chart_male["is_forward_decade"])  # 阴男逆行

    def test_all_fourteen_main_stars_distributed(self):
        result = calculate_ziwei_chart("2026-08-15T16:00:00", gender="男")
        all_main_stars = []
        for p in result["palaces_by_order"]:
            for st in p["main_stars"]:
                all_main_stars.append(st["name"])
        
        expected_14_stars = {
            "紫微", "天机", "太阳", "武曲", "天同", "廉贞",
            "天府", "太阴", "贪狼", "巨门", "天相", "天梁", "七杀", "破军"
        }
        self.assertEqual(set(all_main_stars), expected_14_stars)
        self.assertEqual(len(all_main_stars), 14)

    def test_time_cast_contract(self):
        cast = time_cast("2026-08-15T16:00:00", gender="女")
        self.assertEqual(cast["status"], "deterministic_derivation_complete")
        self.assertEqual(cast["engine_version"], "ziwei-engine-1.0.0")
        self.assertEqual(len(cast["steps"]), 4)
        self.assertIn("ZW-STARS-001", cast["rule_ids"])
        self.assertIn("palaces_by_branch", cast["facts"])


if __name__ == "__main__":
    unittest.main()
