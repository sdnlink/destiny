"""八字流年确定性事实序列测试。"""
import unittest

from fastapi.testclient import TestClient

from app.bazi import calculate_liunian, year_ganzhi
from app.common.ganzhi import HAI_PAIRS, SELF_XING_BRANCHES, STEM_COMBINE, XING_PAIRS
from app.main import app


def synthetic_natal():
    """四柱：甲子年 / 乙丑月 / 丙寅日 / 辛卯时；日干丙。"""
    pillars = {}
    for key, ganzhi in (("year", "甲子"), ("month", "乙丑"), ("day", "丙寅"), ("hour", "辛卯")):
        pillars[key] = {"stem": ganzhi[0], "branch": ganzhi[1], "ganzhi": ganzhi}
    return {
        "day_master": "丙",
        "solar_datetime": "1984-02-10T12:00:00",
        "facts": {"pillars": pillars},
        "luck_start_info": {"start_year": 1987},
        "luck_pillars": [
            {"index": 1, "ganzhi": "丁卯", "stem_ten_god": "劫财",
             "start_year": 1987, "end_year": 1996},
            {"index": 2, "ganzhi": "戊辰", "stem_ten_god": "食神",
             "start_year": 1997, "end_year": 2006},
        ],
    }


class BaZiLiunianTests(unittest.TestCase):
    def test_year_ganzhi_cycle(self):
        self.assertEqual(year_ganzhi(1984), "甲子")
        self.assertEqual(year_ganzhi(2024), "甲辰")
        self.assertEqual(year_ganzhi(2026), "丙午")
        self.assertEqual(year_ganzhi(2044), "甲子")

    def test_liunian_facts_and_relations(self):
        result = calculate_liunian(synthetic_natal(), start_year=1990, count=2)
        self.assertEqual(result["rule_id"], "BZ-LIUNIAN-001")
        self.assertEqual(result["birth_year"], 1984)
        self.assertEqual(len(result["years"]), 2)
        first = result["years"][0]
        self.assertEqual(first["ganzhi"], "庚午")
        self.assertEqual(first["stem_element"], "金")
        self.assertEqual(first["branch_element"], "火")
        self.assertEqual(first["age"], 6)
        self.assertEqual(first["virtual_age"], 7)
        self.assertEqual(first["taisui_branch"], "午")
        self.assertEqual(first["suipo_branch"], "子")
        self.assertEqual(first["luck_pillar"]["ganzhi"], "丁卯")
        # 午与年支子六冲、与月支丑六害、与日支寅三合半合、与时支卯同属三刑组外
        types = [relation["type"] for relation in first["branch_relations"]]
        self.assertIn("六冲", types)
        self.assertIn("六害", types)
        self.assertIn("三合局半合", types)
        # 庚与月干乙天干五合（合金）
        self.assertTrue(any(r["with"] == "月柱" and r["combines_to"] == "金"
                            for r in first["stem_relations"]))
        self.assertTrue(result["evidence"], "流年结论应挂典籍原文依据")
        self.assertTrue(all(p["title"] for p in result["evidence"]))

    def test_luck_pillar_null_outside_range(self):
        result = calculate_liunian(synthetic_natal(), start_year=2030, count=1)
        self.assertIsNone(result["years"][0]["luck_pillar"])
        self.assertEqual(result["years"][0]["ganzhi"], "庚戌")

    def test_bounds_are_enforced(self):
        with self.assertRaises(ValueError):
            calculate_liunian(synthetic_natal(), start_year=2026, count=61)
        with self.assertRaises(ValueError):
            calculate_liunian(synthetic_natal(), start_year=1899, count=1)

    def test_relation_tables_are_shared(self):
        from app.liuyao import advanced
        self.assertEqual(advanced.XING_PAIRS, XING_PAIRS)
        self.assertEqual(advanced.HAI_PAIRS, HAI_PAIRS)
        self.assertEqual(advanced.SELF_XING_BRANCHES, SELF_XING_BRANCHES)
        self.assertEqual(STEM_COMBINE["甲"], ("己", "土"))

    def test_liunian_endpoint_and_validation(self):
        client = TestClient(app)
        payload = {
            "local_datetime": "1990-06-15T12:00:00",
            "timezone": "Asia/Shanghai",
            "gender": "男",
            "start_year": 2026,
            "count": 3,
        }
        response = client.post("/v1/bazi/liunian", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["system"], "bazi-liunian")
        self.assertEqual(len(data["years"]), 3)
        self.assertEqual(data["years"][0]["ganzhi"], "丙午")
        self.assertTrue(data["natal_summary"]["luck_pillars"])
        self.assertEqual(client.post("/v1/bazi/liunian", json={**payload, "count": 0}).status_code, 422)
        self.assertEqual(client.post("/v1/bazi/liunian", json={**payload, "start_year": 1899}).status_code, 422)


if __name__ == "__main__":
    unittest.main()
