import importlib.util
from pathlib import Path
import unittest

import pytest

from app.fengshui import calculate_direction


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "fengshui_direction.py"
SPEC = importlib.util.spec_from_file_location("fengshui_direction", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DirectionTests(unittest.TestCase):
    def test_cardinal_mountains(self):
        self.assertEqual(MODULE.classify(0)["mountain"], "子")
        self.assertEqual(MODULE.classify(90)["mountain"], "卯")
        self.assertEqual(MODULE.classify(180)["mountain"], "午")
        self.assertEqual(MODULE.classify(270)["mountain"], "酉")

    def test_wraparound(self):
        self.assertEqual(MODULE.classify(359)["mountain"], "子")
        self.assertEqual(MODULE.classify(-15)["mountain"], "壬")

    def test_boundary_is_half_open(self):
        self.assertEqual(MODULE.classify(7.499)["mountain"], "子")
        self.assertEqual(MODULE.classify(7.5)["mountain"], "癸")

    def test_sitting_is_opposite_facing(self):
        result = MODULE.calculate(180, input_reference="true")
        self.assertEqual(result["facing"]["mountain"], "午")
        self.assertEqual(result["sitting"]["mountain"], "子")

    def test_declination_correction(self):
        result = MODULE.calculate(6, magnetic_declination=2)
        self.assertEqual(result["true_facing_degree"], 8)
        self.assertEqual(result["facing"]["mountain"], "癸")
        self.assertTrue(result["boundary_warning"])


def test_domain_result_uses_unified_fact_protocol():
    result = calculate_direction(180, input_reference="true", measurement_error=1)
    assert result["system"] == "fengshui"
    assert result["facts"]["facing"]["mountain"]["name"] == "午"
    assert result["facts"]["sitting"]["mountain"]["name"] == "子"
    assert result["facts"]["true_sitting_degree"] == 0
    assert result["judgements"] == []
    assert [step["sequence"] for step in result["steps"]] == [1, 2, 3, 4]


def test_uncertainty_crossing_boundary_returns_both_candidates():
    result = calculate_direction(7.4, input_reference="true", measurement_error=0.2)
    facing = result["facts"]["facing"]
    assert facing["mountain"]["name"] == "子"
    assert {item["name"] for item in facing["candidate_mountains"]} == {"子", "癸"}
    assert facing["classification_stable"] is False
    assert result["facts"]["boundary_warning"] is True


def test_true_north_input_does_not_apply_declination():
    result = calculate_direction(6, input_reference="true", magnetic_declination=2)
    assert result["facts"]["true_facing_degree"] == 6
    assert result["normalized_input"]["applied_declination"] == 0
    assert "未参与修正" in result["warnings"][0]


@pytest.mark.parametrize("field,value", [
    ("facing_degree", True), ("facing_degree", "180"),
    ("facing_degree", float("nan")), ("magnetic_declination", float("inf")),
    ("measurement_error", -0.1), ("measurement_error", 181),
])
def test_invalid_numeric_inputs_are_rejected(field, value):
    payload = {"facing_degree": 180, field: value}
    with pytest.raises(ValueError):
        calculate_direction(**payload)


if __name__ == "__main__":
    unittest.main()
