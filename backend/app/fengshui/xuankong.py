"""玄空飞星：三元九运、二十四山下卦挨星盘与旺衰格局条件。

口径说明：
- 下卦挨星为蒋大鸿《地理辨正》传承的通行法（本地多来源典籍库含《地理辨正》《青囊经》《宅经》
  及《沈氏玄空學》卷首至卷六）；
- 替卦起星表尚未工程化、替卦盘待专家口径签署，暂不提供；
  坐向落替卦区间时明确提示须复测或人工起盘；
- 旺山旺向/上山下水/双星到坐到向为确定性格局条件，不含吉凶断语。
"""

from app.common.classics import get_library

from .rules import MOUNTAINS

ENGINE_VERSION = "fengshui-xuankong-engine-1.0.0"

# 三元九运（通行划分，立春分界由调用方确认）。
PERIODS = (
    (1, 1864, 1883), (2, 1884, 1903), (3, 1904, 1923),
    (4, 1924, 1943), (5, 1944, 1963), (6, 1964, 1983),
    (7, 1984, 2003), (8, 2004, 2023), (9, 2024, 2043),
)

PALACE_ORDER = ("坎", "坤", "震", "巽", "中", "乾", "兑", "艮", "离")
# 洛书飞行次序：入中之后依次到乾、兑、艮、离、坎、坤、震、巽。
FLY_ORDER = ("中", "乾", "兑", "艮", "离", "坎", "坤", "震", "巽")
PALACE_BRANCHES = {
    "坎": ("壬", "子", "癸"), "艮": ("丑", "艮", "寅"), "震": ("甲", "卯", "乙"),
    "巽": ("辰", "巽", "巳"), "离": ("丙", "午", "丁"), "坤": ("未", "坤", "申"),
    "兑": ("庚", "酉", "辛"), "乾": ("戌", "乾", "亥"),
}

# 三元龙阴阳：辰戌丑未、子午卯酉、乙辛丁癸为阴（逆飞），余为阳（顺飞）。
YIN_MOUNTAINS = frozenset((
    "辰", "戌", "丑", "未", "子", "午", "卯", "酉", "乙", "辛", "丁", "癸",
))

# 每山十五度：中间九度用下卦，两侧各三度起替（沈氏口径）。
TI_PU_REGION_DEGREES = 3.0

YUAN_LABELS = {1: "上元", 2: "上元", 3: "上元", 4: "中元", 5: "中元", 6: "中元",
               7: "下元", 8: "下元", 9: "下元"}


def period_for_year(year):
    year = int(year)
    for number, start, end in PERIODS:
        if start <= year <= end:
            return number
    if year < PERIODS[0][1]:
        raise ValueError("year {} earlier than 上元一运 1864".format(year))
    return 9


def mountain_by_name(name):
    for mountain in MOUNTAINS:
        if mountain.name == name:
            return mountain
    raise ValueError("unknown mountain: {}".format(name))


def palace_of_mountain(name):
    for palace, branches in PALACE_BRANCHES.items():
        if name in branches:
            return palace
    raise ValueError("unknown mountain: {}".format(name))


def yuan_dragon(name):
    """三元龙：每宫三山顺时针依次为地、天、人。"""
    branches = PALACE_BRANCHES[palace_of_mountain(name)]
    return ("地", "天", "人")[branches.index(name)]


def opposite_mountain(name):
    mountain = mountain_by_name(name)
    index = (mountain.ordinal - 1 + 12) % 24
    return MOUNTAINS[index].name


def _fly_sequence(start_number, forward):
    sequence = [start_number]
    step = 1 if forward else -1
    current = start_number
    for _ in range(8):
        current = (current - 1 + step) % 9 + 1
        sequence.append(current)
    return sequence


def _chart(entering_number, forward):
    """入中星按顺逆飞布九宫：{宫位: 星数}。入中星落中宫，余按洛书轨迹。"""
    return dict(zip(FLY_ORDER, _fly_sequence(entering_number, forward)))


def _classic_evidence(queries, limit=4):
    try:
        library = get_library()
        if not library.available:
            return []
        return library.evidence(queries, category="kanyu", limit=limit)
    except Exception:
        return []


