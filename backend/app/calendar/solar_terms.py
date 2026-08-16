from datetime import datetime
from types import MappingProxyType

import pytz


REFERENCE_TIMEZONE_NAME = "Asia/Shanghai"
REFERENCE_TIMEZONE = pytz.timezone(REFERENCE_TIMEZONE_NAME)
SOLAR_TERM_ALGORITHM = "lunar-python-1.4.8-shouxing-term-table"
SOLAR_TERM_NAMES = (
    "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
    "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑",
    "白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至",
)
MONTH_JIE_BRANCH = MappingProxyType({
    "立春": "寅", "惊蛰": "卯", "清明": "辰", "立夏": "巳",
    "芒种": "午", "小暑": "未", "立秋": "申", "白露": "酉",
    "寒露": "戌", "立冬": "亥", "大雪": "子", "小寒": "丑",
})


def serialize_jieqi(value, output_timezone):
    if value is None:
        return None
    reference_naive = datetime.strptime(value.getSolar().toYmdHms(), "%Y-%m-%d %H:%M:%S")
    reference_time = REFERENCE_TIMEZONE.localize(reference_naive)
    local_time = reference_time.astimezone(output_timezone)
    return {
        "name": value.getName(),
        "datetime": local_time.strftime("%Y-%m-%d %H:%M:%S"),
        "local_datetime": local_time.isoformat(),
        "reference_datetime": reference_time.isoformat(),
        "utc_datetime": reference_time.astimezone(pytz.UTC).isoformat(),
    }


def solar_term_context(lunar, output_timezone):
    previous = serialize_jieqi(lunar.getPrevJieQi(), output_timezone)
    current = serialize_jieqi(lunar.getCurrentJieQi(), output_timezone)
    next_term = serialize_jieqi(lunar.getNextJieQi(), output_timezone)
    previous_jie = serialize_jieqi(lunar.getPrevJie(), output_timezone)
    next_jie = serialize_jieqi(lunar.getNextJie(), output_timezone)
    return {
        "previous": previous,
        "current": current,
        "next": next_term,
        "previous_month_boundary": previous_jie,
        "next_month_boundary": next_jie,
        "reference_timezone": REFERENCE_TIMEZONE_NAME,
        "algorithm": SOLAR_TERM_ALGORITHM,
        "precision": "second",
        "supported_term_count": len(SOLAR_TERM_NAMES),
    }
