from types import MappingProxyType


MONTH_GENERALS = MappingProxyType({
    "雨水": ("亥", "登明"), "春分": ("戌", "河魁"), "谷雨": ("酉", "从魁"),
    "小满": ("申", "传送"), "夏至": ("未", "小吉"), "大暑": ("午", "胜光"),
    "处暑": ("巳", "太乙"), "秋分": ("辰", "天罡"), "霜降": ("卯", "太冲"),
    "小雪": ("寅", "功曹"), "冬至": ("丑", "大吉"), "大寒": ("子", "神后"),
})

STEM_LODGES = MappingProxyType({
    "甲": "寅", "乙": "辰", "丙": "巳", "丁": "未", "戊": "巳",
    "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑",
})

NOBLE_BRANCHES = MappingProxyType({
    "甲": ("丑", "未"), "戊": ("丑", "未"), "庚": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"), "丙": ("亥", "酉"),
    "丁": ("亥", "酉"), "壬": ("巳", "卯"), "癸": ("巳", "卯"), "辛": ("午", "寅"),
})

HEAVENLY_GENERALS = ("贵人", "螣蛇", "朱雀", "六合", "勾陈", "青龙", "天空", "白虎", "太常", "玄武", "太阴", "天后")

TRANSMISSION_COVERAGE = tuple(MappingProxyType(item) for item in (
    {"path": "贼克", "status": "implemented_engineering_baseline", "rule_id": "LR-TRANSMISSION-001"},
    {"path": "克", "status": "implemented_engineering_baseline", "rule_id": "LR-TRANSMISSION-001"},
    {"path": "比用", "status": "implemented_engineering_baseline", "rule_id": "LR-TRANSMISSION-001"},
    {"path": "涉害", "status": "pending_rule_selection", "rule_id": "LR-COVERAGE-001"},
    {"path": "遥克", "status": "implemented_engineering_baseline", "rule_id": "LR-REMOTE-001"},
    {"path": "昴星", "status": "implemented_engineering_baseline", "rule_id": "LR-STAR-001"},
    {"path": "别责", "status": "pending_rule_selection", "rule_id": "LR-COVERAGE-001"},
    {"path": "八专", "status": "pending_rule_selection", "rule_id": "LR-COVERAGE-001"},
    {"path": "伏吟", "status": "pending_rule_selection", "rule_id": "LR-COVERAGE-001"},
    {"path": "返吟", "status": "pending_rule_selection", "rule_id": "LR-COVERAGE-001"},
))
