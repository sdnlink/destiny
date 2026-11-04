import json
import logging
from collections import Counter
from pathlib import Path

from app.common.ganzhi import BRANCH_ELEMENTS
from .constants import TRIGRAM_BY_NAME
from .db import db_repository

logger = logging.getLogger("destiny.imagery")

ROOT = Path(__file__).resolve().parents[3]
DATA_RULES = ROOT / "data" / "rules"

ENGINE_VERSION = "imagery-engine-1.0.0"
RULE_VERSION = "imagery-engineering-baseline-1.0.0"

CATEGORY_DIMENSIONS = {
    "career": ["人物", "行为", "场所", "事物"],
    "finance": ["事物", "场所", "行为", "方位"],
    "relationship": ["人物", "家庭", "行为", "身体"],
    "travel": ["方位", "场所", "自然", "行为"],
    "study": ["人物", "事物", "行为", "场所"],
    "other": ["自然", "人物", "事物", "场所"],
}


def load_trigram_imagery():
    """Load trigram imagery from ClickHouse database, falling back to data/rules/trigram-imagery.json."""
    try:
        rows = db_repository.get_trigram_imagery()
        if rows:
            mapped = {}
            for row in rows:
                name = row["trigram_name"]
                dimension = row["dimension"]
                items = row["imagery_items"]
                mapped.setdefault(name, {})[dimension] = items
            if len(mapped) == 8:
                return mapped
    except Exception as exc:
        logger.debug("八卦类象数据库不可用，改用本地规则文件：%s", exc)

    fallback_file = DATA_RULES / "trigram-imagery.json"
    if fallback_file.exists():
        try:
            return json.loads(fallback_file.read_text(encoding="utf-8"))["imagery"]
        except (OSError, ValueError, KeyError) as exc:
            logger.warning("八卦类象规则文件损坏：%s (%s)", fallback_file, exc)
    else:
        logger.warning("八卦类象规则文件缺失：%s，相关类象将为空", fallback_file)
    return {}


def load_branch_imagery():
    """Load branch imagery from ClickHouse database, falling back to data/rules/branch-imagery.json."""
    try:
        rows = db_repository.get_branch_imagery()
        if rows:
            mapped = {}
            for row in rows:
                name = row["branch_name"]
                dimension = row["dimension"]
                items = row["imagery_items"]
                mapped.setdefault(name, {})[dimension] = items
            if len(mapped) == 12:
                return mapped
    except Exception as exc:
        logger.debug("地支类象数据库不可用，改用本地规则文件：%s", exc)

    fallback_file = DATA_RULES / "branch-imagery.json"
    if fallback_file.exists():
        try:
            return json.loads(fallback_file.read_text(encoding="utf-8"))["imagery"]
        except (OSError, ValueError, KeyError) as exc:
            logger.warning("地支类象规则文件损坏：%s (%s)", fallback_file, exc)
    else:
        logger.warning("地支类象规则文件缺失：%s，相关类象将为空", fallback_file)
    return {}


# Module level loaded imagery instances
TRIGRAM_IMAGERY = load_trigram_imagery()
BRANCH_IMAGERY = load_branch_imagery()


def _trigram_candidate(module, role, trigram, dimensions, stage="original"):
    all_trigrams = load_trigram_imagery() or TRIGRAM_IMAGERY
    imagery = all_trigrams.get(trigram["name"], {})
    selected = {dimension: imagery[dimension] for dimension in dimensions if dimension in imagery}
    return {
        "candidate_id": f"{module}-{stage}-{role}-{trigram['name']}",
        "module": module,
        "stage": stage,
        "role": role,
        "symbol_type": "trigram",
        "symbol": trigram["name"],
        "element": trigram["element"],
        "direction": trigram["direction"],
        "selected_imagery": selected,
        "all_imagery": imagery,
        "rule_ids": ["XIANG-TRIGRAM-001", "XIANG-CONTEXT-001"],
    }


def _branch_candidate(module, role, branch, dimensions, stage="original"):
    all_branches = load_branch_imagery() or BRANCH_IMAGERY
    imagery = all_branches.get(branch, {})
    selected = {dimension: imagery[dimension] for dimension in dimensions if dimension in imagery}
    return {
        "candidate_id": f"{module}-{stage}-{role}-{branch}",
        "module": module,
        "stage": stage,
        "role": role,
        "symbol_type": "earthly_branch",
        "symbol": branch,
        "element": BRANCH_ELEMENTS.get(branch, ""),
        "selected_imagery": selected,
        "all_imagery": imagery,
        "rule_ids": ["XIANG-BRANCH-001", "XIANG-CONTEXT-001"],
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
        "schema_version": "1.0",
        "status": "unreviewed_imagery_candidates",
        "engine_version": ENGINE_VERSION,
        "rule_version": RULE_VERSION,
        "context": {
            "category": category,
            "priority_dimensions": dimensions,
            "question_summary": (context or {}).get("question_summary"),
        },
        "candidates": candidates,
        "liuyao_relative_summary": dict(sorted(liuyao_relatives.items())),
        "steps": [
            {
                "sequence": 1,
                "operation": "extract_chart_symbols",
                "output": {"candidate_count": len(candidates)},
                "rule_ids": ["XIANG-TRIGRAM-001", "XIANG-BRANCH-001"],
            },
            {
                "sequence": 2,
                "operation": "prioritize_imagery_by_question_category",
                "output": {"category": category, "dimensions": dimensions},
                "rule_ids": ["XIANG-CONTEXT-001"],
            },
        ],
        "warnings": [
            "类象是待核实的对应候选，不表示现实中的特定人物或事件。",
            "类象未经过专家签署，不自动生成吉凶、应期或概率。",
        ],
    }
