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

    def test_qimen_result_exposes_facts_for_plate_pipeline(self):
        """奇门此前把盘面平铺在顶层、没有 facts，冻结快照与 step2 都读不到任何内容。"""
        result = calculate_qimen_chart("2026-08-15T16:00:00")
        facts = result.get("facts")
        self.assertIsInstance(facts, dict)
        self.assertEqual(facts["dun_type"], result["dun_type"])
        self.assertEqual(facts["ju_number"], result["ju_number"])
        self.assertEqual(len(facts["palaces"]), 9)
        self.assertEqual(facts["zhi_fu_star"], result["zhi_fu_star"])

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

    def test_qimen_solar_term_zhongqi_coverage(self):
        """修复审计缺陷：奇门定局必须使用24节气（含中气），冬至夏至阴阳遁正确翻转。"""
        # 1. 2026-07-01 (夏至后、小暑前)：应采用「夏至」阴遁定局，不能延用芒种阳遁
        res_xiazhi = calculate_qimen_chart("2026-07-01T12:00:00")
        self.assertEqual(res_xiazhi["dun_type"], "阴遁")
        # 夏至定局为 阴遁 9, 3, 6 局之一
        self.assertIn(res_xiazhi["ju_number"], [9, 3, 6])

        # 2. 2026-12-25 (冬至后、小寒前)：应采用「冬至」阳遁定局，不能延用大雪阴遁
        res_dongzhi = calculate_qimen_chart("2026-12-25T12:00:00")
        self.assertEqual(res_dongzhi["dun_type"], "阳遁")
        # 冬至定局为 阳遁 1, 7, 4 局之一
        self.assertIn(res_dongzhi["ju_number"], [1, 7, 4])

        # 3. 2026-03-25 (春分后、清明前，中气)：应采用「春分」阳遁定局
        res_chunfen = calculate_qimen_chart("2026-03-25T12:00:00")
        self.assertEqual(res_chunfen["dun_type"], "阳遁")
        self.assertIn(res_chunfen["ju_number"], [3, 9, 6])


if __name__ == "__main__":
    unittest.main()
