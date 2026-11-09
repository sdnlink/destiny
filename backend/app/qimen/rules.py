"""Rules and classical tables for Qimen Dunjia (时家转盘奇门遁甲)."""

from types import MappingProxyType
from typing import Dict, List

# 九宫八卦基底 (洛书九宫)
PALACE_NAMES = MappingProxyType({
    1: {"name": "坎一宫", "trigram": "坎", "element": "水", "direction": "正北", "number": 1},
    2: {"name": "坤二宫", "trigram": "坤", "element": "土", "direction": "西南", "number": 2},
    3: {"name": "震三宫", "trigram": "震", "element": "木", "direction": "正东", "number": 3},
    4: {"name": "巽四宫", "trigram": "巽", "element": "木", "direction": "东南", "number": 4},
    5: {"name": "中五宫", "trigram": "中", "element": "土", "direction": "中央", "number": 5},
    6: {"name": "乾六宫", "trigram": "乾", "element": "金", "direction": "西北", "number": 6},
    7: {"name": "兑七宫", "trigram": "兑", "element": "金", "direction": "正西", "number": 7},
    8: {"name": "艮八宫", "trigram": "艮", "element": "土", "direction": "东北", "number": 8},
    9: {"name": "离九宫", "trigram": "离", "element": "火", "direction": "正南", "number": 9},
})

# 转盘九宫环形顺序 (沿外围顺时针：坎1 -> 艮8 -> 震3 -> 巽4 -> 离9 -> 坤2 -> 兑7 -> 乾6)
RING_PALACE_ORDER = (1, 8, 3, 4, 9, 2, 7, 6)

# 三奇六仪标准顺布序列 (戊, 己, 庚, 辛, 壬, 癸, 丁, 丙, 乙)
SAN_QI_LIU_YI = ("戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙")

# 九星及其本位地盘宫位
NINE_STARS_ORIGIN = MappingProxyType({
    1: "天蓬", 8: "天任", 3: "天冲", 4: "天辅",
    9: "天英", 2: "天芮", 7: "天柱", 6: "天心", 5: "天禽",
})

# 九星转盘顺时针环行序列 (天禽随天芮寄坤二宫)
STAR_RING_ORDER = ("天蓬", "天任", "天冲", "天辅", "天英", "天芮", "天柱", "天心")

# 八门及其本位地盘宫位
EIGHT_GATES_ORIGIN = MappingProxyType({
    1: "休门", 8: "生门", 3: "伤门", 4: "杜门",
    9: "景门", 2: "死门", 7: "惊门", 6: "开门",
    # 中五宫无门，旬首寄坤二，值使门按坤二死门起例。
    5: "死门",
})

# 八门转盘顺时针环行序列
GATE_RING_ORDER = ("休门", "生门", "伤门", "杜门", "景门", "死门", "惊门", "开门")

# 八神标准序列 (值符, 腾蛇, 太阴, 六合, 白虎, 玄武, 九地, 九天)
EIGHT_SPIRITS = ("值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天")

# 旬首与六仪对应
XUN_SHOU_YI = MappingProxyType({
    "甲子": "戊", "甲戌": "己", "甲申": "庚",
    "甲午": "辛", "甲辰": "壬", "甲寅": "癸",
})

# 二十四节气定局表 (拆补法定局数: (阳/阴遁, 上元局, 中元局, 下元局))
SOLAR_TERM_JU_TABLE = MappingProxyType({
    # 阳遁局 (冬至 -> 芒种)
    "冬至": ("阳遁", 1, 7, 4), "小寒": ("阳遁", 2, 8, 5), "大寒": ("阳遁", 3, 9, 6),
    "立春": ("阳遁", 8, 5, 2), "雨水": ("阳遁", 9, 6, 3), "惊蛰": ("阳遁", 1, 7, 4),
    "春分": ("阳遁", 3, 9, 6), "清明": ("阳遁", 4, 1, 7), "谷雨": ("阳遁", 5, 2, 8),
    "立夏": ("阳遁", 4, 1, 7), "小满": ("阳遁", 5, 2, 8), "芒种": ("阳遁", 6, 3, 9),
    # 阴遁局 (夏至 -> 大雪)
    "夏至": ("阴遁", 9, 3, 6), "小暑": ("阴遁", 8, 2, 5), "大暑": ("阴遁", 7, 1, 4),
    "立秋": ("阴遁", 2, 5, 8), "处暑": ("阴遁", 1, 4, 7), "白露": ("阴遁", 9, 3, 6),
    "秋分": ("阴遁", 7, 1, 4), "寒露": ("阴遁", 6, 9, 3), "霜降": ("阴遁", 5, 8, 2),
    "立冬": ("阴遁", 6, 9, 3), "小雪": ("阴遁", 5, 8, 2), "大雪": ("阴遁", 4, 7, 1),
})

# 九宫所辖地支（中五宫不辖地支，不参与旬空判定）
PALACE_BRANCHES = MappingProxyType({
    1: ("子",), 2: ("未", "申"), 3: ("卯",), 4: ("辰", "巳"),
    5: (), 6: ("戌", "亥"), 7: ("酉",), 8: ("丑", "寅"), 9: ("午",),
})

