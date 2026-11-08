"""玄空飞星：三元九运、二十四山下卦挨星盘与旺衰格局条件。

口径说明：
- 下卦挨星为蒋大鸿《地理辨正》传承的通行法（本地多来源典籍库含《地理辨正》《青囊经》《宅经》
  及《沈氏玄空學》卷首至卷六）；
- 替卦起星盘已按库内《沈氏玄空學》起星图 216 局实例实现为工程基线，
  经 `include_tihua_chart=true` 显式请求才提供、默认关闭，不覆盖下卦挨星盘；
  替星表寅午庚丁由库内两套挨星口诀（弼星9）与 430 条可解析起星图实例逆行计算裁定为 9，
  原工程草稿 8（左辅）已废弃（裁定记录见 TIHUA_TABLE_DISCREPANCY）；
  中宫五按原典「五到向，无替可寻」不替、仍 5 入中，顺逆视山向阴阳；
  产物仍属工程基线，专家签署与正式规则发布流程另行，不含吉凶断语；
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

# 玄空替卦（起星）挨星表——据库内《沈氏玄空學》「二十四山配九星图」两套口诀：
#   吹齑子简易挨星口诀「子癸甲申贪狼寻，坤壬乙卯未巨门。乾巽六位皆武曲，
#     艮丙辛酉丑破军。若向寅午庚丁上，一律挨来是弼星。」
#   蒋大鸿授姜汝皋挨星口诀「…寅午庚丁上，右弼四星临。」
# 二者一致：寅午庚丁 = 9（右弼）。早先工程草稿误记为 8（左辅），现据典订正。
# 逆行验证：库内起星图 216 局（432 条山/向，语料缺 1 行、1 行 OCR 不可解析，
#   另 4 处单字 OCR 已按同句源山订正）共 430 条可解析「到星→入中星」实例中，
#   到星7/8/9 用寅午庚丁时均入中9，入中结果从不出现 8，与原典弼星 9 吻合。
TIHUA_STAR = {
    "子": 1, "癸": 1, "甲": 1, "申": 1,
    "坤": 2, "壬": 2, "乙": 2, "卯": 2, "未": 2,
    "戌": 6, "乾": 6, "亥": 6, "辰": 6, "巽": 6, "巳": 6,
    "艮": 7, "丙": 7, "辛": 7, "酉": 7, "丑": 7,
    "寅": 9, "午": 9, "庚": 9, "丁": 9,
}
TIHUA_RULE_ID = "FS-XUANKONG-TIHUA-001"
TIHUA_CHART_RULE_ID = "FS-XUANKONG-TIHUA-002"

# 保留原典口径别名以兼容既有调用；两表现已一致，不再是「并列冲突两表」。
TIHUA_STAR_LIBRARY_CLASSIC = TIHUA_STAR

# 口径裁定的可复核记录（原工程草稿 8 → 据典 9），保留历史以便追溯。
TIHUA_TABLE_DISCREPANCY = {
    "status": "resolved_by_library_classics",
    "signed": False,
    "signature_status": "unsigned",
    "requires_expert_signoff": True,
    "mountains": ["寅", "午", "庚", "丁"],
    "resolved_value": {"star": 9, "name": "弼星（右弼）"},
    "superseded_value": {"star": 8, "name": "左辅", "table": "工程草稿（已废弃）"},
    "library_quotes": [
        "若向寅午庚丁上，一律挨来是弼星",
        "寅午庚丁上，右弼四星临",
    ],
    "library_examples": [
        "九之天元即午，挨弼星，仍九入中，午阴逆行",
        "八之人元即寅，挨弼星，故不用八而以九入中，寅阳顺行",
    ],
    "reverse_computation": "库内起星图216局中430条可解析「到星→入中星」实例逆推：到星7/8/9 用寅午庚丁时均入中9，无一入中8",
    "note": "口径已由库内原典明文 + 起星图标准案例逆行计算裁定为弼星9，但尚无专家签署；产物仍为工程基线，不含吉凶断语。",
}

# 洛书数 → 宫位：到山/到向的运星数，据此宫取与坐/向同元龙之山为替星山。
NUMBER_PALACE = {1: "坎", 2: "坤", 3: "震", 4: "巽", 5: "中",
                 6: "乾", 7: "兑", 8: "艮", 9: "离"}
# 三元龙在每宫三山中的次序（与 yuan_dragon 的 地/天/人 一致）。
YUAN_INDEX = {"地": 0, "天": 1, "人": 2}


def period_for_year(year):
    """三元九运：上元一运起于 1864，每运 20 年，九运 180 年一轮回。

    2043 之后并非恒为九运，而是重新起上元一运（2044–2063）——POST 端点允许
    year 至 2100，早先在此区间无条件返回 9 属算法错误。
    """
    year = int(year)
    if year < PERIODS[0][1]:
        raise ValueError("year {} earlier than 上元一运 1864".format(year))
    return ((year - PERIODS[0][1]) // 20) % 9 + 1


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


def _tihua_entering(period_chart, palace, yuan, star_table, mountain_name):
    """按《沈氏玄空學》起星图口径推导一路（山盘或向盘）的入中替星并飞布九宫。

    原典实例：「八到山，八之天元即艮，挨破军，故不用八而以七入中，艮阳顺行」：
      到山运星 8 → 洛书艮宫 → 取与坐山同元龙（天元）之山「艮」→ 替星表得破军 7
      → 以 7 入中，顺逆按替星山「艮」的阴阳（阳→顺飞）飞布。

    中宫五（原典「五到向，无替可寻，四正逆行」）：五无方位、无元龙山可取替星，
    故「无替可寻」＝不替，仍以 5 入中；顺逆按「中宫五数戊阳己阴，此阴阳视山向为准」
    以坐山/向首之字定阴阳（四正子午卯酉为阴逆行，乾巽等为阳顺行）。
    库内起星图 216 局中「五到山/向」48 例全部标注「无替可寻」，逆行计算一致。
    """
    arriving = period_chart[palace]
    number_palace = NUMBER_PALACE[arriving]
    if number_palace == "中":
        forward = mountain_name not in YIN_MOUNTAINS
        return {
            "status": "completed",
            "arriving_star": arriving,
            "number_palace": "中",
            "yuan_dragon": yuan,
            "substitute_mountain": None,
            "tihua_star": 5,
            "no_substitute": True,
            "fly_reference_mountain": mountain_name,
            "fly_direction": "顺飞" if forward else "逆飞",
            "chart": _chart(5, forward),
            "trace": [
                "运星五临中宫，中宫无方位，《沈氏玄空學》起星图作「无替可寻」，故不替、仍五入中",
                "中宫五数戊阳己阴，此阴阳视山向为准：{}属{}，故{}".format(
                    mountain_name, "阳" if forward else "阴", "顺飞" if forward else "逆飞"
                ),
            ],
        }
    substitute_mountain = PALACE_BRANCHES[number_palace][YUAN_INDEX[yuan]]
    tihua_star = star_table.get(substitute_mountain)
    if tihua_star is None:
        return {
            "status": "unresolved",
            "reason": "替星表未收录 {}（24 山应全覆盖，属异常输入）".format(substitute_mountain),
            "arriving_star": arriving, "number_palace": number_palace,
            "yuan_dragon": yuan, "substitute_mountain": substitute_mountain,
            "trace": [],
        }
    forward = substitute_mountain not in YIN_MOUNTAINS
    return {
        "status": "completed",
        "arriving_star": arriving,
        "number_palace": number_palace,
        "yuan_dragon": yuan,
        "substitute_mountain": substitute_mountain,
        "tihua_star": tihua_star,
        "fly_direction": "顺飞" if forward else "逆飞",
        "chart": _chart(tihua_star, forward),
        "trace": [
            "运星{}到{}，{}之{}元即{}（洛书{}宫）".format(
                arriving, palace, arriving, yuan, substitute_mountain, number_palace
            ),
            "{}挨星得{}，故不用{}而以{}入中，按{}阴阳{}".format(
                substitute_mountain, tihua_star, arriving, tihua_star,
                substitute_mountain, "顺飞" if forward else "逆飞",
            ),
        ],
    }


def _tihua_chart(period_chart, sitting_palace, facing_palace, sitting_yuan, facing_yuan,
                 sitting_name, facing_name):
    """构造替卦起星盘：山盘/向盘各按库内原典起星图口径独立推导。"""
    sitting = _tihua_entering(period_chart, sitting_palace, sitting_yuan,
                              TIHUA_STAR_LIBRARY_CLASSIC, sitting_name)
    facing = _tihua_entering(period_chart, facing_palace, facing_yuan,
                             TIHUA_STAR_LIBRARY_CLASSIC, facing_name)
    overall = "completed" if sitting["status"] == facing["status"] == "completed" else "unresolved"
    return {
        "rule_id": TIHUA_CHART_RULE_ID,
        "status": overall,
        "signed": False,
        "signature_status": "unsigned",
        "requires_expert_signoff": True,
        "school": "沈氏玄空學起星图（库内原典口径，工程基线）",
        "star_table": "TIHUA_STAR",
        "star_table_status": "resolved_by_library_classics",
        "sitting": sitting,
        "facing": facing,
        "resolution_record": dict(TIHUA_TABLE_DISCREPANCY),
        # 兼容旧字段名，指向同一份已裁定记录
        "table_discrepancy": dict(TIHUA_TABLE_DISCREPANCY),
        "evidence": _classic_evidence(["起星", "替卦", "寅午庚丁", "挨弼星"], limit=4),
        "note": "替卦起星盘按库内《沈氏玄空學》起星图 216 局实例实现，属可查证排盘事实（不含吉凶断语）。"
                "寅午庚丁替星口径已由库内两套挨星口诀（弼星9）与 430 条可解析起星图实例逆行计算裁定，"
                "原工程草稿8已废弃；中宫五按原典「无替可寻」不替、仍五入中，顺逆视山向阴阳。"
                "产物仍为工程基线，尚无专家签署与正式规则发布，signed=false。",
    }


def calculate_xuankong(sitting_mountain, year=None, period=None, sitting_degree=None,
                       include_tihua_reference=False, include_tihua_chart=False):
    """按坐山与运造下卦挨星盘，并给出确定性格局条件。

    `include_tihua_reference` 为 True 时附带据库内原典裁定的挨星表参考，
    仅作复核用途，不改变下卦挨星盘，也不用于任何确定性结论。
    `include_tihua_chart` 为 True 时附带按库内《沈氏玄空學》起星图 216 局推导的
    替卦起星盘（工程基线，默认关闭），同样不覆盖下卦盘、不含吉凶断语。
    """
    mountain = mountain_by_name(sitting_mountain)
    facing_name = opposite_mountain(mountain.name)
    if period is None:
        if year is None:
            raise ValueError("year or period is required")
        period = period_for_year(year)
    elif type(period) is not int or not 1 <= period <= 9:
        # 函数级校验：越界 period 会令 _fly_sequence 产出含 0/10 的非法星盘，
        # 并在 YUAN_LABELS[period] 触发 KeyError；字符串则触发 TypeError。
        raise ValueError("period must be an integer between 1 and 9")

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
    # 与旺山旺向/上山下水一致：未满足时也写入带 note 的条件项，避免下游缺项。
    # 双星判据（山向两盘同宫同星）在 24 山×9 运下恒不命中，正确口径待专家签署，
    # 此处只统一输出结构，不杜撰新判据。
    if mountain_at_sitting == facing_at_sitting:
        conditions.append({"name": "双星到坐", "met": True})
    else:
        conditions.append({"name": "双星到坐", "met": False,
                           "note": "判据待专家签署：当前按山向两盘同宫同星判定"})
    if mountain_at_facing == facing_at_facing:
        conditions.append({"name": "双星到向", "met": True})
    else:
        conditions.append({"name": "双星到向", "met": False,
                           "note": "判据待专家签署：当前按山向两盘同宫同星判定"})

    # 替卦区间判定：每山十五度，两侧各三度起替。
    # 《沈氏玄空學·論起星》：「兼一二分者，无须寻替；若兼三四分者，当用替星」——
    # 故恰 3.0 度属起替区间（闭区间 <=），早先严格 < 把边界误判为下卦。
    if sitting_degree is not None:
        degree = float(sitting_degree)
        offset = (degree + 7.5) % 15.0
        boundary_distance = min(offset, 15.0 - offset)
        # 实测度数落哪一山：每山 15 度，子山中心 0/360，MOUNTAINS 按中心度递增；
        # 取最近中心度（+0.5 四舍五入）。
        degree_mountain = MOUNTAINS[int(degree / 15.0 + 0.5) % 24].name
        ti_pu = {
            "in_ti_pu_region": boundary_distance <= TI_PU_REGION_DEGREES,
            "distance_to_boundary": round(boundary_distance, 6),
            "measured_degree": degree,
            "degree_mountain": degree_mountain,
            "degree_matches_sitting_mountain": degree_mountain == mountain.name,
            "note": "《沈氏玄空學·論起星》兼三四分当用替星（含 3.0 度边界）；替卦起星盘可由 include_tihua_chart=true 取得（据库内原典裁定，工程基线）；落入替卦区间时亦应复测坐向或人工起盘。",
        }
    else:
        ti_pu = {
            "in_ti_pu_region": None,
            "measured_degree": None,
            "degree_mountain": None,
            "degree_matches_sitting_mountain": None,
            "note": "未提供实测角度，无法判定是否落替卦区间；每山两侧各三度起替（含边界）。起星盘需 include_tihua_chart=true 显式请求，默认不提供。",
        }

    result = {
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
            "下卦挨星为通行法；替卦起星盘按库内《沈氏玄空學》起星图实现，默认不提供，产物仍属工程基线。",
            "格局条件为确定性判定，不含吉凶断语。",
        ],
    }
    if ti_pu.get("degree_matches_sitting_mountain") is False:
        result["warnings"].append(
            "实测角度 {}° 落{}山，与声明坐山{}不一致；应复测坐向后再判替卦。".format(
                ti_pu["measured_degree"], ti_pu["degree_mountain"], mountain.name
            )
        )

    if include_tihua_reference:
        result["facts"]["tihua_reference"] = {
            "rule_id": TIHUA_RULE_ID,
            "status": "resolved_by_library_classics",
            "signed": False,
            "signature_status": "unsigned",
            "requires_expert_signoff": True,
            "sitting": {"mountain": mountain.name, "tihua_star": TIHUA_STAR.get(mountain.name)},
            "facing": {"mountain": facing_name, "tihua_star": TIHUA_STAR.get(facing_name)},
            "note": "替卦挨星表已按库内《沈氏玄空學》两套口诀（寅午庚丁弼星9）与起星图216局中430条可解析实例逆行计算订正；"
                    "裁定记录见 tihua_chart.resolution_record。产物仍为工程基线，尚无专家签署，signed=false，不含吉凶断语。",
        }
        result["warnings"].append(
            "已附替卦挨星参考（据库内原典裁定，但尚无专家签署），仅供复核，不作为生产结论。"
        )

    if include_tihua_chart:
        # 显式请求才提供起星盘；与下卦挨星盘并列但不覆盖，且带完整裁定记录。
        result["facts"]["tihua_chart"] = _tihua_chart(
            period_chart, sitting_palace, facing_palace,
            yuan_dragon(mountain.name), yuan_dragon(facing_name),
            mountain.name, facing_name,
        )
        result["warnings"].append(
            "已附替卦起星盘（据库内《沈氏玄空學》起星图216局实现）：替星表口径已由原典裁定但尚无专家签署，"
            "中宫五按「无替可寻」不替；产物仍为工程基线，signed=false。"
        )

    return result


__all__ = ("calculate_xuankong", "period_for_year", "yuan_dragon", "opposite_mountain",
           "TIHUA_STAR", "TIHUA_RULE_ID", "TIHUA_STAR_LIBRARY_CLASSIC",
           "TIHUA_TABLE_DISCREPANCY", "TIHUA_CHART_RULE_ID")