def calculate_xuankong(sitting_mountain, year=None, period=None, sitting_degree=None):
    """按坐山与运造下卦挨星盘，并给出确定性格局条件。"""
    mountain = mountain_by_name(sitting_mountain)
    facing_name = opposite_mountain(mountain.name)
    if period is None:
        if year is None:
            raise ValueError("year or period is required")
        period = period_for_year(year)

    sitting_forward = mountain.name not in YIN_MOUNTAINS
    facing_forward = facing_name not in YIN_MOUNTAINS

    sitting_palace = palace_of_mountain(mountain.name)
    facing_palace = palace_of_mountain(facing_name)

    period_chart = _chart(period, True)
    mountain_chart = _chart(period_chart[sitting_palace], sitting_forward)
    facing_chart = _chart(period_chart[facing_palace], facing_forward)

    grid = []
    for palace in PALACE_ORDER:
        grid.append({
            "palace": palace,
            "period_star": period_chart[palace],
            "mountain_star": mountain_chart[palace],
            "facing_star": facing_chart[palace],
        })

    conditions = []
    mountain_at_sitting = mountain_chart[sitting_palace]
    facing_at_facing = facing_chart[facing_palace]
    mountain_at_facing = mountain_chart[facing_palace]
    facing_at_sitting = facing_chart[sitting_palace]
    if mountain_at_sitting == period and facing_at_facing == period:
        conditions.append({"name": "旺山旺向", "met": True})
    else:
        conditions.append({"name": "旺山旺向", "met": False,
                           "note": "须山星当运到坐且向星当运到向"})
    if mountain_at_facing == period and facing_at_sitting == period:
        conditions.append({"name": "上山下水", "met": True})
    else:
        conditions.append({"name": "上山下水", "met": False,
                           "note": "山星当运到向、向星当运到坐"})
    if mountain_at_sitting == facing_at_sitting:
        conditions.append({"name": "双星到坐", "met": True})
    if mountain_at_facing == facing_at_facing:
        conditions.append({"name": "双星到向", "met": True})

    # 替卦区间判定：每山十五度，两侧各三度起替；替卦盘待专家口径签署，不作替卦盘。
    if sitting_degree is not None:
        offset = (float(sitting_degree) + 7.5) % 15.0
        boundary_distance = min(offset, 15.0 - offset)
        ti_pu = {
            "in_ti_pu_region": boundary_distance < TI_PU_REGION_DEGREES,
            "distance_to_boundary": round(boundary_distance, 6),
            "measured_degree": float(sitting_degree),
            "note": "《沈氏玄空學》原文已在库；替卦起星表尚未工程化，替卦盘未提供；落入替卦区间时应复测坐向或人工起盘。",
        }
    else:
        ti_pu = {
            "in_ti_pu_region": None,
            "measured_degree": None,
            "note": "未提供实测角度，无法判定是否落替卦区间；每山两侧各三度起替。替卦盘待专家口径签署，未提供。",
        }

    return {
        "schema_version": "1.0",
        "system": "fengshui",
        "school": "xuankong-xiagua-engineering-baseline",
        "engine_version": ENGINE_VERSION,
        "algorithm_version": ENGINE_VERSION,
        "facts": {
            "sitting_mountain": mountain.name,
            "facing_mountain": facing_name,
            "sitting_yuan_dragon": yuan_dragon(mountain.name),
            "facing_yuan_dragon": yuan_dragon(facing_name),
            "period": period,
            "period_label": "{}{}运".format(YUAN_LABELS[period], period),
            "grid": grid,
            "fly_direction": {
                "sitting": "顺飞" if sitting_forward else "逆飞",
                "facing": "顺飞" if facing_forward else "逆飞",
                "note": "阴阳依三元龙：辰戌丑未、子午卯酉、乙辛丁癸逆飞，余顺飞",
            },
            "conditions": conditions,
            "ti_pu": ti_pu,
        },
        "evidence": _classic_evidence(["挨星", "三元", "九宮", "二十四山"]),
        "warnings": [
            "下卦挨星为通行法；替卦盘待专家口径签署，未提供。",
            "格局条件为确定性判定，不含吉凶断语。",
        ],
    }


__all__ = ("calculate_xuankong", "period_for_year", "yuan_dragon", "opposite_mountain")
