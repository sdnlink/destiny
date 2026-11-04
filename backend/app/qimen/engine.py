"""Core computational engine for Qimen Dunjia (时家转盘奇门遁甲)."""

from typing import Any, Dict, List, Optional

from app.calendar.engine import CalendarEngine
from app.common.ganzhi import xun_info

from .rules import (
    EIGHT_GATES_ORIGIN,
    EIGHT_SPIRITS,
    NINE_STARS_ORIGIN,
    PALACE_NAMES,
    RING_PALACE_ORDER,
    SAN_QI_LIU_YI,
    SOLAR_TERM_JU_TABLE,
    XUN_SHOU_YI,
    evaluate_qimen_patterns,
)

RULE_VERSION = "qimen-chaibu-zhuanpan-v2.0"


def _determine_yuan(day_branch: str) -> str:
    """根据日支确定上中下三元 (子午卯酉为上元，寅申巳亥为中元，辰戌丑未为下元)。"""
    if day_branch in ("子", "午", "卯", "酉"):
        return "上元"
    if day_branch in ("寅", "申", "巳", "亥"):
        return "中元"
    return "下元"


def _build_di_pan(dun_type: str, ju_number: int) -> Dict[int, str]:
    """根据阳遁/阴遁与局数排布地盘三奇六仪 (洛书九宫飞布)。"""
    di_pan = {}
    # 阳遁顺九宫飞布，阴遁逆九宫飞布（偏移量在下面的 palace_idx 计算里直接体现）

    for i, stem in enumerate(SAN_QI_LIU_YI):
        if dun_type == "阳遁":
            palace_idx = ((ju_number - 1 + i) % 9) + 1
        else:
            palace_idx = ((ju_number - 1 - i) % 9) + 1
        di_pan[palace_idx] = stem

    return di_pan


