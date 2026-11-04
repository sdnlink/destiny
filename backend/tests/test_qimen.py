import unittest
from fastapi.testclient import TestClient

from app.main import app
from app.qimen import calculate_qimen_chart
from app.qimen.rules import evaluate_qimen_patterns


class QimenTests(unittest.TestCase):
    def test_qimen_natal_chart_generation(self):
        # 2026-08-15 16:00 (立秋节气后，丙午年 丙申月 辛酉日 丙申时)
        result = calculate_qimen_chart("2026-08-15T16:00:00")

        self.assertEqual(result["system"], "qimen")
        self.assertIn("dun_type", result)
        self.assertIn(result["dun_type"], ["阳遁", "阴遁"])
        self.assertTrue(1 <= result["ju_number"] <= 9)
        self.assertIn(result["yuan_type"], ["上元", "中元", "下元"])

        # 检查值符星与值使门
        self.assertTrue(result["zhi_fu_star"].startswith("天"))
        self.assertTrue(result["zhi_shi_gate"].endswith("门"))
        self.assertTrue(1 <= result["zhi_fu_palace"] <= 9)
        self.assertTrue(1 <= result["zhi_shi_palace"] <= 9)

        # 检查九宫完整性
        palaces = result["palaces"]
        self.assertEqual(len(palaces), 9)

        for p_num in range(1, 10):
            p = palaces[p_num]
            self.assertEqual(p["palace_number"], p_num)
            self.assertTrue(len(p["di_pan_stem"]) > 0)
            self.assertTrue(len(p["tian_pan_stem"]) > 0)
            self.assertTrue(len(p["nine_star"]) > 0)
            self.assertTrue(len(p["eight_gate"]) > 0)
            self.assertTrue(len(p["eight_spirit"]) > 0)

        # 检查吉方研判
        favs = result["favorable_directions"]
        self.assertTrue(len(favs) > 0)
        self.assertIn(favs[0]["gate"], ["开门", "休门", "生门"])

    def test_qimen_pattern_evaluation(self):
        # 戊加丙 (青龙返首)
        p1 = evaluate_qimen_patterns("戊", "丙", "开门", "天心", "值符")
        self.assertTrue(any(pat["name"] == "青龙返首" for pat in p1))

        # 丙加戊 (飞鸟跌穴)
        p2 = evaluate_qimen_patterns("丙", "戊", "休门", "天任", "九天")
        self.assertTrue(any(pat["name"] == "飞鸟跌穴" for pat in p2))

        # 天遁 (丙加丁临生门)
        p3 = evaluate_qimen_patterns("丙", "丁", "生门", "天辅", "太阴")
        self.assertTrue(any(pat["name"] == "天遁" for pat in p3))

    def test_qimen_api_endpoints(self):
        client = TestClient(app)

        # /v1/qimen/time
        res_time = client.post("/v1/qimen/time", json={
            "local_datetime": "2026-08-15T16:00:00",
            "timezone": "Asia/Shanghai"
        })
        self.assertEqual(res_time.status_code, 200)
        data_time = res_time.json()["data"]
        self.assertEqual(data_time["system"], "qimen")

        # /v1/qimen/auto
        res_auto = client.post("/v1/qimen/auto", json={
            "local_datetime": "2026-08-15T16:00:00",
            "timezone": "Asia/Shanghai",
            "cast_nonce": "testnonceqimen123456"
        })
        self.assertEqual(res_auto.status_code, 200)
        data_auto = res_auto.json()["data"]
        self.assertEqual(data_auto["system"], "qimen")

        # /v1/calculations/evaluate
        res_eval = client.post("/v1/calculations/evaluate", json={
            "module": "qimen",
            "method": "time",
            "input": {
                "local_datetime": "2026-08-15T16:00:00",
                "timezone": "Asia/Shanghai"
            }
        })
        self.assertEqual(res_eval.status_code, 200)
        data_eval = res_eval.json()["data"]
        self.assertEqual(data_eval["module"], "qimen")
        self.assertEqual(data_eval["status"], "completed")


if __name__ == "__main__":
    unittest.main()
