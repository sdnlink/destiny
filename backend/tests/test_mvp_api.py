import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import AutoCastRequest, AdvisoryContext, CalculationRequest, LiurenNumberRequest, LiuyaoCoinRequest, LiuyaoLineRequest, MeihuaThreeNumberRequest, YiThreeNumberRequest, calculation_envelope, canonical_hash, comparison_envelope, execute
from pydantic import ValidationError


class MvpApiTests(unittest.TestCase):
    def test_three_number_api_requires_exactly_three_strict_non_negative_integers(self):
        for numbers in ([1, 2], [1, 2, 3, 4], [1, True, 3], [1, -2, 3]):
            with self.subTest(numbers=numbers), self.assertRaises(ValidationError):
                YiThreeNumberRequest(numbers=numbers)

    def test_meihua_three_number_api_requires_three_strict_integers(self):
        for numbers in ([1, 2], [1, 2, 3, 4], [1, True, 3], [1, 2.0, 3]):
            with self.subTest(numbers=numbers), self.assertRaises(ValidationError):
                MeihuaThreeNumberRequest(numbers=numbers)

    def test_liuyao_manual_api_models_are_strict(self):
        with self.assertRaises(ValidationError):
            LiuyaoLineRequest(lines=[7, 7, 7, 7, 7, True], **{
                "local_datetime": "2026-08-15T16:00:00", "timezone": "Asia/Shanghai",
            })
        with self.assertRaises(ValidationError):
            LiuyaoCoinRequest(coins=[[3, 2, 2]] * 5, **{
                "local_datetime": "2026-08-15T16:00:00", "timezone": "Asia/Shanghai",
            })

    def test_daliuren_number_api_requires_a_strict_integer(self):
        for number in (True, 4.0, "4"):
            with self.subTest(number=number), self.assertRaises(ValidationError):
                LiurenNumberRequest(number=number, **{
                    "local_datetime": "2026-08-15T16:00:00", "timezone": "Asia/Shanghai",
                })
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

    def test_dispatches_zhouyi_three_number_method(self):
        payload = {"numbers": [23, 47, 5], "mapping_version": "earlier-heaven-number-v1"}
        result = execute("zhouyi", "three_numbers", payload)
        self.assertEqual(result["facts"]["original"]["name"], "艮")
        self.assertEqual(result["facts"]["changed"]["name"], "渐")
        explained = comparison_envelope([
            CalculationRequest(module="zhouyi", method="three_numbers", input=payload),
        ])
        self.assertIn("YI-3NUM-MAPPING-001", explained["explanation"]["modules"][0]["sections"][0]["rule_ids"])

    def test_dispatches_meihua_three_number_method(self):
        payload = {"numbers": [25, 38, 5]}
        result = execute("meihua", "three_numbers", payload)
        self.assertEqual(result["facts"]["original"]["name"], "讼")
        self.assertEqual(result["facts"]["changed"]["name"], "未济")
        explained = comparison_envelope([
            CalculationRequest(module="meihua", method="three_numbers", input=payload),
        ])
        self.assertIn("MH-THREE-NUMBER-001", explained["explanation"]["modules"][0]["sections"][0]["rule_ids"])

    def test_dispatches_liuyao_lines_and_coin_methods(self):
        calendar = {"local_datetime": "2026-08-15T16:00:00", "timezone": "Asia/Shanghai"}
        lines = execute("liuyao", "lines", dict(calendar, lines=[9, 7, 7, 7, 7, 7]))
        coins = execute("liuyao", "coins", dict(calendar, coins=[[3, 3, 3]] + [[3, 2, 2]] * 5))
        self.assertEqual(lines["facts"]["changed"]["name"], "姤")
        self.assertEqual(coins["facts"]["input_lines"], [9, 7, 7, 7, 7, 7])
        explained = comparison_envelope([
            CalculationRequest(module="liuyao", method="coins", input=dict(calendar, coins=[[3, 2, 2]] * 6)),
        ])
        self.assertIn("LY-COINS-001", explained["explanation"]["modules"][0]["sections"][0]["rule_ids"])

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