# 驿马：申子辰马在寅、寅午戌马在申、巳酉丑马在亥、亥卯未马在巳
HORSE_STAR = MappingProxyType({
    "申": "寅", "子": "寅", "辰": "寅",
    "寅": "申", "午": "申", "戌": "申",
    "巳": "亥", "酉": "亥", "丑": "亥",
    "亥": "巳", "卯": "巳", "未": "巳",
})


# 经典奇门格局判定表
def evaluate_qimen_patterns(
    t_stem: str,
    d_stem: str,
    gate: str,
    star: str,
    spirit: str,
    palace_number: int = 0,
) -> List[Dict[str, str]]:
    """检测当前宫位的天盘干、地盘干、八门、九星与八神组合格局。

    ``palace_number`` 用于需要落宫条件的遁格（风遁巽四宫、龙遁坎一宫、
    虎遁艮八宫）。缺省为 0 时只判定不依赖落宫条件的格局。
    """
    patterns = []
    
    # 1. 天地干吉凶格
    if t_stem == "戊" and d_stem == "丙":
        patterns.append({"name": "青龙返首", "type": "吉格", "desc": "甲木生丙火，丙火生戊土，诸事大吉，利求谋升迁。"})
    elif t_stem == "丙" and d_stem == "戊":
        patterns.append({"name": "飞鸟跌穴", "type": "吉格", "desc": "阳火入土安居，主百事称心，不求自得。"})
    elif t_stem == "丁" and d_stem == "丙":
        patterns.append({"name": "星奇顺遂", "type": "吉格", "desc": "贵人相助，功名显达。"})
    elif t_stem == "乙" and d_stem == "丁":
        patterns.append({"name": "奇仪相佐", "type": "吉格", "desc": "百事吉昌，文书大遂。"})
    elif t_stem == "庚" and d_stem == "丙":
        patterns.append({"name": "太白入荧", "type": "凶格", "desc": "金入火乡，占防盗贼破财与口舌。"})
    elif t_stem == "丙" and d_stem == "庚":
        patterns.append({"name": "荧入太白", "type": "凶格", "desc": "火克庚金，门户防忧，宜静守守正。"})
    elif t_stem == "庚" and d_stem == "戊":
        patterns.append({"name": "伏宫格", "type": "凶格", "desc": "战克困顿，不利主动作为。"})
    elif t_stem == "庚" and d_stem == "癸":
        patterns.append({"name": "大格", "type": "凶格", "desc": "庚加癸水冲克，防阻碍与波折。"})

    # 2. 三吉门
    if gate in ("开门", "休门", "生门"):
        if t_stem in ("乙", "丙", "丁"):
            patterns.append({"name": f"三奇得使（{gate}见{t_stem}奇）", "type": "吉格", "desc": "吉门配三奇，求财官司出行皆利。"})

    # 3. 三遁
    if t_stem == "丙" and d_stem == "丁" and gate == "生门":
        patterns.append({"name": "天遁", "type": "大吉格", "desc": "天时相助，乘势进取，谋事立竿见影。"})
    elif t_stem == "乙" and d_stem == "己" and gate == "开门":
        patterns.append({"name": "地遁", "type": "大吉格", "desc": "地利厚重，宜设伏藏兵、安居置产。"})
    elif t_stem == "丁" and spirit == "太阴" and gate == "休门":
        patterns.append({"name": "人遁", "type": "大吉格", "desc": "人和同心，利谈判定盟、纳贤求和。"})

    # 3.1 九遁其余六遁（《奇门法窍》《奇门旨归》通行条件；异文流派不混算）
    if t_stem == "丙" and gate == "生门" and spirit == "九天":
        patterns.append({"name": "神遁", "type": "大吉格", "desc": "丙奇、生门临九天；宜祭祀祈神、设坛布筹。"})
    if t_stem == "丁" and gate == "杜门" and spirit == "九地":
        patterns.append({"name": "鬼遁", "type": "大吉格", "desc": "丁奇、杜门临九地；宜探机设伏、隐迹藏形。"})
    if t_stem == "乙" and gate in ("开门", "休门", "生门"):
        if palace_number == 4:
            patterns.append({"name": "风遁", "type": "大吉格", "desc": "乙奇合三吉门临巽四宫；宜借势、祷风。"})
        if d_stem == "辛":
            patterns.append({"name": "云遁", "type": "大吉格", "desc": "乙奇合三吉门临地盘六辛；宜藏形、掩袭。"})
        if palace_number == 1 or d_stem == "癸":
            patterns.append({"name": "龙遁", "type": "大吉格", "desc": "乙奇合三吉门临坎一宫或六癸；宜水战、祈雨。"})
    if d_stem == "辛" and palace_number == 8 and (
        (t_stem == "乙" and gate == "休门") or (t_stem == "丙" and gate == "生门")
    ):
        patterns.append({"name": "虎遁", "type": "大吉格", "desc": "乙奇休门或丙奇生门合六辛临艮八宫；宜守隘、设伏。"})

    return patterns
