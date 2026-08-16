import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import AutoCastRequest, AdvisoryContext, CalculationRequest, calculation_envelope, canonical_hash, comparison_envelope, execute
from pydantic import ValidationError


class MvpApiTests(unittest.TestCase):
    def test_auto_request_rejects_unsafe_nonce(self):
        with self.assertRaises(ValidationError):
            AutoCastRequest(
                cast_nonce="contains spaces 123",
                local_datetime="2026-08-15T16:00:00",
                timezone="Asia/Shanghai",
            )

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

    def test_dispatches_four_system_time_and_number_methods(self):
        calendar = {"local_datetime": "2026-08-15T16:00:00", "timezone": "Asia/Shanghai"}
        self.assertEqual(execute("zhouyi", "time", calendar)["facts"]["original"]["name"], "履")
        self.assertEqual(execute("liuyao", "time", calendar)["facts"]["palace"]["name"], "艮")
        liuyao_numbers = dict(calendar, lower_number=1, upper_number=1)
        self.assertEqual(execute("liuyao", "numbers", liuyao_numbers)["facts"]["palace"]["name"], "乾")
        self.assertEqual(execute("liuren", "time", calendar)["facts"]["month_general"]["branch"], "午")
        liuren_numbers = dict(calendar, number=12)
        self.assertEqual(execute("liuren", "numbers", liuren_numbers)["facts"]["occupation_time"]["branch"], "亥")

    def test_dispatches_four_personalized_auto_methods(self):
        payload = {
            "cast_nonce": "person-0000000000000001",
            "local_datetime": "2026-08-15T16:00:00",
            "timezone": "Asia/Shanghai",
        }
        expected = {
            "zhouyi": "personalized_three_coin",
            "meihua": "personalized_lunar_time",
            "liuyao": "personalized_three_coin",
            "liuren": "personalized_report_number",
        }
        for module, method in expected.items():
            with self.subTest(module=module):
                result = execute(module, "auto", payload)
                self.assertEqual(result["facts"]["method"], method)
                self.assertTrue(result["facts"]["cast_nonce_hash"].startswith("sha256:"))

    def test_comparison_explains_personalized_auto_methods(self):
        payload = {
            "cast_nonce": "person-0000000000000001",
            "local_datetime": "2026-08-15T16:00:00",
            "timezone": "Asia/Shanghai",
        }
        calculations = [CalculationRequest(module=module, method="auto", input=payload) for module in (
            "zhouyi", "meihua", "liuyao", "liuren",
        )]
        output = comparison_envelope(calculations)
        self.assertEqual(len(output["explanation"]["modules"]), 4)
        self.assertIn("YI-AUTO-COIN-001", output["explanation"]["modules"][0]["sections"][0]["rule_ids"])

    def test_rejects_unknown_calculation(self):
        with self.assertRaises(ValueError):
            execute("unknown", "method", {})

    def test_comparison_task_is_order_independent(self):
        first_request = CalculationRequest(
            module="zhouyi", method="numbers", input={"lower_number": 8, "upper_number": 8}
        )
        second_request = CalculationRequest(
            module="meihua", method="numbers", input={"upper_number": 8, "lower_number": 8}
        )
        first = comparison_envelope([first_request, second_request])
        second = comparison_envelope([second_request, first_request])
        self.assertEqual(first["task_id"], second["task_id"])
        self.assertEqual(first["input_hash"], second["input_hash"])
        self.assertEqual(first["comparison"]["comparable_judgement_count"], 0)
        self.assertEqual(len(first["module_results"]), 2)
        self.assertEqual(first["explanation"]["conclusion"]["status"], "factual_result_only")

    def test_context_generates_advice_and_changes_task_identity(self):
        calculation = CalculationRequest(
            module="meihua", method="numbers", input={"upper_number": 1, "lower_number": 2}
        )
        career = comparison_envelope([calculation], AdvisoryContext(
            category="career", question_summary="是否接受新的工作机会"
        ))
        finance = comparison_envelope([calculation], AdvisoryContext(
            category="finance", question_summary="是否增加投入"
        ))
        self.assertNotEqual(career["task_id"], finance["task_id"])
        self.assertEqual(career["advisory"]["context"]["category"], "career")
        self.assertIn("工作机会", career["advisory"]["conclusion"]["text"])
        self.assertEqual(career["imagery"]["context"]["category"], "career")
        self.assertIsNone(career["yuan_hui_yun_shi"])

    def test_comparison_attaches_yuanhui_when_calendar_is_present(self):
        calculation = CalculationRequest(
            module="calendar", method="analyze",
            input={"local_datetime": "2026-08-15T16:00:00", "timezone": "Asia/Shanghai"},
        )
        output = comparison_envelope([calculation])
        self.assertEqual(output["yuan_hui_yun_shi"]["facts"]["hui"]["branch"], "午")


if __name__ == "__main__":
    unittest.main()
