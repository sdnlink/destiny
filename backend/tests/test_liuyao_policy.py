import unittest

from app.liuyao.engine import time_cast


class LiuyaoMonthStrengthPolicyTests(unittest.TestCase):
    def test_month_strength_policy_is_explicit(self):
        result = time_cast("2026-08-15T16:00:00", "Asia/Shanghai")
        policy = result["facts"]["month_strength_policy"]
        self.assertEqual(policy["basis"], "月建地支本气单五行生克")
        self.assertEqual(policy["levels"], ["旺", "相", "休", "囚", "死"])
        self.assertFalse(policy["hidden_stems_weighting"])
        self.assertIn("不混算", policy["note"])
        self.assertTrue(
            any("月令旺衰" in item and "不混算" in item for item in result["warnings"]),
            result["warnings"],
        )


if __name__ == "__main__":
    unittest.main()
