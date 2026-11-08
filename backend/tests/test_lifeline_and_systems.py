"""流年大运 / 子平法 / 皇极经世 / 铁板神数 / 生平时间轴 回归测试。

原典依据：
- 《淵海子平·宝法第二》「先看提纲为重…皆以月令为用，不可以年取格」
- 《三命通會·論太歲》真太岁/岁运并临/日年相并/征太岁
- 《皇極經世》卷一「以元經會」元会运世换算层级
- 铁板神数：本地典籍库按书名精确核查无条文底本 → 只声明缺口
"""
import unittest

from fastapi.testclient import TestClient

from app.bazi.lifeline import analyze_lifeline, lichun_datetime
from app.bazi.tieban import tieban_status
from app.core.registry import load_rule_registry, rule_index, validate_rule_registry
from app.core.yuanhui_readonly import cycle_cast
from app.main import app

BIRTH = {"local_datetime": "1984-02-10 10:00:00", "timezone": "Asia/Shanghai", "gender": "男"}


class LichunPrecisionTests(unittest.TestCase):
    def test_known_lichun_moments(self):
        # lunar-python 寿星节气表：立春交接时刻（Asia/Shanghai 参考时）
        self.assertEqual(lichun_datetime(1984), "1984-02-04 23:18:44")
        self.assertEqual(lichun_datetime(2024), "2024-02-04 16:27:07")
        self.assertEqual(lichun_datetime(2026), "2026-02-04 04:02:08")

    def test_out_of_range_rejected(self):
        for year in (1899, 2101):
            with self.assertRaises(ValueError):
                lichun_datetime(year)


class ZipingYuelingTests(unittest.TestCase):
    def test_month_order_basis_and_candidates(self):
        r = analyze_lifeline(**BIRTH, count=3)
        z = r["ziping"]
        self.assertIn("月令为用", z["rule"])
        self.assertTrue(z["month_branch"])
        self.assertTrue(z["hidden_stems"])
        self.assertEqual(z["principal_qi"]["qi"], "本气")
        for row in z["hidden_stems"]:
            self.assertIn(row["ten_god"], (
                "比肩", "劫财", "食神", "伤官", "正财", "偏财",
                "正官", "七杀", "正印", "偏印",
            ))
        for c in z["pattern_candidates"]:
            self.assertTrue(c["pattern_candidate"].endswith("格候选"))
            self.assertTrue(c["basis"])
        # 不产出吉凶/格局成败结论
        blob = str(z)
        for word in ("大吉", "大凶", "贵格", "贱格", "成格", "败格", "准确率"):
            self.assertNotIn(word, blob)

    def test_candidates_only_for_exposed_hidden_stems(self):
        r = analyze_lifeline(**BIRTH, count=1)
        z = r["ziping"]
        exposed = {row["stem"] for row in z["hidden_stems"] if row["exposed"]}
        for c in z["pattern_candidates"]:
            self.assertTrue(any(row["stem"] in c["basis"] and row["stem"] in exposed
                                for row in z["hidden_stems"]))


class SuiyunFactsTests(unittest.TestCase):
    def test_true_taisui_and_suiyun_binglin_are_boolean_facts(self):
        # 1984 甲子生人，60 年后 2044 甲子为真太岁
        r = analyze_lifeline(**BIRTH, start_year=2044, count=1)
        row = r["timeline"][0]
        self.assertEqual(row["ganzhi"], "甲子")
        self.assertTrue(row["suiyun"]["true_taisui"])
        s = row["suiyun"]
        for key in ("true_taisui", "suiyun_binglin", "day_year_parallel", "zheng_taisui"):
            self.assertIsInstance(s[key], bool)
        # 甲子流年与四柱必有冲合刑害组合事实（甲子冲午、子与丑合等依盘而定）
        self.assertIsInstance(s["relations"], dict)
        for label, rels in (s["relations"].get("with_natal_pillars") or {}).items():
            self.assertIsInstance(rels, list)

    def test_no_fortune_conclusions_in_timeline(self):
        r = analyze_lifeline(**BIRTH, start_year=2024, count=12)
        blob = str(r["timeline"])
        for word in ("大吉", "大凶", "灾祸", "必死", "准确率", "发财", "升官"):
            self.assertNotIn(word, blob)
        self.assertEqual(r["judgements"], [])


