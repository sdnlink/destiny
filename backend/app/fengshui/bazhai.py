"""八宅法：大游年歌九星、东四西四宅与命卦配宅。

口径说明：
- 大游年歌为通行传本（各派文字一致，原典《八宅明镜》《阳宅三要》维基文库暂缺，
  见 data/sources/sourcing-backlog.json；理论依据引本地语料《宅经》）；
- 命卦按通行公式（男距百减、女减四起，逢五男寄坤、女寄艮），各派结果一致；
- 输出为九星方位事实与吉凶属性，不做宅命吉凶断语。
"""

from app.common.classics import get_library

from .rules import MOUNTAINS

ENGINE_VERSION = "fengshui-bazhai-engine-1.0.0"

# 后天八卦循环；大游年歌七方按从宅卦之后起的循环序排列，本位伏位。
TRIGRAM_CYCLE = ("坎", "艮", "震", "巽", "离", "坤", "兑", "乾")

# 大游年歌：乾六天五祸绝延生；坎五天生延绝祸六；艮六绝祸生延天五；
# 震延生祸绝五天六；巽天五六祸生绝延；离六五绝延祸生天；坤天延绝生祸五六；兑生祸延绝六五天。
BAZHAI_SONG = {
    "乾": ("六煞", "天医", "五鬼", "祸害", "绝命", "延年", "生气"),
    "坎": ("五鬼", "天医", "生气", "延年", "绝命", "祸害", "六煞"),
    "艮": ("六煞", "绝命", "祸害", "生气", "延年", "天医", "五鬼"),
    "震": ("延年", "生气", "祸害", "绝命", "五鬼", "天医", "六煞"),
    "巽": ("天医", "五鬼", "六煞", "祸害", "生气", "绝命", "延年"),
    "离": ("六煞", "五鬼", "绝命", "延年", "祸害", "生气", "天医"),
    "坤": ("天医", "延年", "绝命", "生气", "祸害", "五鬼", "六煞"),
    "兑": ("生气", "祸害", "延年", "绝命", "六煞", "五鬼", "天医"),
}

STAR_INFO = {
    "生气": {"star": "贪狼", "element": "木", "nature": "吉"},
    "延年": {"star": "武曲", "element": "金", "nature": "吉"},
    "天医": {"star": "巨门", "element": "土", "nature": "吉"},
    "伏位": {"star": "辅弼", "element": "木", "nature": "吉"},
    "绝命": {"star": "破军", "element": "金", "nature": "凶"},
    "五鬼": {"star": "廉贞", "element": "火", "nature": "凶"},
    "祸害": {"star": "禄存", "element": "土", "nature": "凶"},
    "六煞": {"star": "文曲", "element": "水", "nature": "凶"},
}

TRIGRAM_INFO = {
    "坎": {"direction": "北", "east_four": True},
    "离": {"direction": "南", "east_four": True},
    "震": {"direction": "东", "east_four": True},
    "巽": {"direction": "东南", "east_four": True},
    "乾": {"direction": "西北", "east_four": False},
    "坤": {"direction": "西南", "east_four": False},
    "艮": {"direction": "东北", "east_four": False},
    "兑": {"direction": "西", "east_four": False},
}

# 命卦余数到八卦（男逢五寄坤、女逢五寄艮，通行口径）。
REMAINDER_TRIGRAMS = {1: "坎", 2: "坤", 3: "震", 4: "巽", 6: "乾", 7: "兑", 8: "艮", 9: "离"}


def mountain_by_name(name):
    for mountain in MOUNTAINS:
        if mountain.name == name:
            return mountain
    raise ValueError("unknown mountain: {}".format(name))


def trigram_of_mountain(name):
    return mountain_by_name(name).trigram


def life_trigram(birth_year, gender):
    """通行命卦公式：按出生公元年份（立春分界由调用方确认）。"""
    year = int(birth_year)
    last_two = year % 100
    if year >= 2000:
        male_base, female_base = 99 - last_two, last_two + 6
    else:
        male_base, female_base = 100 - last_two, last_two - 4
    remainder = male_base % 9 if str(gender) == "男" else female_base % 9
    remainder = remainder if remainder else 9
    if remainder == 5:
        return "坤" if str(gender) == "男" else "艮"
    return REMAINDER_TRIGRAMS[remainder]


def _directions_for_house(trigram):
    rows = []
    song = BAZHAI_SONG[trigram]

    def row(palace, star):
        info = STAR_INFO[star]
        return {
            "palace": palace,
            "direction": TRIGRAM_INFO[palace]["direction"],
            "star": star,
            "star_animal": info["star"],
            "element": info["element"],
            "nature": info["nature"],
        }

    rows.append(row(trigram, "伏位"))
    index = TRIGRAM_CYCLE.index(trigram)
    for offset, palace in enumerate(
        TRIGRAM_CYCLE[index + 1:] + TRIGRAM_CYCLE[:index]
    ):
        rows.append(row(palace, song[offset]))
    return rows


def _classic_evidence(queries, limit=4):
    try:
        library = get_library()
        if not library.available:
            return []
        return library.evidence(queries, category="yangzhai", limit=limit)
    except Exception:
        return []


def calculate_bazhai(sitting_mountain, birth_year=None, gender="男"):
    """按坐山二十四山排八宅九星；给出命卦与宅命东西四匹配事实。"""
    mountain = mountain_by_name(sitting_mountain)
    house_trigram = mountain.trigram
    east_four_house = TRIGRAM_INFO[house_trigram]["east_four"]
    directions = _directions_for_house(house_trigram)

    life = None
    match = None
    if birth_year is not None:
        life = life_trigram(birth_year, gender)
        east_four_life = TRIGRAM_INFO[life]["east_four"]
        match = {
            "life_trigram": life,
            "life_group": "东四命" if east_four_life else "西四命",
            "house_group": "东四宅" if east_four_house else "西四宅",
            "group_match": east_four_life == east_four_house,
            "auspicious_directions": [
                row["palace"] for row in directions
                if row["nature"] == "吉"
                and TRIGRAM_INFO[row["palace"]]["east_four"] == east_four_life
            ],
            "note": "宅命同组（东四配东四、西四配西四）为八宅通行配法；吉凶断语须由人工复核。",
        }

    lucky = [row["palace"] for row in directions if row["nature"] == "吉"]
    unlucky = [row["palace"] for row in directions if row["nature"] == "凶"]
    return {
        "schema_version": "1.0",
        "system": "fengshui",
        "school": "bazhai-dayou-nian-engineering-baseline",
        "engine_version": ENGINE_VERSION,
        "algorithm_version": ENGINE_VERSION,
        "facts": {
            "sitting_mountain": mountain.name,
            "sitting_trigram": house_trigram,
            "house_group": "东四宅" if east_four_house else "西四宅",
            "directions": directions,
            "lucky_directions": lucky,
            "unlucky_directions": unlucky,
            "life_match": match,
            "song": "乾六天五祸绝延生；坎五天生延绝祸六；艮六绝祸生延天五；震延生祸绝五天六；"
                    "巽天五六祸生绝延；离六五绝延祸生天；坤天延绝生祸五六；兑生祸延绝六五天",
            "song_note": "大游年歌为通行传本，各派文字一致；《八宅明鏡》《陽宅十書》原文已由公开来源补齐入库；《阳宅三要》暂未收录，理论依据并引《宅经》。",
        },
        "evidence": _classic_evidence(["陽宅", "宅", "門", "吉凶"]),
        "warnings": ["八宅输出为九星方位事实与通行配法，不含流年断语。"],
    }


__all__ = ("calculate_bazhai", "life_trigram")
