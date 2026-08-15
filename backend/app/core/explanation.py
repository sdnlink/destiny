MODULE_LABELS = {
    "calendar": "历法",
    "zhouyi": "周易",
    "meihua": "梅花易数",
    "liuyao": "六爻",
    "liuren": "大六壬",
}
MODULE_ORDER = {"calendar": 0, "zhouyi": 1, "meihua": 2, "liuyao": 3, "liuren": 4}


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
                "rule_ids": [{"manual": "YI-MANUAL-001", "numbers": "YI-NUMBER-001", "time": "YI-TIME-001"}[item["method"]]],
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
    if method == "lunar_time":
        source = facts["source_numbers"]
        method_text = "按年支数{}、农历月{}、农历日{}及时支数{}取数。".format(
            source["year_branch"], source["lunar_month"], source["lunar_day"], source["hour_branch"]
        )
        method_rules = ["MH-TIME-001"]
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
                    "时间" if item["method"] == "time" else "双数",
                    original["upper_trigram"]["name"], original["lower_trigram"]["name"],
                    palace["name"], palace["stage"],
                ),
                "rule_ids": ["LY-TIME-001" if item["method"] == "time" else "LY-NUMBER-001", "LY-PALACE-001"],
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
                "rule_ids": ["LR-MONTH-GENERAL-001", "LR-HOUR-001" if item["method"] == "time" else "LR-NUMBER-001"],
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
                "rule_ids": ["LR-TRANSMISSION-001", "LR-GENERAL-001"],
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
