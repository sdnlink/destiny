from .constants import EARTHLY_BRANCHES


HEAVENLY_STEMS = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")
STEM_ELEMENTS = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
BRANCH_ELEMENTS = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}


def polarity(value):
    if value in HEAVENLY_STEMS:
        return "阳" if HEAVENLY_STEMS.index(value) % 2 == 0 else "阴"
    if value in EARTHLY_BRANCHES:
        return "阳" if EARTHLY_BRANCHES.index(value) % 2 == 0 else "阴"
    raise ValueError("unknown stem or branch: {}".format(value))


def sexagenary_index(pillar):
    if not isinstance(pillar, str) or len(pillar) != 2:
        raise ValueError("pillar must contain one heavenly stem and one earthly branch")
    stem, branch = pillar
    if stem not in HEAVENLY_STEMS or branch not in EARTHLY_BRANCHES:
        raise ValueError("invalid sexagenary pillar: {}".format(pillar))
    for index in range(60):
        if HEAVENLY_STEMS[index % 10] == stem and EARTHLY_BRANCHES[index % 12] == branch:
            return index
    raise ValueError("stem and branch do not form a sexagenary pillar: {}".format(pillar))


def xun_info(day_pillar):
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

