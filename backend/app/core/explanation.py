MODULE_LABELS = {
    "calendar": "历法",
    "zhouyi": "周易",
    "meihua": "梅花易数",
    "liuyao": "六爻",
    "liuren": "大六壬",
    "ziwei": "紫微斗数",
    "fengshui": "阳宅方位",
}
MODULE_ORDER = {"calendar": 0, "zhouyi": 1, "meihua": 2, "liuyao": 3, "liuren": 4, "ziwei": 5, "fengshui": 6}


def _calendar_explanation(item):
    result = item["result"]
    pillars = result["pillars"]
    lunar = result["lunar"]
    correction = result["time"]["correction"]
    lunar_name = "{}{}月{}".format(
        "闰" if lunar["is_leap_month"] else "",
        lunar["month_name"],
        lunar["day_name"],
    )
    return {
        "module": "calendar",
        "title": "历法与时间基准",
        "summary": "农历{}，四柱为{}、{}、{}、{}。".format(
            lunar_name,
            pillars["year"],
            pillars["month"],
            pillars["day"],
            pillars["time"],
        ),
        "sections": [
            {
                "title": "时间标准化",
                "text": "原始本地时间为{}，对应UTC时间{}，计算采用{}。".format(
                    result["time"]["original_local_datetime"],
                    result["time"]["utc_datetime"],
                    result["time"]["effective_local_datetime"],
                ),
                "rule_ids": ["CAL-NORMALIZE-001", "CAL-SOLAR-TIME-001"],
            },
            {
                "title": "真太阳时处理",
                "text": "真太阳时{}，总时间修正为{}分钟。".format(
                    "已启用" if correction["enabled"] else "未启用",
                    correction["total_correction_minutes"],
                ),
                "rule_ids": ["CAL-SOLAR-TIME-001"],
            },
            {
                "title": "四柱边界",
                "text": "年柱以{}为界，月柱以{}为界，日柱按{}换日。".format(
                    pillars["year_boundary"],
                    pillars["month_boundary"],
                    pillars["day_boundary"],
                ),
                "rule_ids": ["CAL-CONVERSION-001", "CAL-PILLARS-001"],
            },
        ],
        "limitations": ["历法说明只描述时间转换和四柱事实，不构成事项判断。"],
    }


def _zhouyi_explanation(item):
    result = item["result"]
    facts = result["facts"]
    original = facts["original"]
    changed = facts["changed"]
    moving = facts["moving_lines"]
    moving_text = "、".join(str(value) for value in moving) if moving else "无"
    if moving:
        change_text = "第{}爻发生阴阳转换，形成{}卦（第{}卦）。".format(
            moving_text, changed["name"], changed["ordinal"]
        )
    else:
        change_text = "本次没有动爻，变卦与本卦保持一致。"
    return {
        "module": "zhouyi",
        "title": "周易推演结果",
        "summary": "本卦为{}卦（第{}卦），动爻为{}，变卦为{}卦（第{}卦）。".format(
            original["name"], original["ordinal"], moving_text,
            changed["name"], changed["ordinal"],
        ),
        "sections": [
            {
                "title": "本卦结构",
                "text": "{}上{}下，上卦属{}，下卦属{}；这是起卦完成时的原始六爻结构。".format(
                    original["upper_trigram"]["name"],
                    original["lower_trigram"]["name"],
                    original["upper_trigram"]["element"],
                    original["lower_trigram"]["element"],
                ),
                "rule_ids": [{
                    "auto": "YI-AUTO-COIN-001", "manual": "YI-MANUAL-001",
                    "numbers": "YI-NUMBER-001", "three_numbers": "YI-3NUM-MAPPING-001",
                    "time": "YI-TIME-001",
                }[item["method"]]],
            },
            {
                "title": "动爻与变卦",
                "text": change_text,
                "rule_ids": ["YI-RELATION-001"],
            },
            {
                "title": "关联卦",
                "text": "互卦为{}（第{}卦），错卦为{}（第{}卦），综卦为{}（第{}卦）。".format(
                    facts["mutual"]["name"], facts["mutual"]["ordinal"],
                    facts["opposite"]["name"], facts["opposite"]["ordinal"],
                    facts["reversed"]["name"], facts["reversed"]["ordinal"],
                ),
                "rule_ids": ["YI-RELATION-001"],
            },
        ],
        "limitations": list(result.get("warnings", [])),
    }


