import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.calendar import calendar_analysis
from app.core.imagery import collect_imagery
from app.core.interpretation import explain_correspondences
from app.core.liuren import time_cast as liuren_time_cast
from app.core.liuyao import time_cast as liuyao_time_cast
from app.core.meihua import time_cast as meihua_time_cast
from app.core.yuanhui import analyze_yuan_hui_yun_shi


class InterpretationTests(unittest.TestCase):
    def setUp(self):
        payload = {"local_datetime": "2026-08-15T16:00:00", "timezone": "Asia/Shanghai"}
        self.results = [
            {"module": "calendar", "method": "analyze", "result": calendar_analysis(**payload)},
            {"module": "meihua", "method": "time", "result": meihua_time_cast(**payload)},
            {"module": "liuyao", "method": "time", "result": liuyao_time_cast(**payload)},
            {"module": "liuren", "method": "time", "result": liuren_time_cast(**payload)},
        ]
        self.context = {"category": "career", "question_summary": "是否接受新的工作安排"}

    def test_explains_chart_correspondence_and_verification(self):
        imagery = collect_imagery(self.results, self.context)
        yuan_hui = analyze_yuan_hui_yun_shi(self.results)
        output = explain_correspondences(self.results, self.context, imagery, yuan_hui)
        self.assertEqual(len(output["modules"]), 3)
        self.assertIn("工作安排", output["summary"])
        self.assertTrue(all(item["correspondence"] and item["verification"] for item in output["modules"]))
        self.assertIn("第2爻", next(item for item in output["modules"] if item["module"] == "liuyao")["chart_fact"])
        self.assertTrue(output["cross_layer"])

    def test_does_not_emit_polarity_or_probability(self):
        imagery = collect_imagery(self.results, self.context)
        output = explain_correspondences(self.results, self.context, imagery, None)
        self.assertNotIn("polarity", output)
        self.assertTrue(any("不表示" in text for text in output["limitations"]))


if __name__ == "__main__":
    unittest.main()

