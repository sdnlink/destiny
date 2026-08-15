import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.calendar import calendar_analysis
from app.core.explanation import explain_calculation_set
from app.core.iching import manual_cast
from app.core.meihua import time_cast


class ExplanationTests(unittest.TestCase):
    def setUp(self):
        self.module_results = [
            {
                "module": "calendar",
                "method": "analyze",
                "result": calendar_analysis("2026-08-15T16:00:00", "Asia/Shanghai"),
            },
            {
                "module": "zhouyi",
                "method": "manual",
                "result": manual_cast([9, 7, 7, 7, 7, 7]),
            },
            {
                "module": "meihua",
                "method": "time",
                "result": time_cast("2026-08-15T16:00:00", "Asia/Shanghai"),
            },
        ]
        self.comparison = {
            "comparable_judgement_count": 0,
            "counts": {
                "consistent": 0, "complementary": 0, "conflicts": 0,
                "unpaired": 0, "indeterminate": 0, "excluded": 0,
            },
        }

    def test_explains_all_module_facts(self):
        output = explain_calculation_set(self.module_results, self.comparison)
        self.assertEqual(len(output["modules"]), 3)
        self.assertIn("乾卦（第1卦）", output["summary"])
        self.assertIn("履卦（第10卦）", output["summary"])
        self.assertEqual(output["generation_method"], "deterministic_fact_template")

    def test_does_not_invent_unreviewed_conclusion(self):
        output = explain_calculation_set(self.module_results, self.comparison)
        self.assertEqual(output["conclusion"]["status"], "factual_result_only")
        self.assertIn("不生成事项吉凶", output["conclusion"]["text"])

    def test_each_detail_keeps_rule_references(self):
        output = explain_calculation_set(self.module_results, self.comparison)
        for module in output["modules"]:
            for section in module["sections"]:
                self.assertTrue(section["rule_ids"])


if __name__ == "__main__":
    unittest.main()
