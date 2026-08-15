import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.core.cyclical import sexagenary_index, xun_info


class CyclicalTests(unittest.TestCase):
    def test_sexagenary_index_and_void(self):
        self.assertEqual(sexagenary_index("甲子"), 0)
        self.assertEqual(sexagenary_index("癸亥"), 59)
        self.assertEqual(xun_info("辛酉")["empty_branches"], ["子", "丑"])
        self.assertEqual(xun_info("辛酉")["dun_gan"]["寅"], "甲")

    def test_invalid_pillar_is_rejected(self):
        with self.assertRaises(ValueError):
            sexagenary_index("甲丑")


if __name__ == "__main__":
    unittest.main()

