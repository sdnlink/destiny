import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.calendar import calendar_analysis
from app.core.iching import auto_cast as zhouyi_auto_cast, manual_cast, time_cast as zhouyi_time_cast
from app.zhouyi import three_number_cast
from app.daliuren import auto_cast as liuren_auto_cast, time_cast as liuren_time_cast
from app.core.liuyao import auto_cast as liuyao_auto_cast, time_cast as liuyao_time_cast
from app.liuyao import coin_cast as liuyao_coin_cast, line_cast as liuyao_line_cast
from app.core.meihua import auto_cast as meihua_auto_cast, time_cast
from app.meihua import three_number_cast as meihua_three_number_cast
from app.ziwei import time_cast as ziwei_time_cast, auto_cast as ziwei_auto_cast
from app.core.registry import load_rule_registry, load_validation_cases, unknown_rule_ids
from app.core.validation import compare_subset, run_validation_cases


class RuleRegistryTests(unittest.TestCase):
    def test_registry_is_valid_and_has_stable_checksum(self):
        registry = load_rule_registry()
        # 规则会持续增补，断言下限而不是固定数字，避免每加一条就要改测试
        self.assertGreaterEqual(len(registry["rules"]), 69)
        self.assertTrue(registry["checksum"].startswith("sha256:"))
        self.assertEqual(registry["rule_sets"][0]["status"], "draft")
        registered = {(rule["rule_id"], rule["version"]) for rule in registry["rules"]}
        for ref in registry["rule_sets"][0]["rules"]:
            self.assertIn((ref["rule_id"], ref["version"]), registered)

    def test_workflow_rules_are_registered(self):
        """编排层（workflow/interaction）输出的 rule_ids 必须能在注册表里查到。"""
        registry = load_rule_registry()
        registered = {rule["rule_id"] for rule in registry["rules"]}
        workflow_rule_ids = {
            "WF-YONGSHEN-001",
            "WF-WANGSHUAI-001",
            "WF-FORTUNE-001",
            "WF-TIMING-001",
        }
        self.assertEqual(workflow_rule_ids - registered, set())
        for rule_id in workflow_rule_ids:
            self.assertEqual(unknown_rule_ids({"rule_ids": [rule_id]}, registry), [])

    def test_all_calculation_rule_references_are_registered(self):
        results = [
            calendar_analysis("2026-08-15T16:00:00", "Asia/Shanghai"),
            manual_cast([9, 7, 7, 7, 7, 7]),
            zhouyi_time_cast("2026-08-15T16:00:00", "Asia/Shanghai"),
            time_cast("2026-08-15T16:00:00", "Asia/Shanghai"),
            liuyao_time_cast("2026-08-15T16:00:00", "Asia/Shanghai"),
            liuyao_line_cast([9, 7, 7, 7, 7, 7], "2026-08-15T16:00:00", "Asia/Shanghai"),
            liuyao_coin_cast([[3, 3, 3]] + [[3, 2, 2]] * 5, "2026-08-15T16:00:00", "Asia/Shanghai"),
            liuren_time_cast("2026-08-15T16:00:00", "Asia/Shanghai"),
            zhouyi_auto_cast("person-0000000000000001", "2026-08-15T16:00:00", "Asia/Shanghai"),
            three_number_cast(23, 47, 5),
            meihua_auto_cast("person-0000000000000001", "2026-08-15T16:00:00", "Asia/Shanghai"),
            meihua_three_number_cast(25, 38, 5),
            liuyao_auto_cast("person-0000000000000001", "2026-08-15T16:00:00", "Asia/Shanghai"),
            liuren_auto_cast("person-0000000000000001", "2026-08-15T16:00:00", "Asia/Shanghai"),
            ziwei_time_cast("2026-08-15T16:00:00", "Asia/Shanghai", "男"),
            ziwei_auto_cast("person-0000000000000001", "2026-08-15T16:00:00", "Asia/Shanghai", "女"),
        ]
        for result in results:
            self.assertEqual(unknown_rule_ids(result), [])

    def test_validation_case_document_is_explicitly_unreviewed(self):
        document = load_validation_cases()
        self.assertGreaterEqual(len(document["cases"]), 31)
        self.assertIn("pending_expert_review", document["qualification"])
        self.assertTrue(all(not case["reviewers"] for case in document["cases"]))

    def test_all_engineering_validation_cases_pass(self):
        report = run_validation_cases()
        self.assertEqual(report["failed"], 0, report["results"])

    def test_subset_comparison_reports_nested_path(self):
        differences = compare_subset({"facts": {"value": 2}}, {"facts": {"value": 1}})
        self.assertEqual(differences, ["result.facts.value expected 1, got 2"])


if __name__ == "__main__":
    unittest.main()
