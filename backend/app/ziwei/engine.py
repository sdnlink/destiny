"""Core computational engine for Zi Wei Dou Shu (紫微斗数)."""

from datetime import datetime
from typing import Any, Dict, Optional
from lunar_python import Solar

from app.calendar.engine import CalendarEngine
from .rules import (
    SIHUA_VARIANTS,
    XIAN_CHI_TABLE,
    BRANCH_TO_INDEX,
    EARTHLY_BRANCHES,
    HEAVENLY_STEMS,
    HUO_START_TABLE,
    KUI_YUE_TABLE,
    LING_START_TABLE,
    LU_CUN_TABLE,
    MING_ZHU_TABLE,
    NAYIN_ELEMENT_BUREAU,
    PALACE_NAMES,
    SHEN_ZHU_TABLE,
    SIHUA_TABLE,
    STAR_ELEMENTS,
    STEM_TO_INDEX,
    TIAN_MA_TABLE,
    TIGER_DUN_START,
    get_ganzhi_nayin,
)


def _get_lunar_info(dt: datetime):
    solar = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    lunar = solar.getLunar()
    eight_char = lunar.getEightChar()

    year_gan = eight_char.getYearGan()
    year_zhi = eight_char.getYearZhi()
    month_gan = eight_char.getMonthGan()
    month_zhi = eight_char.getMonthZhi()
    day_gan = eight_char.getDayGan()
    day_zhi = eight_char.getDayZhi()
    time_gan = eight_char.getTimeGan()
    time_zhi = eight_char.getTimeZhi()

    lunar_year = lunar.getYear()
    lunar_month = abs(lunar.getMonth())  # 绝对值处理闰月
    lunar_day = lunar.getDay()
    is_leap = lunar.getMonth() < 0

    return {
        "lunar_year": lunar_year,
        "lunar_month": lunar_month,
        "lunar_day": lunar_day,
        "is_leap": is_leap,
        "year_stem": year_gan,
        "year_branch": year_zhi,
        "month_stem": month_gan,
        "month_branch": month_zhi,
        "day_stem": day_gan,
        "day_branch": day_zhi,
        "hour_stem": time_gan,
        "hour_branch": time_zhi,
        "four_pillars": {
            "year": f"{year_gan}{year_zhi}",
            "month": f"{month_gan}{month_zhi}",
            "day": f"{day_gan}{day_zhi}",
            "hour": f"{time_gan}{time_zhi}",
        },
    }


def _locate_ziwei_star(bureau_number: int, lunar_day: int) -> int:
    """依据五行局数与农历出生日推算紫微星所在宫位地支索引 (0=子, 1=丑, 2=寅...)."""
    B = bureau_number
    D = lunar_day
    remainder = D % B
    if remainder == 0:
        Q = D // B
        return (2 + Q - 1) % 12

    X = B - remainder
    Q = (D + X) // B
    base = (2 + Q - 1) % 12
    if X % 2 == 1:
        # 奇数逆走 X 步
        return (base - X) % 12
    else:
        # 偶数顺走 X 步
        return (base + X) % 12


