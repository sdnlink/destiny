"""排盘执行器。调用各领域引擎执行计算，返回模块结果列表。

复用现有领域引擎，不重复实现算法。
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List

from app.calendar import calendar_analysis
from app.zhouyi import auto_cast as yi_auto_cast
from app.zhouyi import manual_cast as yi_manual_cast
from app.zhouyi import number_cast as yi_number_cast
from app.zhouyi import three_number_cast as yi_three_number_cast
from app.zhouyi import time_cast as yi_time_cast
from app.meihua import auto_cast as meihua_auto_cast
from app.meihua import number_cast as meihua_number_cast
from app.meihua import three_number_cast as meihua_three_number_cast
from app.meihua import time_cast as meihua_time_cast
from app.liuyao import auto_cast as liuyao_auto_cast
from app.liuyao import coin_cast as liuyao_coin_cast
from app.liuyao import line_cast as liuyao_line_cast
from app.liuyao import number_cast as liuyao_number_cast
from app.liuyao import time_cast as liuyao_time_cast
from app.daliuren import auto_cast as liuren_auto_cast
from app.daliuren import number_cast as liuren_number_cast
from app.daliuren import time_cast as liuren_time_cast
from app.bazi import auto_cast as bazi_auto_cast
from app.bazi import time_cast as bazi_time_cast
from app.ziwei import auto_cast as ziwei_auto_cast
from app.ziwei import time_cast as ziwei_time_cast
from app.qimen import auto_cast as qimen_auto_cast
from app.qimen import time_cast as qimen_time_cast


def _execute_one(module: str, method: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """执行单个模块计算。"""
    if module == "calendar" and method == "analyze":
        return calendar_analysis(**payload)

    if module == "zhouyi":
        if method == "manual":
            return yi_manual_cast(payload["lines"])
        if method == "auto":
            return yi_auto_cast(**payload)
        if method == "time":
            return yi_time_cast(**payload)
        if method == "numbers":
            return yi_number_cast(payload["lower_number"], payload["upper_number"])
        if method == "three_numbers":
            return yi_three_number_cast(*payload["numbers"], mapping_version=payload.get("mapping_version", "earlier-heaven-number-v1"))

    if module == "meihua":
        if method == "time":
            return meihua_time_cast(**payload)
        if method == "auto":
            return meihua_auto_cast(**payload)
        if method == "numbers":
            return meihua_number_cast(payload["upper_number"], payload["lower_number"])
        if method == "three_numbers":
            return meihua_three_number_cast(*payload["numbers"])

    if module == "liuyao":
        if method == "time":
            return liuyao_time_cast(**payload)
        if method == "auto":
            return liuyao_auto_cast(**payload)
        if method == "numbers":
            lower = payload.pop("lower_number")
            upper = payload.pop("upper_number")
            return liuyao_number_cast(lower, upper, **payload)
        if method == "lines":
            lines = payload.pop("lines")
            return liuyao_line_cast(lines, **payload)
        if method == "coins":
            coins = payload.pop("coins")
            return liuyao_coin_cast(coins, **payload)

    if module == "liuren":
        if method == "time":
            return liuren_time_cast(**payload)
        if method == "auto":
            return liuren_auto_cast(**payload)
        if method == "numbers":
            number = payload.pop("number")
            return liuren_number_cast(number, **payload)

    if module == "bazi":
        if method == "time":
            return bazi_time_cast(**payload)
        if method == "auto":
            return bazi_auto_cast(**payload)

    if module == "ziwei":
        if method == "time":
            return ziwei_time_cast(**payload)
        if method == "auto":
            return ziwei_auto_cast(**payload)

    if module == "qimen":
        if method == "time":
            return qimen_time_cast(**payload)
        if method == "auto":
            return qimen_auto_cast(**payload)

    raise ValueError(f"unsupported calculation: {module}/{method}")


def execute_calculations(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """并行执行多个计算请求，返回模块结果列表。

    Returns:
        [{module, method, result}, ...]
    """
    with ThreadPoolExecutor(max_workers=max(1, len(requests))) as executor:
        futures = [
            executor.submit(_execute_one, req["module"], req["method"], req["input"])
            for req in requests
        ]
        results = [future.result() for future in futures]

    return [
        {"module": req["module"], "method": req["method"], "result": result}
        for req, result in zip(requests, results)
    ]
