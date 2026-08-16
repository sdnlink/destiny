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


if __name__ == "__main__":
    unittest.main()

