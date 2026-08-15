TRIGRAMS = {
    1: {"name": "乾", "symbol": "☰", "lines": (1, 1, 1), "element": "金", "direction": "西北"},
    2: {"name": "兑", "symbol": "☱", "lines": (1, 1, 0), "element": "金", "direction": "西"},
    3: {"name": "离", "symbol": "☲", "lines": (1, 0, 1), "element": "火", "direction": "南"},
    4: {"name": "震", "symbol": "☳", "lines": (1, 0, 0), "element": "木", "direction": "东"},
    5: {"name": "巽", "symbol": "☴", "lines": (0, 1, 1), "element": "木", "direction": "东南"},
    6: {"name": "坎", "symbol": "☵", "lines": (0, 1, 0), "element": "水", "direction": "北"},
    7: {"name": "艮", "symbol": "☶", "lines": (0, 0, 1), "element": "土", "direction": "东北"},
    8: {"name": "坤", "symbol": "☷", "lines": (0, 0, 0), "element": "土", "direction": "西南"},
}

TRIGRAM_BY_LINES = {value["lines"]: {"number": key, **value} for key, value in TRIGRAMS.items()}
TRIGRAM_BY_NAME = {value["name"]: {"number": key, **value} for key, value in TRIGRAMS.items()}

HEXAGRAM_NAMES = (
    "乾 坤 屯 蒙 需 讼 师 比 小畜 履 泰 否 同人 大有 谦 豫 随 蛊 临 观 噬嗑 贲 剥 复 "
    "无妄 大畜 颐 大过 坎 离 咸 恒 遁 大壮 晋 明夷 家人 睽 蹇 解 损 益 夬 姤 萃 升 困 "
    "井 革 鼎 震 艮 渐 归妹 丰 旅 巽 兑 涣 节 中孚 小过 既济 未济"
).split()

# Rows are upper trigrams, columns are lower trigrams, both in numeric order 乾兑离震巽坎艮坤.
KING_WEN_MATRIX = (
    (1, 10, 13, 25, 44, 6, 33, 12),
    (43, 58, 49, 17, 28, 47, 31, 45),
    (14, 38, 30, 21, 50, 64, 56, 35),
    (34, 54, 55, 51, 32, 40, 62, 16),
    (9, 61, 37, 42, 57, 59, 53, 20),
    (5, 60, 63, 3, 48, 29, 39, 8),
    (26, 41, 22, 27, 18, 4, 52, 23),
    (11, 19, 36, 24, 46, 7, 15, 2),
)

FIVE_ELEMENTS_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
FIVE_ELEMENTS_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}

EARTHLY_BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
EARTHLY_BRANCH_NUMBER = {name: index for index, name in enumerate(EARTHLY_BRANCHES, 1)}


def trigram_number(value):
    remainder = int(value) % 8
    return 8 if remainder == 0 else remainder


def moving_line_number(value):
    remainder = int(value) % 6
    return 6 if remainder == 0 else remainder