def calculate_qimen_chart(
    local_datetime: str,
    timezone: str = "Asia/Shanghai",
    longitude: Optional[float] = None,
    use_true_solar_time: bool = False,
) -> Dict[str, Any]:
    """执行时家转盘奇门遁甲拆补法定局、地盘、天盘、人盘、神盘排布与格局研判。"""
    cal_engine = CalendarEngine()
    cal_res = cal_engine.calculate(
        local_datetime=local_datetime,
        timezone=timezone,
        longitude=longitude,
        use_true_solar_time=use_true_solar_time,
    )

    ganzhi = {
        "year": cal_res["ganzhi"]["year"]["text"],
        "month": cal_res["ganzhi"]["month"]["text"],
        "day": cal_res["ganzhi"]["day"]["text"],
        "hour": cal_res["ganzhi"]["hour"]["text"],
    }

    day_branch = ganzhi["day"][1]
    hour_stem, hour_branch = ganzhi["hour"][0], ganzhi["hour"][1]

    # 1. 拆补法定局
    term_name = cal_res["solar_terms"]["previous_month_boundary"]["name"]
    # 若该节气不在常用24节气表内，取主节气名称
    if term_name not in SOLAR_TERM_JU_TABLE:
        term_name = "立春"

    dun_type, shang_ju, zhong_ju, xia_ju = SOLAR_TERM_JU_TABLE[term_name]
    yuan_type = _determine_yuan(day_branch)

    if yuan_type == "上元":
        ju_number = shang_ju
    elif yuan_type == "中元":
        ju_number = zhong_ju
    else:
        ju_number = xia_ju

    # 2. 地盘奇仪排布
    di_pan = _build_di_pan(dun_type, ju_number)

    # 3. 求时辰旬首与六仪
    hour_xun_data = xun_info(ganzhi["hour"])
    xun_start_pillar = hour_xun_data["start_pillar"]
    xun_yi = XUN_SHOU_YI.get(xun_start_pillar, "戊")

    # 找到旬首六仪在地盘所在的宫位 (值符星、值使门本位原宫)
    origin_palace = 1
    for p_num, stem in di_pan.items():
        if stem == xun_yi:
            origin_palace = p_num
            break

    zhi_fu_origin_star = NINE_STARS_ORIGIN.get(origin_palace, "天蓬")
    zhi_shi_origin_gate = EIGHT_GATES_ORIGIN.get(origin_palace, "休门")
    # 中五宫寄坤二宫
    star_source_palace = 2 if origin_palace == 5 else origin_palace
    gate_source_palace = 2 if origin_palace == 5 else origin_palace

    # 4. 天盘九星与天盘三奇六仪 (转盘法)
    # 时干所在的地盘宫位为值符星所加临的目标宫
    effective_hour_stem = xun_yi if hour_stem == "甲" else hour_stem
    target_star_palace = 1
    for p_num, stem in di_pan.items():
        if stem == effective_hour_stem:
            target_star_palace = 2 if p_num == 5 else p_num
            break

    # 计算外围八宫环形偏移量
    src_ring_idx = RING_PALACE_ORDER.index(star_source_palace)
    tgt_ring_idx = RING_PALACE_ORDER.index(target_star_palace)
    ring_offset = (tgt_ring_idx - src_ring_idx) % 8

    tian_pan_stars = {}
    tian_pan_stems = {}

    for idx, p_num in enumerate(RING_PALACE_ORDER):
        # 旋转九星
        from_ring_idx = (idx - ring_offset) % 8
        from_palace = RING_PALACE_ORDER[from_ring_idx]
        star_name = NINE_STARS_ORIGIN[from_palace]
        tian_pan_stars[p_num] = star_name

        # 携带原宫地盘奇仪到新宫
        carried_stem = di_pan[from_palace]
        tian_pan_stems[p_num] = carried_stem

    # 中五宫地盘
    tian_pan_stars[5] = "天禽"
    tian_pan_stems[5] = di_pan[5]

    # 5. 人盘八门排布 (飞宫或转盘)
    # 从旬首原宫出发，根据时辰与旬首的步数，按阳遁顺数/阴遁逆数九宫到当前时辰所落宫位
    xun_branches = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    xun_start_br = xun_start_pillar[1]
    br_step = (xun_branches.index(hour_branch) - xun_branches.index(xun_start_br)) % 12

    if dun_type == "阳遁":
        gate_target_palace = ((origin_palace - 1 + br_step) % 9) + 1
    else:
        gate_target_palace = ((origin_palace - 1 - br_step) % 9) + 1

    if gate_target_palace == 5:
        gate_target_palace = 2

    # 按八门转盘顺时针排布
    src_gate_idx = RING_PALACE_ORDER.index(gate_source_palace)
    tgt_gate_idx = RING_PALACE_ORDER.index(gate_target_palace)
    gate_offset = (tgt_gate_idx - src_gate_idx) % 8

    ren_pan_gates = {}
    for idx, p_num in enumerate(RING_PALACE_ORDER):
        from_gate_ring_idx = (idx - gate_offset) % 8
        from_gate_palace = RING_PALACE_ORDER[from_gate_ring_idx]
        ren_pan_gates[p_num] = EIGHT_GATES_ORIGIN[from_gate_palace]

    # 中五宫无门
    ren_pan_gates[5] = "—"

    # 6. 神盘八神排布 (值符随天盘值符九星所落宫，阳遁顺排，阴遁逆排)
    shen_pan_spirits = {}
    zhifu_star_palace_idx = RING_PALACE_ORDER.index(target_star_palace)
    spirit_step = 1 if dun_type == "阳遁" else -1

    for s_idx, spirit_name in enumerate(EIGHT_SPIRITS):
        p_idx = (zhifu_star_palace_idx + s_idx * spirit_step) % 8
        palace_num = RING_PALACE_ORDER[p_idx]
        shen_pan_spirits[palace_num] = spirit_name
    shen_pan_spirits[5] = "—"

    # 7. 九宫全景构建与格局判定
    palaces_output: Dict[int, Any] = {}
    favorable_directions: List[Dict[str, Any]] = []

    for p_num in range(1, 10):
        p_meta = PALACE_NAMES[p_num]
        d_stem = di_pan.get(p_num, "")
        t_stem = tian_pan_stems.get(p_num, "")
        star = tian_pan_stars.get(p_num, "")
        gate = ren_pan_gates.get(p_num, "")
        spirit = shen_pan_spirits.get(p_num, "")

        is_tian_qin = (p_num == 2 and tian_pan_stars.get(2) == "天芮")
        qin_stem = di_pan.get(5) if is_tian_qin else None

        patterns = evaluate_qimen_patterns(
            t_stem=t_stem,
            d_stem=d_stem,
            gate=gate,
            star=star,
            spirit=spirit,
        )

        # 判定吉方 (三吉门 + 吉神/三奇)
        if gate in ("开门", "休门", "生门") and p_num != 5:
            score = 80
            if t_stem in ("乙", "丙", "丁"):
                score += 15
            if spirit in ("值符", "九天", "太阴", "六合"):
                score += 10
            favorable_directions.append({
                "palace_number": p_num,
                "palace_name": p_meta["name"],
                "direction": p_meta["direction"],
                "gate": gate,
                "star": star,
                "spirit": spirit,
                "score": score,
                "summary": f"{p_meta['direction']}（{p_meta['name']}），临【{gate}】与【{star}】，吉神【{spirit}】护佑，宜主动布局开拓。",
            })

        palaces_output[p_num] = {
            "palace_number": p_num,
            "palace_name": p_meta["name"],
            "trigram": p_meta["trigram"],
            "element": p_meta["element"],
            "direction": p_meta["direction"],
            "di_pan_stem": d_stem,
            "tian_pan_stem": t_stem,
            "nine_star": star,
            "eight_gate": gate,
            "eight_spirit": spirit,
            "is_tian_qin_present": is_tian_qin,
            "qin_stem": qin_stem,
            "patterns": patterns,
        }

    favorable_directions.sort(key=lambda x: -x["score"])

    # 8. 奇门综合建议
    top_dir = favorable_directions[0]["direction"] if favorable_directions else "正北"
    top_gate = favorable_directions[0]["gate"] if favorable_directions else "吉门"
    advisory = {
        "general": f"本局为【{dun_type}{ju_number}局·{yuan_type}】，值符【{zhi_fu_origin_star}】落{PALACE_NAMES[target_star_palace]['name']}，值使【{zhi_shi_origin_gate}】落{PALACE_NAMES[gate_target_palace]['name']}。乘时借势，利取【{top_dir}】方吉气。",
        "action": f"重要决策、商务出行或商务谈判，优先选用【{top_gate}】所在方位推进，避开死门与凶煞冲克。",
        "strategy": "奇门重在审机夺势，动静有常。天盘奇仪与九星指示天时良机，人盘八门指示人事进退，神盘指引心境定力。",
    }

    return {
        "rule_id": RULE_VERSION,
        "system": "qimen",
        "solar_datetime": cal_res["time"]["effective_local_datetime"],
        "lunar_datetime": f"{cal_res['lunar']['year']}年 {'(闰)' if cal_res['lunar']['is_leap_month'] else ''}{cal_res['lunar']['month_name']}月{cal_res['lunar']['day_name']}",
        "ganzhi": ganzhi,
        "solar_term": term_name,
        "dun_type": dun_type,
        "ju_number": ju_number,
        "yuan_type": yuan_type,
        "xun_shou": f"{xun_start_pillar}（{xun_yi}）",
        "zhi_fu_star": zhi_fu_origin_star,
        "zhi_shi_gate": zhi_shi_origin_gate,
        "zhi_fu_palace": target_star_palace,
        "zhi_shi_palace": gate_target_palace,
        "palaces": palaces_output,
        "favorable_directions": favorable_directions,
        "advisory": advisory,
    }


def auto_cast(
    local_datetime: str,
    cast_nonce: str,
    timezone: str = "Asia/Shanghai",
    longitude: Optional[float] = None,
    use_true_solar_time: bool = False,
) -> Dict[str, Any]:
    """个体凭证与时间起局奇门排盘。"""
    res = calculate_qimen_chart(
        local_datetime=local_datetime,
        timezone=timezone,
        longitude=longitude,
        use_true_solar_time=use_true_solar_time,
    )
    res["cast_nonce"] = cast_nonce
    return res


def time_cast(
    local_datetime: str,
    timezone: str = "Asia/Shanghai",
    longitude: Optional[float] = None,
    use_true_solar_time: bool = False,
) -> Dict[str, Any]:
    """时间起局奇门排盘。"""
    return calculate_qimen_chart(
        local_datetime=local_datetime,
        timezone=timezone,
        longitude=longitude,
        use_true_solar_time=use_true_solar_time,
    )
