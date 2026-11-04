"""Rules, tables, and correspondences for BaZi (子平八字四柱命理)."""

from types import MappingProxyType
from typing import Dict, List, Tuple

from app.common.five_elements import FIVE_ELEMENTS_CONTROLS, FIVE_ELEMENTS_GENERATES
from app.common.ganzhi import (
    BRANCH_ELEMENTS,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    STEM_ELEMENTS,
)

# 天干地支、五行属相、五行生克全部取自 app.common，
# 这里只做名称转出，避免八字模块再维护一份同样的表。
STEM_POLARITY = MappingProxyType({
    "甲": "阳", "乙": "阴", "丙": "阳", "丁": "阴", "戊": "阳",
    "己": "阴", "庚": "阳", "辛": "阴", "壬": "阳", "癸": "阴",
})

BRANCH_POLARITY = MappingProxyType({
    "子": "阳", "丑": "阴", "寅": "阳", "卯": "阴", "辰": "阳", "巳": "阴",
    "午": "阳", "未": "阴", "申": "阳", "酉": "阴", "戌": "阳", "亥": "阴",
})

# 五行生克关系
ELEMENT_GENERATING = FIVE_ELEMENTS_GENERATES
ELEMENT_OVERCOMING = FIVE_ELEMENTS_CONTROLS
ELEMENT_GENERATED_BY = MappingProxyType({v: k for k, v in ELEMENT_GENERATING.items()})
ELEMENT_OVERCOME_BY = MappingProxyType({v: k for k, v in ELEMENT_OVERCOMING.items()})

# 地支藏干表及其气运权重分值 (本气, 中气, 余气)
# 格式: {"支": [("干", 权重比, "本气/中气/余气")]}
HIDDEN_STEMS_MAP = MappingProxyType({
    "子": (("癸", 1.0, "本气"),),
    "丑": (("己", 0.6, "本气"), ("癸", 0.3, "中气"), ("辛", 0.1, "余气")),
    "寅": (("甲", 0.6, "本气"), ("丙", 0.3, "中气"), ("戊", 0.1, "余气")),
    "卯": (("乙", 1.0, "本气"),),
    "辰": (("戊", 0.6, "本气"), ("乙", 0.3, "中气"), ("癸", 0.1, "余气")),
    "巳": (("丙", 0.6, "本气"), ("戊", 0.3, "中气"), ("庚", 0.1, "余气")),
    "午": (("丁", 0.7, "本气"), ("己", 0.3, "中气")),
    "未": (("己", 0.6, "本气"), ("丁", 0.3, "中气"), ("乙", 0.1, "余气")),
    "申": (("庚", 0.6, "本气"), ("壬", 0.3, "中气"), ("戊", 0.1, "余气")),
    "酉": (("辛", 1.0, "本气"),),
    "戌": (("戊", 0.6, "本气"), ("辛", 0.3, "中气"), ("丁", 0.1, "余气")),
    "亥": (("壬", 0.7, "本气"), ("甲", 0.3, "中气")),
})

# 十神映射 (以日干为基准)
def get_ten_god(day_stem: str, target_stem: str) -> str:
    """计算 target_stem 相对于 day_stem 的十神名称。"""
    day_elem = STEM_ELEMENTS[day_stem]
    target_elem = STEM_ELEMENTS[target_stem]
    same_polar = (STEM_POLARITY[day_stem] == STEM_POLARITY[target_stem])

    if target_elem == day_elem:
        return "比肩" if same_polar else "劫财"
    if target_elem == ELEMENT_GENERATING[day_elem]:
        return "食神" if same_polar else "伤官"
    if target_elem == ELEMENT_OVERCOMING[day_elem]:
        return "偏财" if same_polar else "正财"
    if target_elem == ELEMENT_OVERCOME_BY[day_elem]:
        return "七杀" if same_polar else "正官"
    if target_elem == ELEMENT_GENERATED_BY[day_elem]:
        return "偏印" if same_polar else "正印"
    raise ValueError(f"Unknown relationship between {day_stem} and {target_stem}")

# 十二长生顺逆表
CHANGSHENG_STAGES = (
    "长生", "沐浴", "冠带", "临官", "帝旺",
    "衰", "病", "死", "墓", "绝", "胎", "养"
)

# 各天干起长生的地支与顺逆 (1为顺, -1为逆)
CHANGSHENG_START = MappingProxyType({
    "甲": ("亥", 1),
    "丙": ("寅", 1),
    "戊": ("寅", 1),
    "庚": ("巳", 1),
    "壬": ("申", 1),
    "乙": ("午", -1),
    "丁": ("酉", -1),
    "己": ("酉", -1),
    "辛": ("子", -1),
    "癸": ("卯", -1),
})