def _meihua_explanation(item):
    result = item["result"]
    facts = result["facts"]
    original = facts["original"]
    changed = facts["changed"]
    body_use = facts["body_use"]
    method = facts["method"]
    if method in ("lunar_time", "personalized_lunar_time"):
        source = facts["source_numbers"]
        method_text = "按年支数{}、农历月{}、农历日{}及时支数{}取数。".format(
            source["year_branch"], source["lunar_month"], source["lunar_day"], source["hour_branch"]
        )
        if method == "personalized_lunar_time":
            method_text += " 本次加入凭证派生个体数{}。".format(facts["personal_number"])
            method_rules = ["MH-AUTO-PERSONAL-001"]
        else:
            method_rules = ["MH-TIME-001"]
    elif method == "three_numbers":
        source = facts["input_numbers"]
        method_text = "按输入的上卦数{}、下卦数{}和独立动爻数{}取卦。".format(
            source["upper"], source["lower"], source["moving"]
        )
        method_rules = ["MH-THREE-NUMBER-001"]
    else:
        source = facts["input_numbers"]
        method_text = "按输入的上卦数{}和下卦数{}取卦。".format(source["upper"], source["lower"])
        method_rules = ["MH-NUMBER-001"]

    relation_texts = []
    for evidence in result.get("evidence", []):
        stage = "本卦阶段" if evidence["stage"] == "original" else "变卦阶段"
        relation_texts.append("{}为{}：体属{}，用属{}。".format(
            stage, evidence["label"], evidence["body_element"], evidence["use_element"]
        ))

    return {
        "module": "meihua",
        "title": "梅花易数推演结果",
        "summary": "本卦为{}卦（第{}卦），第{}爻动，变卦为{}卦（第{}卦）；体卦为{}，用卦为{}。".format(
            original["name"], original["ordinal"], facts["moving_line"],
            changed["name"], changed["ordinal"],
            body_use["body_trigram"]["name"], body_use["use_trigram"]["name"],
        ),
        "sections": [
            {
                "title": "起卦方法",
                "text": method_text + " 上卦数为{}，下卦数为{}，动爻为第{}爻。".format(
                    facts["upper_trigram_number"], facts["lower_trigram_number"], facts["moving_line"]
                ),
                "rule_ids": method_rules,
            },
            {
                "title": "体用定位",
                "text": "动爻位于{}，因此{}为用卦，{}为体卦。".format(
                    "下卦" if facts["moving_line"] <= 3 else "上卦",
                    body_use["use_trigram"]["name"],
                    body_use["body_trigram"]["name"],
                ),
                "rule_ids": ["MH-BODYUSE-001"],
            },
            {
                "title": "体用五行关系",
                "text": " ".join(relation_texts),
                "rule_ids": ["MH-FIVE-ELEMENT-001"],
            },
        ],
        "limitations": list(result.get("warnings", [])),
    }


