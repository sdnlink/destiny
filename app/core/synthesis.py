import json

from app.core.registry import load_rule_registry, rule_index


POLARITIES = {"favorable", "neutral", "cautious", "unfavorable", "indeterminate"}


def _comparison_key(judgement):
    time_range = judgement.get("time_range")
    encoded_range = json.dumps(time_range, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return judgement.get("dimension"), encoded_range


def _public_record(result, judgement, index):
    return {
        "judgement_id": judgement.get("judgement_id", "{}:{}".format(result.get("system", "unknown"), index)),
        "system": result.get("system"),
        "school": result.get("school"),
        "rule_version": result.get("rule_version"),
        "dimension": judgement.get("dimension"),
        "time_range": judgement.get("time_range"),
        "polarity": judgement.get("polarity"),
        "strength": judgement.get("strength"),
        "rule_ids": judgement.get("rule_ids", []),
        "evidence_ids": judgement.get("evidence_ids", []),
        "limitations": judgement.get("limitations", []),
    }


def synthesize(module_results, registry=None):
    registry = registry or load_rule_registry()
    rules = rule_index(registry)
    groups = {}
    excluded = []

    for result in module_results:
        for index, judgement in enumerate(result.get("judgements", []), 1):
            record = _public_record(result, judgement, index)
            reasons = []
            if not record["dimension"]:
                reasons.append("dimension is required")
            if record["time_range"] is None:
                reasons.append("time_range is required")
            if record["polarity"] not in POLARITIES:
                reasons.append("polarity is invalid")
            if not record["rule_ids"]:
                reasons.append("rule_ids are required")
            else:
                missing = [rule_id for rule_id in record["rule_ids"] if rule_id not in rules]
                unpublished = [
                    rule_id for rule_id in record["rule_ids"]
                    if rule_id in rules and rules[rule_id]["status"] != "published"
                ]
                if missing:
                    reasons.append("unknown rules: {}".format(", ".join(sorted(missing))))
                if unpublished:
                    reasons.append("rules are not published: {}".format(", ".join(sorted(unpublished))))
            if reasons:
                excluded.append({**record, "reasons": reasons})
                continue
            groups.setdefault(_comparison_key(judgement), []).append(record)

    comparison = {
        "consistent": [],
        "complementary": [],
        "conflicts": [],
        "unpaired": [],
        "indeterminate": [],
        "excluded": excluded,
    }
    for (dimension, _), records in groups.items():
        time_range = records[0]["time_range"]
        polarities = {record["polarity"] for record in records}
        group = {
            "dimension": dimension,
            "time_range": time_range,
            "polarities": sorted(polarities),
            "judgements": records,
        }
        if "indeterminate" in polarities:
            comparison["indeterminate"].append(group)
        elif len(records) == 1:
            comparison["unpaired"].append(group)
        elif len(polarities) == 1:
            comparison["consistent"].append(group)
        elif {"favorable", "unfavorable"}.issubset(polarities):
            comparison["conflicts"].append(group)
        else:
            comparison["complementary"].append(group)

    comparable_count = sum(len(records) for records in groups.values())
    notices = []
    if comparable_count == 0:
        notices.append("当前模块没有引用已发布规则的结构化判断，只返回各模块事实，不生成综合倾向。")
    if excluded:
        notices.append("存在未发布、无来源或结构不完整的判断，已从综合比较中排除。")
    return {
        "schema_version": "1.0",
        "strategy": "parallel-evidence-comparison-no-automatic-score",
        "comparable_judgement_count": comparable_count,
        "counts": {key: len(value) for key, value in comparison.items()},
        **comparison,
        "notices": notices,
    }
