import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.casting import derive_coin_lines, derive_integer, validate_cast_nonce
from app.core.iching import auto_cast as zhouyi_auto_cast
from app.core.liuren import auto_cast as liuren_auto_cast
from app.core.liuyao import auto_cast as liuyao_auto_cast
from app.core.meihua import auto_cast as meihua_auto_cast


CALENDAR_ARGS = ("2026-08-15T16:00:00", "Asia/Shanghai")


class PersonalizedCastingTests(unittest.TestCase):
    def test_same_nonce_is_replayable(self):
        nonce = "person-0000000000000001"
        first = zhouyi_auto_cast(nonce, *CALENDAR_ARGS)
        second = zhouyi_auto_cast(nonce, *CALENDAR_ARGS)
        self.assertEqual(first["facts"]["input_lines"], second["facts"]["input_lines"])
        self.assertEqual(first["facts"]["coin_rounds"], second["facts"]["coin_rounds"])

    def test_modules_use_separate_derivation_domains(self):
        nonce = "person-0000000000000001"
        zhouyi, _ = derive_coin_lines("zhouyi-auto-coins-v1", nonce)
        liuyao, _ = derive_coin_lines("liuyao-auto-coins-v1", nonce)
        self.assertNotEqual(zhouyi, liuyao)

    def test_nonce_validation_rejects_short_or_unsafe_values(self):
        for value in ("short", "contains spaces 123", "中文凭证0000000000000000"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_cast_nonce(value)

    def test_one_hundred_independent_casts_have_expected_distribution(self):
        nonces = ["person-%020d" % index for index in range(100)]
        zhouyi = [tuple(zhouyi_auto_cast(nonce, *CALENDAR_ARGS)["facts"]["input_lines"]) for nonce in nonces]
        liuyao = [tuple(liuyao_auto_cast(nonce, *CALENDAR_ARGS)["facts"]["input_lines"]) for nonce in nonces]
        meihua = [
            (result["facts"]["original"]["ordinal"], result["facts"]["moving_line"])
            for result in (meihua_auto_cast(nonce, *CALENDAR_ARGS) for nonce in nonces)
        ]
        liuren = [liuren_auto_cast(nonce, *CALENDAR_ARGS)["facts"]["report_number"] for nonce in nonces]

        self.assertGreaterEqual(len(set(zhouyi)), 85)
        self.assertGreaterEqual(len(set(liuyao)), 85)
        self.assertGreaterEqual(len(set(meihua)), 16)
        self.assertGreaterEqual(len(set(liuren)), 10)
        self.assertEqual(len({derive_integer("identity-audit-v1", nonce, 1, 1, 2**128) for nonce in nonces}), 100)


if __name__ == "__main__":
    unittest.main()
