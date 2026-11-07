"""调度表 ↔ 统一分发表的一致性。

`workflow/scheduler.py` 决定"排哪些请求"，`common/calculation_dispatch.py` 决定
"这些请求由谁执行"。两张表分开维护过一段时间，结果新增方法时只有一边更新，
调用时才暴露成 `unsupported calculation`。这里把两边钉在一起。
"""

import unittest

from app.common.calculation_dispatch import CALCULATION_HANDLERS, execute_calculation
from app.workflow import scheduler

CASTING_METHODS = ("auto", "time", "numbers", "manual", "coins", "three_numbers")

SOURCE = {
    "local_datetime": "2026-11-05T10:00:00",
    "timezone": "Asia/Shanghai",
    "cast_nonce": "scheduler-contract-nonce-01",
    "gender": "女",
    "numbers": [3, 5, 7],
    "upper_number": 3,
    "lower_number": 5,
    "number": 9,
}


class SchedulerDispatchAlignmentTests(unittest.TestCase):
    def test_every_scheduled_combination_is_registered(self):
        for system in scheduler.REQUEST_BUILDERS:
            for method in CASTING_METHODS:
                requests = scheduler.build_calculation_requests([system], method, SOURCE)
                for request in requests:
                    key = (request["module"], request["method"])
                    self.assertIn(
                        key,
                        CALCULATION_HANDLERS,
                        f"调度表排出了未注册的调用 {key}（system={system}, casting_method={method}）",
                    )

    def test_schedulable_methods_are_all_reachable(self):
        # zhouyi 与 fengshui 不走工作流调度（周易由独立端点/梅花覆盖，风水是独立入口），
        # 所以只要求这些体系的方法全部可达。
        schedulable = {"calendar": {"analyze"}, "meihua": {"auto", "time", "numbers", "three_numbers"},
                       "liuyao": {"auto", "time", "numbers", "lines", "coins"},
                       "qimen": {"auto", "time"}, "liuren": {"auto", "time", "numbers"},
                       "bazi": {"auto", "time"}, "ziwei": {"auto", "time"}}
        produced = set()
        for system in scheduler.REQUEST_BUILDERS:
            for method in CASTING_METHODS:
                for request in scheduler.build_calculation_requests([system], method, SOURCE):
                    produced.add((request["module"], request["method"]))
        produced.add(("calendar", "analyze"))
        for module, methods in schedulable.items():
            reachable = {method for name, method in produced if name == module}
            self.assertEqual(methods - reachable, set(), f"{module} 有方法不可达：{methods - reachable}")

    def test_default_systems_build_meihua_and_liuyao(self):
        systems, _ = scheduler.select_systems("auto")
        requests = scheduler.build_calculation_requests(systems, "auto", SOURCE)
        keys = [(request["module"], request["method"]) for request in requests]
        self.assertEqual(keys, [("calendar", "analyze"), ("meihua", "auto"), ("liuyao", "auto")])

    def test_unknown_system_is_skipped_without_empty_plate(self):
        requests = scheduler.build_calculation_requests(["nonexistent"], "auto", SOURCE)
        self.assertEqual([request["module"] for request in requests], ["calendar"])

    def test_scheduled_requests_actually_execute(self):
        """排出来的请求要真能跑通，而不是只存在于表里。"""
        for system in scheduler.REQUEST_BUILDERS:
            for method in CASTING_METHODS:
                requests = scheduler.build_calculation_requests([system], method, SOURCE)
                for request in requests:
                    result = execute_calculation(request["module"], request["method"], request["input"])
                    self.assertIsInstance(result, dict, f"{request['module']}/{request['method']} 未返回盘面")


if __name__ == "__main__":
    unittest.main()
