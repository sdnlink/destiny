from .constants import EARTHLY_BRANCHES, FIVE_ELEMENTS_CONTROLS, FIVE_ELEMENTS_GENERATES
from app.common.ganzhi import BRANCH_ELEMENTS


ENGINE_VERSION = "yuanhui-engine-1.0.0"
RULE_VERSION = "yuanhui-engineering-baseline-1.0.0"
EPOCH_ASTRONOMICAL_YEAR = -67016
YEARS_PER_YUAN = 129600
YEARS_PER_HUI = 10800
YEARS_PER_YUN = 360
YEARS_PER_SHI = 30


def civil_year_label(astronomical_year):
    if astronomical_year <= 0:
        return "公元前{}年".format(1 - astronomical_year)
    return "公元{}年".format(astronomical_year)


def _period(start, length, index, label):
    period_start = start + (index - 1) * length
    return {
        "index": index, "label": label, "start_year": civil_year_label(period_start),
        "end_year": civil_year_label(period_start + length - 1),
    }


def cycle_position(solar_year):
    year = int(solar_year)
    elapsed = year - EPOCH_ASTRONOMICAL_YEAR
    yuan_index = elapsed // YEARS_PER_YUAN + 1
    within_yuan = elapsed % YEARS_PER_YUAN
    hui_index = within_yuan // YEARS_PER_HUI + 1
    within_hui = within_yuan % YEARS_PER_HUI
    yun_index = within_hui // YEARS_PER_YUN + 1
    within_yun = within_hui % YEARS_PER_YUN
    shi_index = within_yun // YEARS_PER_SHI + 1
    year_in_shi = within_yun % YEARS_PER_SHI + 1
    yuan_start = EPOCH_ASTRONOMICAL_YEAR + (yuan_index - 1) * YEARS_PER_YUAN
    hui_start = yuan_start + (hui_index - 1) * YEARS_PER_HUI
    yun_start = hui_start + (yun_index - 1) * YEARS_PER_YUN
    branch = EARTHLY_BRANCHES[hui_index - 1]
    return {
        "solar_year": year,
        "epoch": {"label": "公元前67017年", "astronomical_year": EPOCH_ASTRONOMICAL_YEAR, "status": "pending_expert_review"},
        "yuan": _period(EPOCH_ASTRONOMICAL_YEAR, YEARS_PER_YUAN, yuan_index, "第{}元".format(yuan_index)),
        "hui": {**_period(yuan_start, YEARS_PER_HUI, hui_index, "第{}会".format(hui_index)), "branch": branch, "element": BRANCH_ELEMENTS[branch]},
        "yun": _period(hui_start, YEARS_PER_YUN, yun_index, "第{}运".format(yun_index)),
        "shi": {**_period(yun_start, YEARS_PER_SHI, shi_index, "第{}世".format(shi_index)), "year_in_shi": year_in_shi},
    }


def element_relation(background, target):
    if background == target:
        return {"code": "same_element", "label": "同属{}".format(background)}
    if FIVE_ELEMENTS_GENERATES[background] == target:
        return {"code": "background_generates_target", "label": "会运背景{}生盘面{}".format(background, target)}
    if FIVE_ELEMENTS_GENERATES[target] == background:
        return {"code": "target_generates_background", "label": "盘面{}生会运背景{}".format(target, background)}
    if FIVE_ELEMENTS_CONTROLS[background] == target:
        return {"code": "background_controls_target", "label": "会运背景{}克盘面{}".format(background, target)}
    return {"code": "target_controls_background", "label": "盘面{}克会运背景{}".format(target, background)}


def _module_elements(module_results):
    rows = []
    for item in module_results:
        facts = item["result"].get("facts", {})
        if item["module"] == "zhouyi":
            rows.extend([("zhouyi", "本卦上卦", facts["original"]["upper_trigram"]["element"]), ("zhouyi", "本卦下卦", facts["original"]["lower_trigram"]["element"])])
        elif item["module"] == "meihua":
            rows.extend([("meihua", "体卦", facts["body_use"]["body_trigram"]["element"]), ("meihua", "用卦", facts["body_use"]["use_trigram"]["element"])])
        elif item["module"] == "liuyao":
            rows.append(("liuyao", "卦宫", facts["palace"]["element"]))
        elif item["module"] == "liuren":
            for index, branch in enumerate(facts["three_transmissions"].get("transmissions", [])):
                rows.append(("liuren", ("初传", "中传", "末传")[index], BRANCH_ELEMENTS[branch]))
    return rows


def analyze_yuan_hui_yun_shi(module_results):
    calendar = next((item["result"] for item in module_results if item["module"] == "calendar"), None)
    if calendar is None:
        return None
    position = cycle_position(calendar["solar"]["year"])
    background = position["hui"]["element"]
    evidence = []
    for index, (module, role, element) in enumerate(_module_elements(module_results), 1):
        evidence.append({
            "evidence_id": "YHYS-{:03d}".format(index), "module": module, "role": role,
            "background_element": background, "target_element": element,
            **element_relation(background, element), "rule_ids": ["YHYS-RELATION-001"],
        })
    return {
        "schema_version": "1.0", "status": "engineering_cycle_context_pending_expert_review",
        "engine_version": ENGINE_VERSION, "rule_version": RULE_VERSION, "facts": position,
        "evidence": evidence,
        "steps": [
            {"sequence": 1, "operation": "map_solar_year_to_yuan_hui_yun_shi", "inputs": {"solar_year": calendar["solar"]["year"], "epoch_astronomical_year": EPOCH_ASTRONOMICAL_YEAR}, "output": {"yuan": position["yuan"]["index"], "hui": position["hui"]["index"], "yun": position["yun"]["index"], "shi": position["shi"]["index"], "year_in_shi": position["shi"]["year_in_shi"]}, "rule_ids": ["YHYS-CYCLE-001"]},
            {"sequence": 2, "operation": "compare_hui_element_with_chart_elements", "inputs": {"hui_branch": position["hui"]["branch"], "hui_element": background}, "output": {"evidence_count": len(evidence)}, "rule_ids": ["YHYS-RELATION-001"]},
        ],
        "warnings": ["元会运世纪元采用待专家审核的工程基线，当前只计算到公历年粒度。", "宏观周期五行关系不直接表示个人吉凶、事件概率或应期。"],
    }
