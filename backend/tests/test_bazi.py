import unittest
from fastapi.testclient import TestClient

from app.bazi import calculate_bazi
from app.bazi.rules import (
    get_ten_god,
    get_twelve_stage,
)
from app.main import app


class BaZiTests(unittest.TestCase):
    def test_ten_gods_relationships(self):
        # 甲木 (阳木) 对各天干
        self.assertEqual(get_ten_god("甲", "甲"), "比肩")
        self.assertEqual(get_ten_god("甲", "乙"), "劫财")
        self.assertEqual(get_ten_god("甲", "丙"), "食神")
        self.assertEqual(get_ten_god("甲", "丁"), "伤官")
        self.assertEqual(get_ten_god("甲", "戊"), "偏财")
        self.assertEqual(get_ten_god("甲", "己"), "正财")
        self.assertEqual(get_ten_god("甲", "庚"), "七杀")
        self.assertEqual(get_ten_god("甲", "辛"), "正官")
        self.assertEqual(get_ten_god("甲", "壬"), "偏印")
        self.assertEqual(get_ten_god("甲", "癸"), "正印")

    def test_twelve_changsheng_stages(self):
        # 甲木长生在亥顺行
        self.assertEqual(get_twelve_stage("甲", "亥"), "长生")
        self.assertEqual(get_twelve_stage("甲", "子"), "沐浴")
        self.assertEqual(get_twelve_stage("甲", "寅"), "临官")
        self.assertEqual(get_twelve_stage("甲", "卯"), "帝旺")
        self.assertEqual(get_twelve_stage("甲", "辰"), "衰")
        self.assertEqual(get_twelve_stage("甲", "未"), "墓")

        # 乙木长生在午逆行
        self.assertEqual(get_twelve_stage("乙", "午"), "长生")
        self.assertEqual(get_twelve_stage("乙", "巳"), "沐浴")
        self.assertEqual(get_twelve_stage("乙", "卯"), "临官")
        self.assertEqual(get_twelve_stage("乙", "寅"), "帝旺")
        self.assertEqual(get_twelve_stage("乙", "戌"), "墓")

    def test_bazi_natal_chart_generation(self):
        # 2026-08-15 16:00 (丙午年 丙申月 辛亥日 丙申时)
        result = calculate_bazi("2026-08-15T16:00:00", gender="男")

        self.assertEqual(result["system"], "bazi")
        self.assertEqual(result["day_master"], "辛")
        self.assertIn("pillars", result["facts"])

        pillars = result["facts"]["pillars"]
        self.assertIn("year", pillars)
        self.assertIn("month", pillars)
        self.assertIn("day", pillars)
        self.assertIn("hour", pillars)

        # 检查各柱十神、长生与纳音
        day_p = pillars["day"]
        self.assertEqual(day_p["stem_ten_god"], "日元")
        self.assertEqual(day_p["ganzhi"], "辛酉")
        self.assertEqual(day_p["nayin"], "石榴木")

        # 检查藏干
        self.assertTrue(len(day_p["hidden_stems"]) > 0)
        self.assertTrue(all("ten_god" in h for h in day_p["hidden_stems"]))

        # 检查五行与强弱评估
        strength = result["day_master_strength"]
        self.assertEqual(strength["day_master"], "辛")
        self.assertEqual(strength["element"], "金")
        self.assertIn(strength["level"], ["极弱", "偏弱", "中和", "偏旺", "极旺"])
        self.assertTrue(len(strength["favorable_elements"]) > 0)
        self.assertTrue(len(strength["unfavorable_elements"]) > 0)

        # 检查大运
        luck = result["luck_pillars"]
        self.assertEqual(len(luck), 8)
        self.assertTrue(luck[0]["start_age"] > 0)
        self.assertTrue(luck[0]["ganzhi"] != "")
        self.assertIn("stem_ten_god", luck[0])

    def test_bazi_gender_polarity_luck_cycles(self):
        # 2024年甲辰 (阳干年)
        male_res = calculate_bazi("2024-06-01T12:00:00", gender="男")
        self.assertEqual(male_res["luck_start_info"]["direction"], "顺行")

        female_res = calculate_bazi("2024-06-01T12:00:00", gender="女")
        self.assertEqual(female_res["luck_start_info"]["direction"], "逆行")

    def test_luck_start_year_carries_start_month(self):
        """起运是「X 岁 Y 个月」，跨年月份必须进位到实际交运年。"""
        result = calculate_bazi("1984-12-20T10:00:00", gender="男")
        info = result["luck_start_info"]
        self.assertEqual(info["start_age"], 5)
        self.assertEqual(info["start_month"], 5)
        # 1984-12 + 5 岁 5 个月 = 1990-05，而不是只加 5 年的 1989。
        self.assertEqual(info["start_year"], 1990)
        self.assertEqual(info["start_actual_month"], 5)
        self.assertEqual(result["luck_pillars"][0]["start_year"], 1990)
        self.assertEqual(result["luck_pillars"][0]["end_year"], 1999)
        self.assertEqual(result["luck_pillars"][1]["start_year"], 2000)

    def test_bazi_accepts_male_alias(self):
        """性别写 M/male 时不能按女性顺逆与 getYun 各算一套。"""
        result = calculate_bazi("2024-06-01T12:00:00", gender="male")
        self.assertEqual(result["facts"]["gender"], "男")
        self.assertEqual(result["luck_start_info"]["direction"], "顺行")

    def test_bazi_api_endpoints(self):
        client = TestClient(app)

        # /v1/bazi/time
        res_time = client.post("/v1/bazi/time", json={
            "local_datetime": "2026-08-15T16:00:00",
            "timezone": "Asia/Shanghai",
            "gender": "男"
        })
        self.assertEqual(res_time.status_code, 200)
        data_time = res_time.json()["data"]
        self.assertEqual(data_time["day_master"], "辛")

        # /v1/bazi/auto
        res_auto = client.post("/v1/bazi/auto", json={
            "local_datetime": "2026-08-15T16:00:00",
            "timezone": "Asia/Shanghai",
            "gender": "女",
            "cast_nonce": "testnoncetestnonce12345"
        })
        self.assertEqual(res_auto.status_code, 200)
        data_auto = res_auto.json()["data"]
        self.assertEqual(data_auto["gender"], "女")

        # /v1/calculations/evaluate
        res_eval = client.post("/v1/calculations/evaluate", json={
            "module": "bazi",
            "method": "time",
            "input": {
                "local_datetime": "2026-08-15T16:00:00",
                "timezone": "Asia/Shanghai",
                "gender": "男"
            }
        })
        self.assertEqual(res_eval.status_code, 200)
        data_eval = res_eval.json()["data"]
        self.assertEqual(data_eval["module"], "bazi")
        self.assertEqual(data_eval["status"], "completed")


if __name__ == "__main__":
    unittest.main()
