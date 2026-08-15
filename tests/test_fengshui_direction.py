import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "fengshui_direction.py"
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


if __name__ == "__main__":
    unittest.main()
