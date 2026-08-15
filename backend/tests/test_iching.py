import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.iching import derive_hexagrams, hexagram_from_bits, manual_cast, number_cast


class IChingTests(unittest.TestCase):
    def test_qian_and_kun_map_to_king_wen_order(self):
        self.assertEqual(hexagram_from_bits((1, 1, 1, 1, 1, 1))["ordinal"], 1)
        self.assertEqual(hexagram_from_bits((0, 0, 0, 0, 0, 0))["ordinal"], 2)

    def test_water_thunder_zhun_mapping(self):
        # Lower Zhen, upper Kan.
        result = hexagram_from_bits((1, 0, 0, 0, 1, 0))
        self.assertEqual((result["ordinal"], result["name"]), (3, "屯"))

    def test_manual_old_yang_changes_to_yin(self):
        result = manual_cast([9, 7, 7, 7, 7, 7])
        self.assertEqual(result["facts"]["original"]["ordinal"], 1)
        self.assertEqual(result["facts"]["changed"]["ordinal"], 44)
        self.assertEqual(result["facts"]["moving_lines"], [1])

    def test_related_hexagrams(self):
        result = derive_hexagrams((1, 0, 0, 0, 1, 0), [1])
        self.assertEqual(result["original"]["ordinal"], 3)
        self.assertEqual(result["opposite"]["ordinal"], 50)
        self.assertEqual(result["reversed"]["ordinal"], 4)

    def test_number_cast_remainder_zero_rules(self):
        result = number_cast(8, 8)
        self.assertEqual(result["facts"]["original"]["ordinal"], 2)
        self.assertEqual(result["facts"]["moving_lines"], [4])

    def test_invalid_manual_lines_are_rejected(self):
        with self.assertRaises(ValueError):
            manual_cast([7, 7, 7])
        with self.assertRaises(ValueError):
            manual_cast([7, 7, 7, 7, 7, 5])


if __name__ == "__main__":
    unittest.main()