def calculate_ziwei_chart(
    local_datetime: str,
    timezone: str = "Asia/Shanghai",
    gender: str = "男",
    longitude: Optional[float] = None,
    use_true_solar_time: bool = False,
) -> Dict[str, Any]:
    """Calculate the complete Ziwei Doushu chart using CalendarEngine baseline."""
    cal_engine = CalendarEngine()
    cal_res = cal_engine.calculate(
        local_datetime=local_datetime,
        timezone=timezone,
        longitude=longitude,
        use_true_solar_time=use_true_solar_time,
    )

    year_ganzhi = cal_res["ganzhi"]["year"]["text"]
    year_stem, year_branch = year_ganzhi[0], year_ganzhi[1]
    hour_branch = cal_res["time_branch"]["name"]
    lunar_month = abs(cal_res["lunar"]["month"])
    lunar_day = cal_res["lunar"]["day"]

    # 1. 阴阳男女判定
    stem_idx = STEM_TO_INDEX[year_stem]
    is_yang_stem = (stem_idx % 2 == 0)  # 甲丙戊庚壬 为阳
    polarity_text = "阳" if is_yang_stem else "阴"
    gender_norm = "男" if gender in ("男", "M", "male") else "女"
    yin_yang_gender = f"{polarity_text}{gender_norm}"

    # 顺行 / 逆行判定 (阳男阴女顺行，阴男阳女逆行)
    is_forward = (is_yang_stem and gender_norm == "男") or (not is_yang_stem and gender_norm == "女")

    # 2. 定命宫、身宫
    # 寅宫(2)起正月顺数生月，逆数生时安命宫
    hour_idx = BRANCH_TO_INDEX[hour_branch]
    month_offset = lunar_month - 1
    ming_palace_idx = (2 + month_offset - hour_idx) % 12
    # 寅宫(2)起正月顺数生月，顺数生时安身宫
    shen_palace_idx = (2 + month_offset + hour_idx) % 12

    ming_branch = EARTHLY_BRANCHES[ming_palace_idx]
    shen_branch = EARTHLY_BRANCHES[shen_palace_idx]

    # 3. 定十二宫天干 (五虎遁起寅宫干)
    tiger_stem = TIGER_DUN_START[year_stem]
    tiger_stem_idx = STEM_TO_INDEX[tiger_stem]
    palace_stems = {}
    for i in range(12):
        branch_idx = (2 + i) % 12
        branch_name = EARTHLY_BRANCHES[branch_idx]
        stem_name = HEAVENLY_STEMS[(tiger_stem_idx + i) % 10]
        palace_stems[branch_name] = stem_name

    # 4. 定命宫干支与五行局
    ming_stem = palace_stems[ming_branch]
    nayin_val = get_ganzhi_nayin(ming_stem, ming_branch)
    bureau_name, bureau_number = NAYIN_ELEMENT_BUREAU.get(nayin_val, ("水二局", 2))

    # 5. 排十二宫名称与大限区间
    palaces = []
    for i in range(12):
        # 命宫起逆时针排十二宫：命宫, 兄弟, 夫妻, 子女, 财帛, 疾厄, 迁移, 仆役, 官禄, 田宅, 福德, 父母
        p_branch_idx = (ming_palace_idx - i) % 12
        p_branch = EARTHLY_BRANCHES[p_branch_idx]
        p_stem = palace_stems[p_branch]
        p_name = PALACE_NAMES[i]
        is_shen = (p_branch_idx == shen_palace_idx)

        # 大限计算（《紫微斗數全書·安大限诀》）：
        #   「阳男阴女从命前一宫起顺行，是父母宫；阴男阳女从命后一宫起逆行，是兄弟宫」。
        # palaces 按 (ming_idx - i) 排，即 i 递增＝地支递减（十二宫从命宫逆转）。
        # 「命前一宫」是父母宫(i=11)，顺行沿 i 递减方向推进；
        # 「命后一宫」是兄弟宫(i=1)，逆行沿 i 递增方向推进。
        # 早先两式写反：顺行给了兄弟宫第二限、逆行给了父母宫第二限。
        if is_forward:
            decade_index = (12 - i) % 12
        else:
            decade_index = i
        limit_start = bureau_number + decade_index * 10
        limit_end = limit_start + 9

        palaces.append({
            "order": i + 1,
            "branch_index": p_branch_idx,
            "earthly_branch": p_branch,
            "heavenly_stem": p_stem,
            "palace_stem_branch": f"{p_stem}{p_branch}",
            "name": p_name,
            "is_body_palace": is_shen,
            # 三方四正：本宫 + 三合两宫（+4/+8）+ 对宫（+6），纯宫位索引推导
            "san_fang_branches": [
                p_branch,
                EARTHLY_BRANCHES[(p_branch_idx + 4) % 12],
                EARTHLY_BRANCHES[(p_branch_idx + 8) % 12],
            ],
            "dui_gong_branch": EARTHLY_BRANCHES[(p_branch_idx + 6) % 12],
            "si_zheng_branches": [
                p_branch,
                EARTHLY_BRANCHES[(p_branch_idx + 4) % 12],
                EARTHLY_BRANCHES[(p_branch_idx + 8) % 12],
                EARTHLY_BRANCHES[(p_branch_idx + 6) % 12],
            ],
            "major_limit_start": limit_start,
            "major_limit_end": limit_end,
            "main_stars": [],
            "lucky_stars": [],
            "bad_stars": [],
            "minor_stars": [],
            "si_hua": [],
        })

    # 建立地支索引到宫位对象的字典
    branch_to_palace = {p["earthly_branch"]: p for p in palaces}

    # 6. 定紫微星与天府星
    ziwei_branch_idx = _locate_ziwei_star(bureau_number, lunar_day)
    # 天府星与紫微星之关系（紫微斗數全書·卷二·安天府图）：
    #   「天府惟寅、申二宫与紫微同宫，余宫俱各相对（如紫居丑则府居未）。」
    #   即：紫微在寅(2)或申(8)时天府同宫；其余各宫天府恒在紫微之对宫（六冲，±6）。
    if ziwei_branch_idx in (2, 8):  # 寅=2, 申=8
        tianfu_branch_idx = ziwei_branch_idx
    else:
        tianfu_branch_idx = (ziwei_branch_idx + 6) % 12

    # 7. 安十四正曜
    # 紫微系六星 (逆时针)
    ziwei_series = [
        ("紫微", 0),
        ("天机", -1),
        ("太阳", -3),
        ("武曲", -4),
        ("天同", -5),
        ("廉贞", -8),
    ]
    for star_name, offset in ziwei_series:
        b_idx = (ziwei_branch_idx + offset) % 12
        b_name = EARTHLY_BRANCHES[b_idx]
        branch_to_palace[b_name]["main_stars"].append({
            "name": star_name,
            "type": "main",
            "element": STAR_ELEMENTS.get(star_name, ""),
        })

    # 天府系八星 (顺时针)
    tianfu_series = [
        ("天府", 0),
        ("太阴", 1),
        ("贪狼", 2),
        ("巨门", 3),
        ("天相", 4),
        ("天梁", 5),
        ("七杀", 6),
        ("破军", 10),
    ]
    for star_name, offset in tianfu_series:
        b_idx = (tianfu_branch_idx + offset) % 12
        b_name = EARTHLY_BRANCHES[b_idx]
        branch_to_palace[b_name]["main_stars"].append({
            "name": star_name,
            "type": "main",
            "element": STAR_ELEMENTS.get(star_name, ""),
        })

    # 8. 安六吉星
    # 左辅 (辰宫4起正月顺数生月)
    zuofu_branch = EARTHLY_BRANCHES[(4 + lunar_month - 1) % 12]
    branch_to_palace[zuofu_branch]["lucky_stars"].append({"name": "左辅", "type": "lucky", "element": "土"})
    # 右弼 (戌宫10起正月逆数生月)
    youbi_branch = EARTHLY_BRANCHES[(10 - (lunar_month - 1)) % 12]
    branch_to_palace[youbi_branch]["lucky_stars"].append({"name": "右弼", "type": "lucky", "element": "水"})
    # 文昌 (戌宫10起子时逆数生时)
    wenchang_branch = EARTHLY_BRANCHES[(10 - hour_idx) % 12]
    branch_to_palace[wenchang_branch]["lucky_stars"].append({"name": "文昌", "type": "lucky", "element": "金"})
    # 文曲 (辰宫4起子时顺数生时)
    wenqu_branch = EARTHLY_BRANCHES[(4 + hour_idx) % 12]
    branch_to_palace[wenqu_branch]["lucky_stars"].append({"name": "文曲", "type": "lucky", "element": "水"})
    # 天魁、天钺 (年干)
    kui_branch, yue_branch = KUI_YUE_TABLE.get(year_stem, ("丑", "未"))
    branch_to_palace[kui_branch]["lucky_stars"].append({"name": "天魁", "type": "lucky", "element": "火"})
    branch_to_palace[yue_branch]["lucky_stars"].append({"name": "天钺", "type": "lucky", "element": "火"})

    # 禄存、天马
    lucun_branch = LU_CUN_TABLE.get(year_stem, "寅")
    branch_to_palace[lucun_branch]["lucky_stars"].append({"name": "禄存", "type": "lucky", "element": "土"})
    tianma_branch = TIAN_MA_TABLE.get(year_branch, "寅")
    branch_to_palace[tianma_branch]["lucky_stars"].append({"name": "天马", "type": "lucky", "element": "火"})

    # 9. 安六煞星
    # 擎羊 (禄存顺一宫), 陀罗 (禄存逆一宫)
    lucun_idx = BRANCH_TO_INDEX[lucun_branch]
    qingyang_branch = EARTHLY_BRANCHES[(lucun_idx + 1) % 12]
    tuoluo_branch = EARTHLY_BRANCHES[(lucun_idx - 1) % 12]
    branch_to_palace[qingyang_branch]["bad_stars"].append({"name": "擎羊", "type": "bad", "element": "金"})
    branch_to_palace[tuoluo_branch]["bad_stars"].append({"name": "陀罗", "type": "bad", "element": "金"})

    # 火星、铃星
    huo_start = HUO_START_TABLE.get(year_branch, "丑")
    huo_idx = (BRANCH_TO_INDEX[huo_start] + hour_idx) % 12
    huo_branch = EARTHLY_BRANCHES[huo_idx]
    branch_to_palace[huo_branch]["bad_stars"].append({"name": "火星", "type": "bad", "element": "火"})

    ling_start = LING_START_TABLE.get(year_branch, "卯")
    ling_idx = (BRANCH_TO_INDEX[ling_start] + hour_idx) % 12
    ling_branch = EARTHLY_BRANCHES[ling_idx]
    branch_to_palace[ling_branch]["bad_stars"].append({"name": "铃星", "type": "bad", "element": "火"})

    # 地空、地劫 (亥起子时)
    dijie_branch = EARTHLY_BRANCHES[(11 + hour_idx) % 12]
    dikong_branch = EARTHLY_BRANCHES[(11 - hour_idx) % 12]
    branch_to_palace[dijie_branch]["bad_stars"].append({"name": "地劫", "type": "bad", "element": "火"})
    branch_to_palace[dikong_branch]["bad_stars"].append({"name": "地空", "type": "bad", "element": "火"})

    # 9.1 安杂曜：红鸾、天喜、天刑、天姚、咸池
    # 红鸾卯起子年逆数生年支；天喜居红鸾对宫
    year_branch_idx = BRANCH_TO_INDEX[year_branch]
    hongluan_branch = EARTHLY_BRANCHES[(3 - year_branch_idx) % 12]
    tianxi_branch = EARTHLY_BRANCHES[(3 - year_branch_idx + 6) % 12]
    branch_to_palace[hongluan_branch]["minor_stars"].append({"name": "红鸾", "type": "minor", "element": "水"})
    branch_to_palace[tianxi_branch]["minor_stars"].append({"name": "天喜", "type": "minor", "element": "水"})
    # 天刑酉起正月顺数生月；天姚丑起正月顺数生月（闰月按月序本身）
    lunar_month_num = abs(cal_res["lunar"]["month"])
    tianxing_branch = EARTHLY_BRANCHES[(9 + lunar_month_num - 1) % 12]
    tianyao_branch = EARTHLY_BRANCHES[(1 + lunar_month_num - 1) % 12]
    branch_to_palace[tianxing_branch]["minor_stars"].append({"name": "天刑", "type": "minor", "element": "火"})
    branch_to_palace[tianyao_branch]["minor_stars"].append({"name": "天姚", "type": "minor", "element": "水"})
    # 咸池按生年支三合局取
    xianchi_branch = XIAN_CHI_TABLE.get(year_branch, "酉")
    branch_to_palace[xianchi_branch]["minor_stars"].append({"name": "咸池", "type": "minor", "element": "水"})

    # 10. 生年四化（底本A标记星盘；两底本变体全部输出并标注分歧）
    sihua_map = SIHUA_TABLE.get(year_stem, {})
    for hua_name, target_star in sihua_map.items():
        # 在全盘寻找 target_star 并打上四化标记
        for p in palaces:
            for st in p["main_stars"] + p["lucky_stars"]:
                if st["name"] == target_star:
                    st["si_hua"] = hua_name
                    p["si_hua"].append(f"{target_star}{hua_name}")
    sihua_variants = {}
    for key, variant in SIHUA_VARIANTS.items():
        sihua_variants[key] = {
            "label": variant["label"],
            "si_hua": variant["table"].get(year_stem, {}),
        }
    if sihua_variants["quanshu"]["si_hua"] == sihua_variants["bieben"]["si_hua"]:
        sihua_note = "本年干四化两底本一致"
    else:
        sihua_note = "本年干四化两底本存在分歧（化科），全部变体已输出，请按所用底本取用"

    # 11. 命主与身主
    ming_zhu = MING_ZHU_TABLE.get(ming_branch, "贪狼")
    shen_zhu = SHEN_ZHU_TABLE.get(year_branch, "火星")

    # 按照地支环状顺序 (子至亥) 整理供前端渲染
    branches_sorted_palaces = [branch_to_palace[b] for b in EARTHLY_BRANCHES]

    return {
        "system": "ziwei",
        "chart_type": "ziwei_doushu_natal",
        "input_datetime": local_datetime,
        "timezone": timezone,
        "gender": gender_norm,
        "yin_yang_gender": yin_yang_gender,
        "is_forward_decade": is_forward,
        "lunar_calendar": {
            "lunar_year": cal_res["lunar"]["year"],
            "lunar_month": abs(cal_res["lunar"]["month"]),
            "lunar_day": cal_res["lunar"]["day"],
            "is_leap": cal_res["lunar"].get("is_leap", False),
        },
        "four_pillars": {
            "year": cal_res["ganzhi"]["year"]["text"],
            "month": cal_res["ganzhi"]["month"]["text"],
            "day": cal_res["ganzhi"]["day"]["text"],
            "hour": cal_res["ganzhi"]["hour"]["text"],
            "time": cal_res["ganzhi"]["hour"]["text"],
        },
        "bureau": {
            "name": bureau_name,
            "number": bureau_number,
            "nayin": nayin_val,
        },
        "ming_palace": {
            "earthly_branch": ming_branch,
            "heavenly_stem": ming_stem,
            "palace_stem_branch": f"{ming_stem}{ming_branch}",
        },
        "shen_palace": {
            "earthly_branch": shen_branch,
            "heavenly_stem": palace_stems[shen_branch],
            "palace_stem_branch": f"{palace_stems[shen_branch]}{shen_branch}",
        },
        "ming_zhu": ming_zhu,
        "shen_zhu": shen_zhu,
        "si_hua": sihua_map,
        "si_hua_variants": sihua_variants,
        "si_hua_note": sihua_note,
        "palaces_by_order": palaces,
        "palaces_by_branch": branches_sorted_palaces,
    }