def _liuyao_explanation(item):
    result = item["result"]
    facts = result["facts"]
    original = facts["original"]
    changed = facts["changed"]
    palace = facts["palace"]
    moving = "、".join(str(value) for value in facts["moving_lines"])
    void = "、".join(facts["xun"]["empty_branches"])
    method_labels = {
        "auto": "个体三枚铜钱", "time": "传统时间", "numbers": "双数",
        "lines": "六爻值", "coins": "六次三枚硬币",
    }
    method_rules = {
        "auto": "LY-AUTO-COIN-001", "time": "LY-TIME-001", "numbers": "LY-NUMBER-001",
        "lines": "LY-LINES-001", "coins": "LY-COINS-001",
    }
    return {
        "module": "liuyao",
        "title": "六爻纳甲排盘",
        "summary": "本卦为{}，属{}宫{}，世爻在{}、应爻在{}；第{}爻动，变卦为{}。".format(
            original["name"], palace["name"], palace["stage"], palace["host_line"],
            palace["response_line"], moving, changed["name"],
        ),
        "sections": [
            {
                "title": "起卦与八宫",
                "text": "采用{}排盘，本卦{}上{}下，归{}宫{}。".format(
                    method_labels[item["method"]],
                    original["upper_trigram"]["name"], original["lower_trigram"]["name"],
                    palace["name"], palace["stage"],
                ),
                "rule_ids": [method_rules[item["method"]], "LY-PALACE-001"],
            },
            {
                "title": "纳甲与六亲",
                "text": "六爻已按内外卦配置纳干、纳支、五行和六亲；世爻为第{}爻，应爻为第{}爻。".format(
                    palace["host_line"], palace["response_line"]
                ),
                "rule_ids": ["LY-NAJIA-001", "LY-RELATIVE-001"],
            },
            {
                "title": "六神与旬空",
                "text": "占日为{}，{}，旬空为{}。六神由初爻至上爻顺排。".format(
                    facts["day_pillar"], facts["xun"]["name"], void
                ),
                "rule_ids": ["LY-SPIRIT-001", "CYCLE-XUN-001"],
            },
        ],
        "limitations": list(result.get("warnings", [])),
    }


def _liuren_explanation(item):
    result = item["result"]
    facts = result["facts"]
    month_general = facts["month_general"]
    transmissions = facts["three_transmissions"]
    if transmissions["status"] == "completed":
        transmission_text = "三传为{}，课体路径为{}。".format("、".join(transmissions["transmissions"]), transmissions["lesson_type"])
    else:
        transmission_text = "本课进入{}路径，首版未生成三传。".format(transmissions["pending_path"])
    transmission_rule = {
        "涉害": "LR-SHEHAI-001", "遥克": "LR-REMOTE-001", "昴星": "LR-STAR-001",
        "别责": "LR-BIEZE-001", "八专": "LR-BAZHUAN-001", "伏吟": "LR-FUYIN-001",
        "返吟": "LR-FANYIN-001",
    }.get(transmissions["lesson_type"], "LR-COVERAGE-001" if transmissions["status"] != "completed" else "LR-TRANSMISSION-001")
    hour_rules = {"auto": "LR-AUTO-REPORT-001", "time": "LR-HOUR-001", "numbers": "LR-NUMBER-001"}
    return {
        "module": "liuren",
        "title": "大六壬排盘",
        "summary": "占日{}，占时{}，{}后以{}将加时。{}".format(
            facts["day_pillar"], facts["occupation_time"]["branch"],
            month_general["boundary_term"], month_general["name"], transmission_text,
        ),
        "sections": [
            {
                "title": "月将与占时",
                "text": "最近中气为{}，月将{}（{}）；本次占时为{}。".format(
                    month_general["boundary_term"], month_general["name"], month_general["branch"],
                    facts["occupation_time"]["branch"],
                ),
                "rule_ids": ["LR-MONTH-GENERAL-001", hour_rules[item["method"]]],
            },
            {
                "title": "天地盘与四课",
                "text": "月将加临占时后顺布天盘，并由{}日的干寄宫和日支生成四课。".format(facts["day_pillar"]),
                "rule_ids": ["LR-PLATE-001", "LR-LESSON-001"],
            },
            {
                "title": "三传与天将",
                "text": transmission_text + " 十二天将按{}贵人起例{}。".format(
                    "昼" if facts["heavenly_generals"]["period"] == "day" else "夜",
                    facts["heavenly_generals"]["distribution_direction"],
                ),
                "rule_ids": [transmission_rule, "LR-GENERAL-001"],
            },
        ],
        "limitations": list(result.get("warnings", [])),
    }


