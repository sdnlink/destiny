from collections import Counter

from app.common.ganzhi import BRANCH_ELEMENTS
from .constants import TRIGRAM_BY_NAME


ENGINE_VERSION = "imagery-engine-1.0.0"
RULE_VERSION = "imagery-engineering-baseline-1.0.0"

TRIGRAM_IMAGERY = {
    "乾": {"自然": ["天", "寒", "冰"], "方位": ["西北"], "人物": ["父", "长者", "主事者"], "家庭": ["父亲"], "身体": ["首", "骨", "肺"], "动物": ["马"], "事物": ["金玉", "圆物", "刚健之物"], "场所": ["高处", "官署"], "行为": ["统领", "决断", "健行"]},
    "兑": {"自然": ["泽", "雨后积水"], "方位": ["西"], "人物": ["少女", "言说者"], "家庭": ["少女"], "身体": ["口", "舌", "肺"], "动物": ["羊"], "事物": ["器皿", "缺口之物"], "场所": ["水边", "娱乐场所"], "行为": ["言谈", "喜悦", "交换"]},
    "离": {"自然": ["火", "日", "电"], "方位": ["南"], "人物": ["中女", "文职者"], "家庭": ["中女"], "身体": ["目", "心", "血"], "动物": ["雉", "鸟"], "事物": ["文书", "灯火", "有纹理之物"], "场所": ["明亮处", "文化场所"], "行为": ["观察", "显现", "依附"]},
    "震": {"自然": ["雷", "地震"], "方位": ["东"], "人物": ["长男", "行动者"], "家庭": ["长男"], "身体": ["足", "肝", "神经"], "动物": ["龙"], "事物": ["竹木", "车辆", "发声之物"], "场所": ["道路", "林地"], "行为": ["启动", "惊动", "快速推进"]},
    "巽": {"自然": ["风", "气流"], "方位": ["东南"], "人物": ["长女", "协调者"], "家庭": ["长女"], "身体": ["股", "胆", "呼吸"], "动物": ["鸡"], "事物": ["绳索", "木器", "细长物"], "场所": ["通风处", "出入口"], "行为": ["进入", "传播", "协商"]},
    "坎": {"自然": ["水", "雨", "月"], "方位": ["北"], "人物": ["中男", "劳作者"], "家庭": ["中男"], "身体": ["耳", "肾", "血液"], "动物": ["猪", "水生物"], "事物": ["液体", "沟槽", "弯曲物"], "场所": ["低处", "水边", "险处"], "行为": ["下行", "隐伏", "反复试探"]},
    "艮": {"自然": ["山", "土石"], "方位": ["东北"], "人物": ["少男", "守门者"], "家庭": ["少男"], "身体": ["手", "背", "关节"], "动物": ["狗"], "事物": ["石块", "门槛", "静止物"], "场所": ["山地", "门庭", "边界"], "行为": ["停止", "守界", "积累"]},
    "坤": {"自然": ["地", "云", "土"], "方位": ["西南"], "人物": ["母", "众人", "承事者"], "家庭": ["母亲"], "身体": ["腹", "脾", "肌肉"], "动物": ["牛"], "事物": ["布帛", "容器", "方形物"], "场所": ["田野", "平地", "仓储处"], "行为": ["承载", "配合", "包容"]},
}

BRANCH_IMAGERY = {
    "子": {"方位": ["北"], "自然": ["水", "寒"], "时令": ["冬", "夜半"], "事物": ["流动信息", "种子"]},
    "丑": {"方位": ["东北偏北"], "自然": ["湿土"], "时令": ["季冬"], "事物": ["仓储", "积累"]},
    "寅": {"方位": ["东北偏东"], "自然": ["木", "初生"], "时令": ["孟春"], "事物": ["道路", "组织启动"]},
    "卯": {"方位": ["东"], "自然": ["木", "草木"], "时令": ["仲春"], "事物": ["门户", "往来"]},
    "辰": {"方位": ["东南偏东"], "自然": ["湿土"], "时令": ["季春"], "事物": ["汇集", "转折"]},
    "巳": {"方位": ["东南偏南"], "自然": ["火"], "时令": ["孟夏"], "事物": ["传播", "变化"]},
    "午": {"方位": ["南"], "自然": ["火", "日"], "时令": ["仲夏"], "事物": ["显达", "公开"]},
    "未": {"方位": ["西南偏南"], "自然": ["燥土"], "时令": ["季夏"], "事物": ["整理", "收束"]},
    "申": {"方位": ["西南偏西"], "自然": ["金"], "时令": ["孟秋"], "事物": ["传递", "制度"]},
    "酉": {"方位": ["西"], "自然": ["金"], "时令": ["仲秋"], "事物": ["成形", "评定"]},
    "戌": {"方位": ["西北偏西"], "自然": ["燥土"], "时令": ["季秋"], "事物": ["守卫", "归档"]},
    "亥": {"方位": ["西北偏北"], "自然": ["水"], "时令": ["孟冬"], "事物": ["收藏", "远行"]},
}