def get_twelve_stage(stem: str, branch: str) -> str:
    """获取天干在指定地支的十二长生状态。"""
    start_branch, direction = CHANGSHENG_START[stem]
    start_idx = EARTHLY_BRANCHES.index(start_branch)
    target_idx = EARTHLY_BRANCHES.index(branch)
    offset = (target_idx - start_idx) * direction % 12
    return CHANGSHENG_STAGES[offset]

# 六十甲子纳音表
NAYIN_TABLE = MappingProxyType({
    "甲子": "海中金", "乙丑": "海中金", "丙寅": "炉中火", "丁卯": "炉中火",
    "戊辰": "大林木", "己巳": "大林木", "庚午": "路旁土", "辛未": "路旁土",
    "壬申": "剑锋金", "癸酉": "剑锋金", "甲戌": "山头火", "乙亥": "山头火",
    "丙子": "涧下水", "丁丑": "涧下水", "戊寅": "城头土", "己卯": "城头土",
    "庚辰": "白蜡金", "辛巳": "白蜡金", "壬午": "杨柳木", "癸未": "杨柳木",
    "甲申": "泉中水", "乙酉": "泉中水", "丙戌": "屋上土", "丁亥": "屋上土",
    "戊子": "霹雳火", "己丑": "霹雳火", "庚寅": "松柏木", "辛卯": "松柏木",
    "壬辰": "长流水", "癸巳": "长流水", "甲午": "沙中金", "乙未": "沙中金",
    "丙申": "山下火", "丁酉": "山下火", "戊戌": "平地木", "己亥": "平地木",
    "庚子": "壁上土", "辛丑": "壁上土", "壬寅": "金箔金", "癸卯": "金箔金",
    "甲辰": "覆灯火", "乙巳": "覆灯火", "丙午": "天河水", "丁未": "天河水",
    "戊申": "大驿土", "己酉": "大驿土", "庚戌": "钗钏金", "辛亥": "钗钏金",
    "壬子": "桑柘木", "癸丑": "桑柘木", "甲寅": "大溪水", "乙卯": "大溪水",
    "丙辰": "沙中土", "丁巳": "沙中土", "戊午": "天上火", "己未": "天上火",
    "庚申": "石榴木", "辛酉": "石榴木", "壬戌": "大海水", "癸亥": "大海水",
})

# 神煞查法表
TIAN_YI_GUI_REN = MappingProxyType({
    "甲": ("丑", "未"), "戊": ("丑", "未"),
    "乙": ("子", "申"), "己": ("子", "申"),
    "丙": ("亥", "酉"), "丁": ("亥", "酉"),
    "壬": ("卯", "巳"), "癸": ("卯", "巳"),
    "庚": ("丑", "未"), "辛": ("午", "寅"),
})

WEN_CHANG_GUI_REN = MappingProxyType({
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申",
    "己": "酉", "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯",
})

YANG_REN = MappingProxyType({
    "甲": "卯", "乙": "辰", "丙": "午", "丁": "未", "戊": "午",
    "己": "未", "庚": "酉", "辛": "戌", "壬": "子", "癸": "丑",
})

LU_SHEN = MappingProxyType({
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳",
    "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
})

# 基于年支或日支查神煞
SAN_HE_GROUP = MappingProxyType({
    "申": "水", "子": "水", "辰": "水",
    "巳": "金", "酉": "金", "丑": "金",
    "寅": "火", "午": "火", "戌": "火",
    "亥": "木", "卯": "木", "未": "木",
})

YI_MA_MAP = MappingProxyType({
    "水": "寅", "金": "亥", "火": "申", "木": "巳"
})

TAO_HUA_MAP = MappingProxyType({
    "水": "酉", "金": "午", "火": "卯", "木": "子"
})

HUA_GAI_MAP = MappingProxyType({
    "水": "辰", "金": "丑", "火": "戌", "木": "未"
})

JIANG_XING_MAP = MappingProxyType({
    "水": "子", "金": "酉", "火": "午", "木": "卯"
})

# 月令查天德月德
TIAN_DE_MAP = MappingProxyType({
    "寅": "丁", "卯": "申", "辰": "壬", "巳": "辛", "午": "亥", "未": "甲",
    "申": "癸", "酉": "寅", "戌": "丙", "亥": "乙", "子": "巳", "丑": "庚",
})

YUE_DE_MAP = MappingProxyType({
    "寅": "丙", "午": "丙", "戌": "丙",
    "申": "壬", "子": "壬", "辰": "壬",
    "亥": "甲", "卯": "甲", "未": "甲",
    "巳": "庚", "酉": "庚", "丑": "庚",
})

TIAN_YI_DOC_MAP = MappingProxyType({
    "寅": "丑", "卯": "寅", "辰": "卯", "巳": "辰", "午": "巳", "未": "午",
    "申": "未", "酉": "申", "戌": "酉", "亥": "戌", "子": "亥", "丑": "子"
})