def _fengshui_explanation(item):
    result = item["result"]
    facts = result["facts"]
    if facts.get("mode") == "multiple_measurements":
        consensus = facts["consensus"]
        aggregate = consensus["aggregate"]
        status_labels = {
            "consistent": "一致", "boundary_sensitive": "跨山界", "inconsistent": "读数不一致",
        }
        if aggregate is None:
            direction_summary = "读数不能形成唯一圆周均值，未生成合并山向"
            mountain_text = "没有生成合并坐向；应检查是否混入坐山读数或测量方向相反。"
        else:
            facing = aggregate["facing"]
            sitting = aggregate["sitting"]
            direction_summary = "共识向首{:.1f}°为{}向，坐山{:.1f}°为{}坐".format(
                aggregate["true_facing_degree"], facing["mountain"]["name"],
                aggregate["true_sitting_degree"], sitting["mountain"]["name"],
            )
            mountain_text = "合并向首候选为{}，坐山候选为{}。".format(
                "、".join(value["name"] for value in facing["candidate_mountains"]),
                "、".join(value["name"] for value in sitting["candidate_mountains"]),
            )
        return {
            "module": "fengshui",
            "title": "阳宅多次坐向测量",
            "summary": "共{}次测量，状态为{}；{}。".format(
                consensus["sample_count"], status_labels[consensus["status"]], direction_summary,
            ),
            "sections": [
                {
                    "title": "逐次真北修正",
                    "text": "{}次读数分别完成角度归一化和磁偏角修正，未先做普通算术平均。".format(consensus["sample_count"]),
                    "rule_ids": ["FS-DIRECTION-NORMALIZE-001", "FS-DECLINATION-001"],
                },
                {
                    "title": "圆周共识",
                    "text": "最小覆盖弧为{:.2f}°，方向集中度为{:.4f}；工程允许的最大一致跨度为{:.2f}°。".format(
                        consensus["angular_spread"], consensus["resultant_length"],
                        consensus["maximum_consensus_spread"],
                    ),
                    "rule_ids": ["FS-MEASUREMENT-CONSENSUS-001"],
                },
                {
                    "title": "合并山向与误差",
                    "text": mountain_text,
                    "rule_ids": ["FS-MEASUREMENT-CONSENSUS-001", "FS-24MOUNTAIN-001", "FS-UNCERTAINTY-001"],
                },
            ],
            "limitations": list(result.get("warnings", [])),
        }
    facing = facts["facing"]
    sitting = facts["sitting"]
    facing_names = "、".join(value["name"] for value in facing["candidate_mountains"])
    sitting_names = "、".join(value["name"] for value in sitting["candidate_mountains"])
    return {
        "module": "fengshui",
        "title": "阳宅坐向测量",
        "summary": "真北向首{:.1f}°为{}向，坐山{:.1f}°为{}坐；测量分类{}。".format(
            facts["true_facing_degree"], facing["mountain"]["name"],
            facts["true_sitting_degree"], sitting["mountain"]["name"],
            "稳定" if facts["classification_stable"] else "跨越分界",
        ),
        "sections": [
            {
                "title": "真北修正",
                "text": "输入基准为{}，应用磁偏角{:.2f}°后，真北向首为{:.2f}°。".format(
                    result["normalized_input"]["input_reference"],
                    result["normalized_input"]["applied_declination"],
                    facts["true_facing_degree"],
                ),
                "rule_ids": ["FS-DIRECTION-NORMALIZE-001", "FS-DECLINATION-001"],
            },
            {
                "title": "坐向与二十四山",
                "text": "向首归{}山（{}卦、{}），旋转180°后的坐山归{}山（{}卦、{}）。".format(
                    facing["mountain"]["name"], facing["mountain"]["trigram"], facing["mountain"]["element"],
                    sitting["mountain"]["name"], sitting["mountain"]["trigram"], sitting["mountain"]["element"],
                ),
                "rule_ids": ["FS-24MOUNTAIN-001"],
            },
            {
                "title": "测量误差",
                "text": "按正负{:.2f}°传播误差，向首候选为{}，坐山候选为{}；向首距最近分界{:.2f}°。".format(
                    result["normalized_input"]["measurement_error"], facing_names, sitting_names,
                    facing["distance_to_boundary"],
                ),
                "rule_ids": ["FS-UNCERTAINTY-001"],
            },
        ],
        "limitations": list(result.get("warnings", [])),
    }


