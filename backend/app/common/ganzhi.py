from types import MappingProxyType
from typing import Dict


HEAVENLY_STEMS = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")
EARTHLY_BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")
EARTHLY_BRANCH_NUMBER = MappingProxyType({name: index for index, name in enumerate(EARTHLY_BRANCHES, 1)})
STEM_ELEMENTS = MappingProxyType({
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
})
BRANCH_ELEMENTS = MappingProxyType({
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
})
BRANCH_ZODIAC = MappingProxyType({
    "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔", "辰": "龙", "巳": "蛇",
    "午": "马", "未": "羊", "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪",
})
# 六冲：子午、丑未、寅申、卯酉、辰戌、巳亥
BRANCH_CLASH = MappingProxyType({
    "子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳",
})
# 六合：子丑、寅亥、卯戌、辰酉、巳申、午未
BRANCH_COMBINE = MappingProxyType({
    "子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午",
})
# 三合局：申子辰水、亥卯未木、寅午戌火、巳酉丑金
BRANCH_TRIPLE = MappingProxyType({
    "申子辰": "水", "亥卯未": "木", "寅午戌": "火", "巳酉丑": "金",
})
# 地支三刑（两两成刑）：寅巳申、丑戌未、子卯
XING_PAIRS = frozenset({
    frozenset(("寅", "巳")), frozenset(("巳", "申")), frozenset(("寅", "申")),
    frozenset(("丑", "戌")), frozenset(("戌", "未")), frozenset(("丑", "未")),
    frozenset(("子", "卯")),
})
# 自刑：辰午酉亥
SELF_XING_BRANCHES = ("辰", "午", "酉", "亥")
# 六害：子未、丑午、寅巳、卯辰、申亥、酉戌
HAI_PAIRS = frozenset({
    frozenset(("子", "未")), frozenset(("丑", "午")), frozenset(("寅", "巳")),
    frozenset(("卯", "辰")), frozenset(("申", "亥")), frozenset(("酉", "戌")),
})
# 天干五合：甲己合土、乙庚合金、丙辛合水、丁壬合木、戊癸合火
STEM_COMBINE = MappingProxyType({
    "甲": ("己", "土"), "己": ("甲", "土"),
    "乙": ("庚", "金"), "庚": ("乙", "金"),
    "丙": ("辛", "水"), "辛": ("丙", "水"),
    "丁": ("壬", "木"), "壬": ("丁", "木"),
    "戊": ("癸", "火"), "癸": ("戊", "火"),
})


def triple_group_of(branch: str) -> str:
    """返回该地支所属三合局的三个地支，未命中返回空串。"""
    for group in BRANCH_TRIPLE:
        if branch in group:
            return group
    return ""


def branch_label(branch: str) -> str:
    """地支及其五行标签，用于生成可读的依据说明。"""
    element = BRANCH_ELEMENTS.get(branch, "")
    return "{}（{}）".format(branch, element) if element else branch


def polarity(value: str) -> str:
    if value in HEAVENLY_STEMS:
        return "阳" if HEAVENLY_STEMS.index(value) % 2 == 0 else "阴"
    if value in EARTHLY_BRANCHES:
        return "阳" if EARTHLY_BRANCHES.index(value) % 2 == 0 else "阴"
    raise ValueError("unknown stem or branch: {}".format(value))


def sexagenary_index(pillar: str) -> int:
    if not isinstance(pillar, str) or len(pillar) != 2:
        raise ValueError("pillar must contain one heavenly stem and one earthly branch")
    stem, branch = pillar
    if stem not in HEAVENLY_STEMS or branch not in EARTHLY_BRANCHES:
        raise ValueError("invalid sexagenary pillar: {}".format(pillar))
    for index in range(60):
        if HEAVENLY_STEMS[index % 10] == stem and EARTHLY_BRANCHES[index % 12] == branch:
            return index
    raise ValueError("stem and branch do not form a sexagenary pillar: {}".format(pillar))


def pillar_details(pillar: str) -> Dict[str, object]:
    index = sexagenary_index(pillar)
    stem, branch = pillar
    return {
        "text": pillar,
        "stem": stem,
        "branch": branch,
        "stem_element": STEM_ELEMENTS[stem],
        "branch_element": BRANCH_ELEMENTS[branch],
        "polarity": polarity(stem),
        "sexagenary_number": index + 1,
    }


def xun_info(day_pillar: str) -> Dict[str, object]:
    index = sexagenary_index(day_pillar)
    xun_start_index = (index // 10) * 10
    start_branch_index = xun_start_index % 12
    empty = [
        EARTHLY_BRANCHES[(start_branch_index - 2) % 12],
        EARTHLY_BRANCHES[(start_branch_index - 1) % 12],
    ]
    dun_gan = {
        EARTHLY_BRANCHES[(start_branch_index + offset) % 12]: stem
        for offset, stem in enumerate(HEAVENLY_STEMS)
    }
    return {
        "name": "{}{}旬".format(HEAVENLY_STEMS[0], EARTHLY_BRANCHES[start_branch_index]),
        "start_pillar": "{}{}".format(HEAVENLY_STEMS[0], EARTHLY_BRANCHES[start_branch_index]),
        "empty_branches": empty,
        "dun_gan": dun_gan,
    }
