import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.synthesis import synthesize


def registry_with_published_rule():
    return {
        "rules": [
            {
                "rule_id": "TEST-JUDGEMENT-001",
                "version": "1.0.0",
                "status": "published",
            }
        ]
    }


def result(system, polarity, time_range=None):
    return {
        "system": system,
        "school": "test-school",
        "rule_version": "1.0.0",
        "judgements": [
            {
                "dimension": "external_support",
                "time_range": time_range or {"start": "2026-08-01", "end": "2026-09-01"},
                "polarity": polarity,
                "rule_ids": ["TEST-JUDGEMENT-001"],
                "evidence_ids": ["evidence-1"],
            }
        ],
    }


class SynthesisTests(unittest.TestCase):
    def test_same_polarity_is_consistent(self):
        output = synthesize(
            [result("zhouyi", "favorable"), result("meihua", "favorable")],
            registry_with_published_rule(),
        )
        self.assertEqual(output["counts"]["consistent"], 1)
        self.assertEqual(output["comparable_judgement_count"], 2)

    def test_opposite_polarity_is_conflict(self):
        output = synthesize(
            [result("zhouyi", "favorable"), result("meihua", "unfavorable")],
            registry_with_published_rule(),
        )
        self.assertEqual(output["counts"]["conflicts"], 1)

    def test_different_time_ranges_are_not_compared(self):
        later = {"start": "2026-09-01", "end": "2026-10-01"}
        output = synthesize(
            [result("zhouyi", "favorable"), result("meihua", "unfavorable", later)],
            registry_with_published_rule(),
        )
        self.assertEqual(output["counts"]["conflicts"], 0)
        self.assertEqual(output["counts"]["unpaired"], 2)

    def test_unpublished_rules_are_excluded(self):
        registry = registry_with_published_rule()
        registry["rules"][0]["status"] = "draft"
        output = synthesize([result("zhouyi", "favorable")], registry)
        self.assertEqual(output["comparable_judgement_count"], 0)
        self.assertEqual(output["counts"]["excluded"], 1)


if __name__ == "__main__":
    unittest.main()