CATEGORY_DIMENSIONS = {
    "career": ["人物", "行为", "场所", "事物"],
    "finance": ["事物", "场所", "行为", "方位"],
    "relationship": ["人物", "家庭", "行为", "身体"],
    "travel": ["方位", "场所", "自然", "行为"],
    "study": ["人物", "事物", "行为", "场所"],
    "other": ["自然", "人物", "事物", "场所"],
}


def _trigram_candidate(module, role, trigram, dimensions, stage="original"):
    imagery = TRIGRAM_IMAGERY[trigram["name"]]
    selected = {dimension: imagery[dimension] for dimension in dimensions if dimension in imagery}
    return {
        "candidate_id": "{}-{}-{}-{}".format(module, stage, role, trigram["name"]),
        "module": module, "stage": stage, "role": role, "symbol_type": "trigram",
        "symbol": trigram["name"], "element": trigram["element"], "direction": trigram["direction"],
        "selected_imagery": selected, "all_imagery": imagery, "rule_ids": ["XIANG-TRIGRAM-001", "XIANG-CONTEXT-001"],
    }


def _branch_candidate(module, role, branch, dimensions, stage="original"):
    imagery = BRANCH_IMAGERY[branch]
    selected = {dimension: imagery[dimension] for dimension in dimensions if dimension in imagery}
    return {
        "candidate_id": "{}-{}-{}-{}".format(module, stage, role, branch),
        "module": module, "stage": stage, "role": role, "symbol_type": "earthly_branch",
        "symbol": branch, "element": BRANCH_ELEMENTS[branch], "selected_imagery": selected,
        "all_imagery": imagery, "rule_ids": ["XIANG-BRANCH-001", "XIANG-CONTEXT-001"],
    }


def collect_imagery(module_results, context=None):
    category = (context or {}).get("category", "other")
    dimensions = CATEGORY_DIMENSIONS.get(category, CATEGORY_DIMENSIONS["other"])
    candidates = []
    liuyao_relatives = Counter()
    for item in module_results:
        module = item["module"]
        result = item["result"]
        facts = result.get("facts", {})
        if module == "zhouyi":
            for stage in ("original", "changed"):
                for role in ("upper_trigram", "lower_trigram"):
                    candidates.append(_trigram_candidate(module, role, facts[stage][role], dimensions, stage))
        elif module == "meihua":
            body_use = facts["body_use"]
            candidates.append(_trigram_candidate(module, "body", body_use["body_trigram"], dimensions))
            candidates.append(_trigram_candidate(module, "use", body_use["use_trigram"], dimensions))
            candidates.append(_trigram_candidate(module, "changed_use", body_use["changed_use_trigram"], dimensions, "changed"))
        elif module == "liuyao":
            candidates.append(_trigram_candidate(module, "palace", TRIGRAM_BY_NAME[facts["palace"]["name"]], dimensions))
            for line in facts["line_chart"]:
                liuyao_relatives[line["six_relative"]] += 1
        elif module == "liuren":
            candidates.append(_branch_candidate(module, "month_general", facts["month_general"]["branch"], dimensions))
            for index, branch in enumerate(facts["three_transmissions"].get("transmissions", [])):
                candidates.append(_branch_candidate(module, ("initial", "middle", "final")[index] + "_transmission", branch, dimensions))
    return {
        "schema_version": "1.0", "status": "unreviewed_imagery_candidates",
        "engine_version": ENGINE_VERSION, "rule_version": RULE_VERSION,
        "context": {"category": category, "priority_dimensions": dimensions, "question_summary": (context or {}).get("question_summary")},
        "candidates": candidates,
        "liuyao_relative_summary": dict(sorted(liuyao_relatives.items())),
        "steps": [
            {"sequence": 1, "operation": "extract_chart_symbols", "output": {"candidate_count": len(candidates)}, "rule_ids": ["XIANG-TRIGRAM-001", "XIANG-BRANCH-001"]},
            {"sequence": 2, "operation": "prioritize_imagery_by_question_category", "output": {"category": category, "dimensions": dimensions}, "rule_ids": ["XIANG-CONTEXT-001"]},
        ],
        "warnings": ["类象是待核实的对应候选，不表示现实中的特定人物或事件。", "类象未经过专家签署，不自动生成吉凶、应期或概率。"],
    }