def _minor_star_summary(facts):
    """从排盘结果中汇总五颗杂曜的落宫，供步骤足迹引用。"""
    positions = {}
    for palace in facts["palaces_by_branch"]:
        for star in palace["minor_stars"]:
            positions[star["name"]] = palace["earthly_branch"]
    return {
        "hongluan": positions.get("红鸾", ""),
        "tianxi": positions.get("天喜", ""),
        "tianxing": positions.get("天刑", ""),
        "tianyao": positions.get("天姚", ""),
        "xianchi": positions.get("咸池", ""),
    }


def time_cast(
    local_datetime: str,
    timezone: str = "Asia/Shanghai",
    gender: str = "男",
    longitude: Optional[float] = None,
    use_true_solar_time: bool = False,
) -> Dict[str, Any]:
    """Execute standard time-based Ziwei Doushu chart deduction."""
    facts = calculate_ziwei_chart(local_datetime, timezone, gender, longitude, use_true_solar_time)
    ming_p = next(p for p in facts["palaces_by_order"] if p["name"] == "命宫")
    main_stars_str = "、".join([s["name"] for s in ming_p["main_stars"]]) or "无主星"

    return {
        "schema_version": "1.0",
        "status": "deterministic_derivation_complete",
        "engine_version": "ziwei-engine-1.0.0",
        "rule_version": "ziwei-canonical-1.0.0",
        "method": "time",
        "facts": facts,
        "steps": [
            {
                "sequence": 1,
                "operation": "convert_solar_to_lunar_four_pillars",
                "output": {"four_pillars": facts["four_pillars"], "lunar": facts["lunar_calendar"]},
                "rule_ids": ["ZW-CAL-001"],
            },
            {
                "sequence": 2,
                "operation": "calculate_ming_shen_palaces",
                "output": {"ming_palace": facts["ming_palace"], "shen_palace": facts["shen_palace"]},
                "rule_ids": ["ZW-MING-001"],
            },
            {
                "sequence": 3,
                "operation": "derive_five_element_bureau",
                "output": facts["bureau"],
                "rule_ids": ["ZW-BUREAU-001"],
            },
            {
                "sequence": 4,
                "operation": "arrange_main_and_auxiliary_stars",
                "output": {"ming_stars": main_stars_str, "si_hua": facts["si_hua"],
                           "si_hua_variants": facts["si_hua_variants"], "si_hua_note": facts["si_hua_note"]},
                "rule_ids": ["ZW-STARS-001", "ZW-SIHUA-001", "ZW-SIHUA-002"],
            },
            {
                "sequence": 5,
                "operation": "arrange_minor_stars",
                "output": _minor_star_summary(facts),
                "rule_ids": ["ZW-MINOR-001"],
            },
        ],
        "rule_ids": [
            "ZW-CAL-001",
            "ZW-MING-001",
            "ZW-BUREAU-001",
            "ZW-STARS-001",
            "ZW-SIHUA-001",
            "ZW-MINOR-001",
            "ZW-DECADE-001",
        ],
        "warnings": [
            "紫微斗数排盘严格遵循经典星曜干支数理规则，不作现代确定性宿命推断。",
            "星曜吉凶状态需结合三方四正与生年四化综合考量。",
        ],
    }


def auto_cast(
    cast_nonce: str,
    local_datetime: str,
    timezone: str = "Asia/Shanghai",
    gender: str = "男",
    longitude: Optional[float] = None,
    use_true_solar_time: bool = False,
) -> Dict[str, Any]:
    """Automatic cast based on local datetime and cast nonce."""
    res = time_cast(local_datetime, timezone, gender, longitude, use_true_solar_time)
    res["cast_nonce"] = cast_nonce
    return res
