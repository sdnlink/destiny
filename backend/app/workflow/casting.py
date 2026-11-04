"""排盘执行器。调用各领域引擎执行计算，返回模块结果列表。

复用现有领域引擎，不重复实现算法；module/method 分发表集中在
app.common.calculation_dispatch，避免与校验模块各维护一份。
"""

from typing import Any, Dict, List

from app.common.calculation_dispatch import execute_calculation


def _execute_one(module: str, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """执行单个模块计算。

    分发表里的 handler 内部自行拷贝 payload，不会改写入参，
    因此快照里冻结的 calculation_requests 始终保留真实起盘参数。
    """
    return execute_calculation(module, method, payload)


def execute_calculations(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """顺序执行多个计算请求，返回模块结果列表。

    各引擎都是纯 CPU 计算，线程池受 GIL 限制没有收益，反而带来线程膨胀与
    共享状态（缓存、数据库连接）并发写风险，因此这里改为顺序执行。

    Returns:
        [{module, method, result}, ...]
    """
    results = []
    for req in requests:
        results.append(_execute_one(req["module"], req["method"], req["input"]))

    return [
        {"module": req["module"], "method": req["method"], "result": result}
        for req, result in zip(requests, results)
    ]
