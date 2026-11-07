"""模块/方法 → 引擎调用的唯一分发表。

此前 `workflow/casting.py` 与 `core/validation.py` 各自维护一份 module/method 分发，
两边很容易漂移（一个新增方法另一个没跟上，调用时才发现）。这里收成一张表，
两处都从这里取。

调用约定统一为 `handler(payload: dict) -> result`，handler 内部自己取需要的键，
外层不会因为 pop 而改写入参。
"""

from typing import Any, Callable, Dict, Tuple

from app.bazi import auto_cast as bazi_auto_cast
from app.bazi import liunian_cast as bazi_liunian_cast
from app.bazi import time_cast as bazi_time_cast
from app.calendar import calendar_analysis
from app.daliuren import auto_cast as liuren_auto_cast
from app.daliuren import number_cast as liuren_number_cast
from app.daliuren import time_cast as liuren_time_cast
from app.fengshui import analyze_measurements as fengshui_measurements
from app.fengshui import calculate_direction as fengshui_direction
from app.liuyao import auto_cast as liuyao_auto_cast
from app.liuyao import coin_cast as liuyao_coin_cast
from app.liuyao import line_cast as liuyao_line_cast
from app.liuyao import number_cast as liuyao_number_cast
from app.liuyao import time_cast as liuyao_time_cast
from app.meihua import auto_cast as meihua_auto_cast
from app.meihua import number_cast as meihua_number_cast
from app.meihua import three_number_cast as meihua_three_number_cast
from app.meihua import time_cast as meihua_time_cast
from app.qimen import auto_cast as qimen_auto_cast
from app.qimen import time_cast as qimen_time_cast
from app.zhouyi import auto_cast as yi_auto_cast
from app.zhouyi import manual_cast as yi_manual_cast
from app.zhouyi import number_cast as yi_number_cast
from app.zhouyi import three_number_cast as yi_three_number_cast
from app.zhouyi import time_cast as yi_time_cast
from app.ziwei import auto_cast as ziwei_auto_cast
from app.ziwei import time_cast as ziwei_time_cast


CALCULATION_HANDLERS: Dict[Tuple[str, str], Callable[[Dict[str, Any]], Any]] = {
    ("calendar", "analyze"): lambda payload: calendar_analysis(**payload),
    ("zhouyi", "manual"): lambda payload: yi_manual_cast(payload["lines"]),
    ("zhouyi", "auto"): lambda payload: yi_auto_cast(**payload),
    ("zhouyi", "time"): lambda payload: yi_time_cast(**payload),
    ("zhouyi", "numbers"): lambda payload: yi_number_cast(payload["lower_number"], payload["upper_number"]),
    ("zhouyi", "three_numbers"): lambda payload: yi_three_number_cast(
        *payload["numbers"],
        mapping_version=payload.get("mapping_version", "earlier-heaven-number-v1"),
    ),
    ("meihua", "time"): lambda payload: meihua_time_cast(**payload),
    ("meihua", "auto"): lambda payload: meihua_auto_cast(**payload),
    ("meihua", "numbers"): lambda payload: meihua_number_cast(payload["upper_number"], payload["lower_number"]),
    ("meihua", "three_numbers"): lambda payload: meihua_three_number_cast(*payload["numbers"]),
    ("liuyao", "time"): lambda payload: liuyao_time_cast(**payload),
    ("liuyao", "auto"): lambda payload: liuyao_auto_cast(**payload),
    ("liuyao", "numbers"): lambda payload: _liuyao_numbers(payload),
    ("liuyao", "lines"): lambda payload: _liuyao_lines(payload),
    ("liuyao", "coins"): lambda payload: _liuyao_coins(payload),
    ("liuren", "time"): lambda payload: liuren_time_cast(**payload),
    ("liuren", "auto"): lambda payload: liuren_auto_cast(**payload),
    ("liuren", "numbers"): lambda payload: _liuren_numbers(payload),
    ("bazi", "time"): lambda payload: bazi_time_cast(**payload),
    ("bazi", "auto"): lambda payload: bazi_auto_cast(**payload),
    ("bazi", "liunian"): lambda payload: bazi_liunian_cast(**payload),
    ("ziwei", "time"): lambda payload: ziwei_time_cast(**payload),
    ("ziwei", "auto"): lambda payload: ziwei_auto_cast(**payload),
    ("qimen", "time"): lambda payload: qimen_time_cast(**payload),
    ("qimen", "auto"): lambda payload: qimen_auto_cast(**payload),
    ("fengshui", "direction"): lambda payload: fengshui_direction(**payload),
    ("fengshui", "measurements"): lambda payload: fengshui_measurements(payload["measurements"]),
}


def _liuyao_numbers(payload):
    values = dict(payload)
    lower_number = values.pop("lower_number")
    upper_number = values.pop("upper_number")
    return liuyao_number_cast(lower_number, upper_number, **values)


def _liuyao_lines(payload):
    values = dict(payload)
    lines = values.pop("lines")
    return liuyao_line_cast(lines, **values)


def _liuyao_coins(payload):
    values = dict(payload)
    coins = values.pop("coins")
    return liuyao_coin_cast(coins, **values)


def _liuren_numbers(payload):
    values = dict(payload)
    number = values.pop("number")
    return liuren_number_cast(number, **values)


def execute_calculation(module: str, method: str, payload: Dict[str, Any]) -> Any:
    """按 module/method 调用对应引擎。未知组合直接报错，不静默返回空结果。"""
    handler = CALCULATION_HANDLERS.get((module, method))
    if handler is None:
        raise ValueError("unsupported calculation: {}/{}".format(module, method))
    return handler(payload)


def supported_calculations() -> Tuple[Tuple[str, str], ...]:
    return tuple(sorted(CALCULATION_HANDLERS))
