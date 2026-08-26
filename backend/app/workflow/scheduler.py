"""术数调度策略。

规则：
- 用户未指定门派：默认主用梅花易数 + 六爻辅助参断
- 指定六爻：完整纳甲装卦（单体系）
- 指定奇门：时家奇门（单体系）
- 指定大六壬：月将日辰四课三传（单体系）
- 历法始终作为基线预处理
"""

from typing import List, Tuple


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
    requests = []
    # 历法始终作为基线
    calendar_input = {
        "local_datetime": casting_source.get("local_datetime", ""),
        "timezone": casting_source.get("timezone", "Asia/Shanghai"),
        "use_true_solar_time": casting_source.get("use_true_solar_time", False),
    }
    if casting_source.get("longitude") is not None:
        calendar_input["longitude"] = casting_source["longitude"]
    requests.append({"module": "calendar", "method": "analyze", "input": calendar_input})

    auto_input = {**calendar_input, "cast_nonce": casting_source.get("cast_nonce", "")}

    for system in systems:
        if system == "meihua":
            if casting_method == "numbers":
                requests.append({
                    "module": "meihua", "method": "numbers",
                    "input": {
                        "upper_number": casting_source.get("upper_number", 8),
                        "lower_number": casting_source.get("lower_number", 8),
                    },
                })
            elif casting_method == "three_numbers":
                requests.append({
                    "module": "meihua", "method": "three_numbers",
                    "input": {"numbers": casting_source.get("numbers", [8, 8, 8])},
                })
            elif casting_method == "time":
                requests.append({"module": "meihua", "method": "time", "input": calendar_input})
            else:
                requests.append({"module": "meihua", "method": "auto", "input": auto_input})

        elif system == "liuyao":
            if casting_method == "coins":
                requests.append({
                    "module": "liuyao", "method": "coins",
                    "input": {**calendar_input, "coins": casting_source.get("coins", [[2,2,2]]*6)},
                })
            elif casting_method == "manual":
                requests.append({
                    "module": "liuyao", "method": "lines",
                    "input": {**calendar_input, "lines": casting_source.get("lines", [7,8,7,8,7,8])},
                })
            elif casting_method == "numbers":
                requests.append({
                    "module": "liuyao", "method": "numbers",
                    "input": {
                        **calendar_input,
                        "lower_number": casting_source.get("lower_number", 8),
                        "upper_number": casting_source.get("upper_number", 8),
                    },
                })
            elif casting_method == "time":
                requests.append({"module": "liuyao", "method": "time", "input": calendar_input})
            else:
                requests.append({"module": "liuyao", "method": "auto", "input": auto_input})

        elif system == "qimen":
            if casting_method == "time":
                requests.append({"module": "qimen", "method": "time", "input": calendar_input})
            else:
                requests.append({"module": "qimen", "method": "auto", "input": auto_input})

        elif system == "daliuren":
            if casting_method == "numbers":
                requests.append({
                    "module": "liuren", "method": "numbers",
                    "input": {**calendar_input, "number": casting_source.get("number", 8)},
                })
            elif casting_method == "time":
                requests.append({"module": "liuren", "method": "time", "input": calendar_input})
            else:
                requests.append({"module": "liuren", "method": "auto", "input": auto_input})

        elif system == "bazi":
            gender = casting_source.get("gender", "男")
            if casting_method == "time":
                requests.append({"module": "bazi", "method": "time", "input": {**calendar_input, "gender": gender}})
            else:
                requests.append({"module": "bazi", "method": "auto", "input": {**auto_input, "gender": gender}})

        elif system == "ziwei":
            gender = casting_source.get("gender", "男")
            if casting_method == "time":
                requests.append({"module": "ziwei", "method": "time", "input": {**calendar_input, "gender": gender}})
            else:
                requests.append({"module": "ziwei", "method": "auto", "input": {**auto_input, "gender": gender}})

    return requests
