import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.meihua import five_element_relation, number_cast, time_cast


class MeihuaTests(unittest.TestCase):
    def test_five_element_relationships(self):
        self.assertEqual(five_element_relation("木", "水")["code"], "use_generates_body")
        self.assertEqual(five_element_relation("木", "火")["code"], "body_generates_use")
        self.assertEqual(five_element_relation("木", "金")["code"], "use_controls_body")
        self.assertEqual(five_element_relation("木", "土")["code"], "body_controls_use")
        self.assertEqual(five_element_relation("金", "金")["code"], "same_element")

    def test_two_number_cast(self):
        result = number_cast(1, 2)
        self.assertEqual(result["facts"]["original"]["ordinal"], 10)
        self.assertEqual(result["facts"]["moving_line"], 3)
        self.assertEqual(result["facts"]["body_use"]["body_position"], "upper")
        self.assertEqual(result["facts"]["body_use"]["use_position"], "lower")
        self.assertEqual(result["evidence"][0]["code"], "same_element")

    def test_known_time_cast(self):
        result = time_cast("2026-08-15T16:00:00", "Asia/Shanghai")
        facts = result["facts"]
        self.assertEqual(facts["source_numbers"], {
            "year_branch": 7,
            "lunar_month": 7,
            "lunar_day": 3,
            "hour_branch": 9,
            "upper_sum": 17,
            "lower_sum": 26,
        })
        self.assertEqual(facts["original"]["ordinal"], 10)
        self.assertEqual(facts["moving_line"], 2)
        self.assertEqual(facts["body_use"]["body_position"], "upper")

    def test_time_cast_can_use_true_solar_time(self):
        result = time_cast(
            "2026-08-15T00:20:00", "Asia/Shanghai", longitude=105, use_true_solar_time=True
        )
        self.assertTrue(result["facts"]["calendar"]["time"]["correction"]["enabled"])
        self.assertNotEqual(
            result["facts"]["calendar"]["time"]["original_local_datetime"],
            result["facts"]["calendar"]["time"]["effective_local_datetime"],
        )


if __name__ == "__main__":
    unittest.main()
