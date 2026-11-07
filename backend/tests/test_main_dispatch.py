"""统一分发表的守卫：端点、入参模型、引擎调用三者不得各走一套。

改这一层最容易出现"三个地方都改对了才生效"的裂缝：加一个 method 却只改一处，
线上才炸。这里把三张表钉在一起。
"""

import unittest

from app.common.calculation_dispatch import CALCULATION_HANDLERS
from app.main import CALCULATION_MODELS, app, execute

PATH_FOR = {
    ("calendar", "analyze"): "/v1/calendar/analyze",
    ("zhouyi", "manual"): "/v1/zhouyi/manual",
    ("zhouyi", "auto"): "/v1/zhouyi/auto",
    ("zhouyi", "time"): "/v1/zhouyi/time",
    ("zhouyi", "numbers"): "/v1/zhouyi/numbers",
    ("zhouyi", "three_numbers"): "/v1/zhouyi/three-numbers",
    ("meihua", "time"): "/v1/meihua/time",
    ("meihua", "auto"): "/v1/meihua/auto",
    ("meihua", "numbers"): "/v1/meihua/numbers",
    ("meihua", "three_numbers"): "/v1/meihua/three-numbers",
    ("liuyao", "time"): "/v1/liuyao/time",
    ("liuyao", "auto"): "/v1/liuyao/auto",
    ("liuyao", "numbers"): "/v1/liuyao/numbers",
    ("liuyao", "lines"): "/v1/liuyao/lines",
    ("liuyao", "coins"): "/v1/liuyao/coins",
    ("liuren", "time"): "/v1/liuren/time",
    ("liuren", "auto"): "/v1/liuren/auto",
    ("liuren", "numbers"): "/v1/liuren/numbers",
    ("ziwei", "time"): "/v1/ziwei/time",
    ("ziwei", "auto"): "/v1/ziwei/auto",
    ("bazi", "time"): "/v1/bazi/time",
    ("bazi", "auto"): "/v1/bazi/auto",
    ("bazi", "liunian"): "/v1/bazi/liunian",
    ("qimen", "time"): "/v1/qimen/time",
    ("qimen", "auto"): "/v1/qimen/auto",
    ("fengshui", "direction"): "/v1/fengshui/direction",
    ("fengshui", "measurements"): "/v1/fengshui/measurements",
}


class DispatchTableAlignmentTests(unittest.TestCase):
    def test_model_table_matches_handler_table(self):
        self.assertEqual(set(CALCULATION_MODELS), set(CALCULATION_HANDLERS))

    def test_every_combination_has_a_route(self):
        routes = {route.path for route in app.routes}
        missing = {key: PATH_FOR[key] for key in CALCULATION_MODELS if PATH_FOR[key] not in routes}
        self.assertEqual(missing, {}, f"这些组合没有 HTTP 端点：{missing}")

    def test_path_table_covers_every_combination(self):
        self.assertEqual(set(PATH_FOR), set(CALCULATION_MODELS))

    def test_unknown_combination_is_rejected(self):
        with self.assertRaises(ValueError):
            execute("nonexistent", "auto", {})


if __name__ == "__main__":
    unittest.main()