def _ziwei_explanation(item):
    result = item["result"]
    facts = result["facts"]
    ming_palace = facts["ming_palace"]
    shen_palace = facts["shen_palace"]
    bureau = facts["bureau"]
    ming_p = next(p for p in facts["palaces_by_order"] if p["name"] == "命宫")
    main_stars = "、".join(s["name"] for s in ming_p["main_stars"]) or "无主星"
    lucky_stars = "、".join(s["name"] for s in ming_p["lucky_stars"]) or "无"
    bad_stars = "、".join(s["name"] for s in ming_p["bad_stars"]) or "无"
    sihua_text = "、".join(f"{v}{k}" for k, v in facts["si_hua"].items())

    return {
        "module": "ziwei",
        "title": "紫微斗数命盘",
        "summary": f"命宫在{ming_palace['palace_stem_branch']}，五行局为{bureau['name']}（{bureau['nayin']}），命宫主星为{main_stars}，身宫在{shen_palace['palace_stem_branch']}。",
        "sections": [
            {
                "title": "命身宫位与五行局",
                "text": f"生辰八字四柱为{facts['four_pillars']['year']}、{facts['four_pillars']['month']}、{facts['four_pillars']['day']}、{facts['four_pillars']['hour']}，{facts['yin_yang_gender']}，大限{'顺行' if facts['is_forward_decade'] else '逆行'}。命宫在{ming_palace['palace_stem_branch']}，身宫在{shen_palace['palace_stem_branch']}；五行局定为{bureau['name']}，命主为{facts['ming_zhu']}，身主为{facts['shen_zhu']}。",
                "rule_ids": ["ZW-CAL-001", "ZW-MING-001", "ZW-BUREAU-001"],
            },
            {
                "title": "命宫星曜配置",
                "text": f"命宫主星：{main_stars}；吉星辅曜：{lucky_stars}；煞星杂曜：{bad_stars}。",
                "rule_ids": ["ZW-STARS-001"],
            },
            {
                "title": "生年四化与大限",
                "text": f"生年四化配置为：{sihua_text}。起运大限从{bureau['number']}岁起步，按十天干地支顺布十二宫位。",
                "rule_ids": ["ZW-SIHUA-001", "ZW-DECADE-001"],
            },
        ],
        "limitations": list(result.get("warnings", [])),
    }


EXPLAINERS = {
    "calendar": _calendar_explanation,
    "zhouyi": _zhouyi_explanation,
    "meihua": _meihua_explanation,
    "liuyao": _liuyao_explanation,
    "liuren": _liuren_explanation,
    "ziwei": _ziwei_explanation,
    "fengshui": _fengshui_explanation,
}


def explain_calculation_set(module_results, comparison):
    ordered_results = sorted(module_results, key=lambda item: MODULE_ORDER.get(item["module"], 99))
    modules = [EXPLAINERS[item["module"]](item) for item in ordered_results if item["module"] in EXPLAINERS]
    labels = [MODULE_LABELS[item["module"]] for item in ordered_results if item["module"] in MODULE_LABELS]
    result_parts = [module["summary"] for module in modules if module["module"] != "calendar"]
    counts = comparison["counts"]
    if comparison["comparable_judgement_count"]:
        conclusion_status = "structured_comparison_available"
        conclusion_text = "已比较{}条已发布结构化判断：一致{}组、互补{}组、冲突{}组。".format(
            comparison["comparable_judgement_count"],
            counts["consistent"], counts["complementary"], counts["conflicts"],
        )
    else:
        conclusion_status = "factual_result_only"
        conclusion_text = "当前没有引用已发布解释规则的结构化判断，因此只给出排盘结果和计算说明，不生成事项吉凶、应期或行动建议。"
    return {
        "schema_version": "1.0",
        "generation_method": "deterministic_fact_template",
        "review_status": "factual_only_pending_expert_rules",
        "summary": "本次完成{}模块的确定性推演。{}".format("、".join(labels), " ".join(result_parts)),
        "modules": modules,
        "conclusion": {
            "status": conclusion_status,
            "title": "综合说明",
            "text": conclusion_text,
            "counts": counts,
        },
        "limitations": [
            "说明文本由确定性模板生成，只复述本次输入、盘面、步骤和规则关系。",
            "未经专家审核的语料不会进入推演结论。",
            "本结果用于传统术数数字化研究与辅助分析，不代表现实事件概率。",
        ],
    }
