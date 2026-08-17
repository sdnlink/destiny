import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.imagery import collect_imagery
from app.core.meihua import number_cast


class ImageryTests(unittest.TestCase):
    def test_context_prioritizes_dimensions_without_judgement(self):
        output = collect_imagery(
            [{"module": "meihua", "method": "numbers", "result": number_cast(1, 2)}],
            {"category": "career", "question_summary": "是否调整工作"},
        )
        self.assertEqual(output["context"]["priority_dimensions"], ["人物", "行为", "场所", "事物"])
        self.assertEqual(output["status"], "unreviewed_imagery_candidates")
        self.assertEqual(len(output["candidates"]), 3)
        self.assertIn("人物", output["candidates"][0]["selected_imagery"])

    def test_all_eight_trigrams_have_complete_imagery_dimensions(self):
        from app.core.imagery import TRIGRAM_IMAGERY
        trigram_names = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]
        expected_dimensions = [
            "象意", "自然", "方位", "人物", "家庭", "身体",
            "动物", "事物", "场所", "行为", "色彩", "饮食", "疾病",
        ]
        self.assertEqual(sorted(TRIGRAM_IMAGERY.keys()), sorted(trigram_names))
        for name in trigram_names:
            imagery = TRIGRAM_IMAGERY[name]
            for dim in expected_dimensions:
                self.assertIn(dim, imagery, f"Trigram {name} missing dimension {dim}")
                self.assertTrue(len(imagery[dim]) > 0, f"Trigram {name} dimension {dim} is empty")


if __name__ == "__main__":
    unittest.main()

