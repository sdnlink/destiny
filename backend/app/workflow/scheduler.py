"""术数调度策略。

规则：
- 用户未指定门派：默认主用梅花易数 + 六爻辅助参断
- 指定六爻：完整纳甲装卦（单体系）
- 指定奇门：时家奇门（单体系）
- 指定大六壬：月将日辰四课三传（单体系）
- 历法始终作为基线预处理

调度结果是一串 `{module, method, input}` 请求，交给 `app.common.calculation_dispatch`
统一执行。这里用一张"体系 × 起盘方式 → 请求构造器"的表代替原来的 if/elif 长链，
好处是：可用组合一眼能数清，且能由测试逐个比对 `CALCULATION_HANDLERS`
（此前两处各自维护，新增方法时另一处容易漏配，直到调用时才 422/报错）。
"""

from typing import Callable, Dict, List, Tuple


SYSTEM_LABELS = {
    "calendar": "历法",
    "zhouyi": "周易",
    "meihua": "梅花易数",
    "liuyao": "六爻纳甲",
    "bazi": "八字命理",
    "ziwei": "紫微斗数",
    "qimen": "奇门遁甲",
    "daliuren": "大六壬神课",
    "fengshui": "阳宅风水",
}

# 每个体系默认的起盘方式键：表里查不到指定方法时用它（对应原来的 else 分支）
DEFAULT_METHOD = "auto"


def _meihua_numbers(source, calendar_input, auto_input):
    return {
        "module": "meihua",
        "method": "numbers",
        "input": {
            "upper_number": source.get("upper_number", 8),
            "lower_number": source.get("lower_number", 8),
        },
    }


def _meihua_three_numbers(source, calendar_input, auto_input):
    return {
        "module": "meihua",
        "method": "three_numbers",
        "input": {"numbers": source.get("numbers", [8, 8, 8])},
    }


def _with_calendar(module, method, calendar_input, **extra):
    return {"module": module, "method": method, "input": {**calendar_input, **extra}}


def _with_auto(module, method, auto_input, **extra):
    return {"module": module, "method": method, "input": {**auto_input, **extra}}


def _liuyao_coins(source, calendar_input, auto_input):
    return _with_calendar(
        "liuyao",
        "coins",
        calendar_input,
        coins=source.get("coins", [[2, 2, 2]] * 6),
    )


def _liuyao_lines(source, calendar_input, auto_input):
    return _with_calendar(
        "liuyao",
        "lines",
        calendar_input,
        lines=source.get("lines", [7, 8, 7, 8, 7, 8]),
    )


def _liuyao_numbers(source, calendar_input, auto_input):
    return _with_calendar(
        "liuyao",
        "numbers",
        calendar_input,
        lower_number=source.get("lower_number", 8),
        upper_number=source.get("upper_number", 8),
    )


def _liuren_numbers(source, calendar_input, auto_input):
    return _with_calendar("liuren", "numbers", calendar_input, number=source.get("number", 8))


def _gendered(module, method, auto_input, source, calendar_input):
    gender = source.get("gender", "男")
    if method == "time":
        return _with_calendar(module, method, calendar_input, gender=gender)
    return _with_auto(module, method, auto_input, gender=gender)


def _bazi(source, calendar_input, auto_input, method="auto"):
    return _gendered("bazi", method, auto_input, source, calendar_input)


def _ziwei(source, calendar_input, auto_input, method="auto"):
    return _gendered("ziwei", method, auto_input, source, calendar_input)


