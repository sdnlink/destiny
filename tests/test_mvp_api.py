import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import calculation_envelope, canonical_hash, execute


class MvpApiTests(unittest.TestCase):
    def test_hash_is_stable_across_dictionary_order(self):
        first = canonical_hash({"b": 2, "a": 1})
        second = canonical_hash({"a": 1, "b": 2})
        self.assertEqual(first, second)

    def test_calculation_task_id_is_idempotent(self):
        payload = {"lower_number": 8, "upper_number": 8}
        first = calculation_envelope("zhouyi", "numbers", payload)
        second = calculation_envelope("zhouyi", "numbers", payload)
        self.assertEqual(first["task_id"], second["task_id"])
        self.assertEqual(first["input_hash"], second["input_hash"])

    def test_dispatches_meihua_time(self):
        result = execute("meihua", "time", {
            "local_datetime": "2026-08-15T16:00:00",
            "timezone": "Asia/Shanghai",
        })
        self.assertEqual(result["facts"]["original"]["ordinal"], 10)

    def test_dispatches_calendar(self):
        result = execute("calendar", "analyze", {
            "local_datetime": "2026-08-15T16:00:00",
            "timezone": "Asia/Shanghai",
        })
        self.assertEqual(result["pillars"]["day"], "辛酉")

    def test_rejects_unknown_calculation(self):
        with self.assertRaises(ValueError):
            execute("unknown", "method", {})


if __name__ == "__main__":
    unittest.main()
