import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.advisory import generate_advisory
from app.core.iching import manual_cast
from app.core.meihua import number_cast


class AdvisoryTests(unittest.TestCase):
    def setUp(self):
        self.results = [
            {"module": "zhouyi", "method": "manual", "result": manual_cast([7, 8, 7, 8, 7, 8])},
            {"module": "meihua", "method": "numbers", "result": number_cast(1, 2)},
        ]

    def test_combines_question_category_and_calculation_facts(self):
        output = generate_advisory(self.results, {
            "category": "career",
            "question_summary": "是否应该接受新的工作机会",
        })
        self.assertEqual(output["context"]["category_label"], "事业")
        self.assertIn("是否应该接受新的工作机会", output["conclusion"]["text"])
        self.assertGreaterEqual(len(output["recommendations"]), 4)
        self.assertTrue(output["evidence_basis"])

    def test_advice_is_explicitly_provisional_and_indeterminate(self):
        output = generate_advisory(self.results, {
            "category": "finance",
            "question_summary": "是否增加投入",
        })
        self.assertEqual(output["review_status"], "unreviewed_engineering_template")
        self.assertEqual(output["conclusion"]["polarity"], "indeterminate")
        self.assertTrue(any("不可逆" in note for note in output["risk_notes"]))

    def test_rejects_unknown_category(self):
        with self.assertRaises(ValueError):
            generate_advisory(self.results, {"category": "unknown", "question_summary": "测试"})


if __name__ == "__main__":
    unittest.main()