class YuanhuiBackgroundTests(unittest.TestCase):
    def test_position_and_pending_epoch(self):
        r = cycle_cast(2026)
        self.assertEqual(r["status"], "engineering_cycle_context_pending_expert_review")
        self.assertEqual(r["facts"]["epoch"]["status"], "pending_expert_review")
        self.assertEqual(r["facts"]["hui"]["branch"], "午")
        self.assertEqual(r["facts"]["yuan"]["index"], 1)
        self.assertEqual(r["cycle_units"]["years_per_yuan"], 129600)
        self.assertEqual(r["judgements"], [])

    def test_evidence_from_huangji(self):
        r = cycle_cast(2026)
        self.assertTrue(any("皇極經世" in (e.get("title") or "") for e in r["evidence"]))

    def test_year_range(self):
        for year in (1899, 2101):
            with self.assertRaises(ValueError):
                cycle_cast(year)


class TiebanDataGapTests(unittest.TestCase):
    def test_status_declares_gap_without_any_article_or_number(self):
        r = tieban_status()
        self.assertFalse(r["implemented"])
        self.assertEqual(r["available_capabilities"], [])
        self.assertEqual(r["tieban_corpus_titles"], [])
        self.assertGreaterEqual(len(r["missing_prerequisites"]), 5)
        self.assertEqual(r["judgements"], [])
        # 不输出任何条数或条文断语（capabilities 为空）
        self.assertEqual(r["available_capabilities"], [])
        self.assertTrue(all("pending" in w or "不" in w or "伪造" in w for w in r["warnings"]))


class LifelineEventsTests(unittest.TestCase):
    def test_events_are_readonly_alignment(self):
        events = [{"year": 2030, "label": "已发生：迁居"}, {"year": 2030, "label": "已发生：入职"}]
        r = analyze_lifeline(**BIRTH, start_year=2030, count=2, events=events)
        self.assertEqual(len(r["timeline"][0]["recorded_events"]), 2)
        self.assertEqual(r["timeline"][1]["recorded_events"], [])
        # 事件不改变任何计算字段
        plain = analyze_lifeline(**BIRTH, start_year=2030, count=2)
        for a, b in zip(plain["timeline"], r["timeline"]):
            self.assertEqual(a["ganzhi"], b["ganzhi"])
            self.assertEqual(a["suiyun"], b["suiyun"])

    def test_invalid_event_rejected(self):
        with self.assertRaises(ValueError):
            analyze_lifeline(**BIRTH, count=1, events=[{"label": "缺少年份"}])
        with self.assertRaises(ValueError):
            analyze_lifeline(**BIRTH, count=1, events=[{"year": 1899}])

    def test_count_and_year_range(self):
        for count in (0, 61):
            with self.assertRaises(ValueError):
                analyze_lifeline(**BIRTH, count=count)
        with self.assertRaises(ValueError):
            analyze_lifeline(**BIRTH, start_year=2099, count=5)


class EnvelopeAndRegistryTests(unittest.TestCase):
    def test_new_endpoints(self):
        c = TestClient(app)
        r = c.post("/v1/bazi/lifeline", json={**BIRTH, "count": 3})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json()["data"]["timeline"]), 3)
        self.assertEqual(c.get("/v1/yuanhui/cycle", params={"year": 2026}).status_code, 200)
        self.assertEqual(c.get("/v1/yuanhui/cycle", params={"year": 1899}).status_code, 422)
        self.assertEqual(c.get("/v1/tieban/status").status_code, 200)
        self.assertEqual(c.post("/v1/bazi/lifeline", json={**BIRTH, "count": 99}).status_code, 422)

    def test_bazi_and_liunian_envelopes(self):
        c = TestClient(app)
        b = c.post("/v1/bazi/time", json=BIRTH).json()["data"]
        self.assertEqual(b["status"], "engineering_baseline_draft")
        self.assertIn("ziping", b["school"])
        self.assertEqual(b["judgements"], [])
        self.assertTrue(b["warnings"])
        l = c.post("/v1/bazi/liunian", json={**BIRTH, "count": 2}).json()["data"]
        self.assertEqual(l["status"], "engineering_baseline_draft")
        self.assertEqual(l["judgements"], [])
        self.assertTrue(l["warnings"])

    def test_new_rules_registered(self):
        registry = load_rule_registry()
        self.assertEqual(validate_rule_registry(registry), [])
        idx = rule_index(registry)
        for rule_id in ("BZ-LIFELINE-001", "YHYS-READONLY-001", "BZ-TIEBAN-STATUS-001"):
            self.assertEqual(idx[rule_id]["status"], "draft")
            self.assertTrue(idx[rule_id]["source_refs"])
            self.assertEqual(idx[rule_id]["reviewers"], [])


if __name__ == "__main__":
    unittest.main()