# 体系 × 起盘方式 → 请求构造器。未列出的组合退到 DEFAULT_METHOD 那一条。
REQUEST_BUILDERS: Dict[str, Dict[str, Callable[[dict, dict, dict], dict]]] = {
    "meihua": {
        "numbers": _meihua_numbers,
        "three_numbers": _meihua_three_numbers,
        "time": lambda source, calendar_input, auto_input: {
            "module": "meihua",
            "method": "time",
            "input": dict(calendar_input),
        },
        DEFAULT_METHOD: lambda source, calendar_input, auto_input: _with_auto("meihua", "auto", auto_input),
    },
    "liuyao": {
        "coins": _liuyao_coins,
        "manual": _liuyao_lines,
        "numbers": _liuyao_numbers,
        "time": lambda source, calendar_input, auto_input: _with_calendar("liuyao", "time", calendar_input),
        DEFAULT_METHOD: lambda source, calendar_input, auto_input: _with_auto("liuyao", "auto", auto_input),
    },
    "qimen": {
        "time": lambda source, calendar_input, auto_input: _with_calendar("qimen", "time", calendar_input),
        DEFAULT_METHOD: lambda source, calendar_input, auto_input: _with_auto("qimen", "auto", auto_input),
    },
    "daliuren": {
        "numbers": _liuren_numbers,
        "time": lambda source, calendar_input, auto_input: _with_calendar("liuren", "time", calendar_input),
        DEFAULT_METHOD: lambda source, calendar_input, auto_input: _with_auto("liuren", "auto", auto_input),
    },
    "bazi": {
        "time": lambda source, calendar_input, auto_input: _bazi(source, calendar_input, auto_input, "time"),
        DEFAULT_METHOD: lambda source, calendar_input, auto_input: _bazi(source, calendar_input, auto_input),
    },
    "ziwei": {
        "time": lambda source, calendar_input, auto_input: _ziwei(source, calendar_input, auto_input, "time"),
        DEFAULT_METHOD: lambda source, calendar_input, auto_input: _ziwei(source, calendar_input, auto_input),
    },
}


def select_systems(user_specified: str = "auto") -> Tuple[List[str], str]:
    """根据用户指定选择术数体系。

    Returns:
        (systems_list, scheduling_note)
    """
    if user_specified == "liuyao":
        return ["liuyao"], "用户指定六爻，执行完整纳甲装卦、世应、六亲、六神、动变爻。"
    if user_specified == "qimen":
        return ["qimen"], "用户指定奇门遁甲，执行时家奇门阴阳遁、九宫、九星、八门、八神、值符值使。"
    if user_specified == "daliuren":
        return ["daliuren"], "用户指定大六壬，执行月将日辰、四课三传、天将排布。"
    if user_specified == "meihua":
        return ["meihua"], "用户指定梅花易数，执行本卦互卦变卦、体用生克、动爻推演。"
    if user_specified == "bazi":
        return ["bazi"], "用户指定八字命理，执行四柱排盘、十神、旺衰。"
    if user_specified == "ziwei":
        return ["ziwei"], "用户指定紫微斗数，执行十二宫星曜排盘。"
    # 默认：主用梅花易数 + 六爻辅助
    return ["meihua", "liuyao"], "未指定门派，默认主用梅花易数起卦，六爻纳甲辅助参断。"


def build_calculation_requests(
    systems: List[str],
    casting_method: str,
    casting_source: dict,
) -> List[dict]:
    """根据体系列表和起盘方式构建计算请求。

    Args:
        systems: 术数体系列表
        casting_method: auto / time / numbers / manual / coins
        casting_source: 起盘素材（local_datetime, timezone, cast_nonce, numbers 等）

    Returns:
        计算请求列表 [{module, method, input}, ...]
    """
    # 历法始终作为基线
    calendar_input = {
        "local_datetime": casting_source.get("local_datetime", ""),
        "timezone": casting_source.get("timezone", "Asia/Shanghai"),
        "use_true_solar_time": casting_source.get("use_true_solar_time", False),
    }
    if casting_source.get("longitude") is not None:
        calendar_input["longitude"] = casting_source["longitude"]

    auto_input = {**calendar_input, "cast_nonce": casting_source.get("cast_nonce", "")}

    requests = [{"module": "calendar", "method": "analyze", "input": calendar_input}]
    for system in systems:
        builders = REQUEST_BUILDERS.get(system)
        if not builders:
            # 未知体系沿用原行为：跳过而不排空盘（调用方负责校验 system 取值）
            continue
        builder = builders.get(casting_method) or builders[DEFAULT_METHOD]
        requests.append(builder(casting_source, calendar_input, auto_input))
    return requests
