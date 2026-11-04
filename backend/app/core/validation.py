from app.common.calculation_dispatch import execute_calculation
from app.core.registry import load_rule_registry, load_validation_cases, unknown_rule_ids


def execute_validation_case(case):
    """执行单个校验案例。分发表与正式排盘共用，避免两边方法覆盖漂移。"""
    return execute_calculation(case["system"], case["method"], case["input"])


def compare_subset(actual, expected, path="result"):
    differences = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return ["{} expected object, got {!r}".format(path, actual)]
        for key, value in expected.items():
            if key not in actual:
                differences.append("{} missing expected key {}".format(path, key))
                continue
            differences.extend(compare_subset(actual[key], value, "{}.{}".format(path, key)))
        return differences
    if isinstance(expected, list):
        if not isinstance(actual, list):
            return ["{} expected list, got {!r}".format(path, actual)]
        if len(actual) != len(expected):
            return ["{} expected {} items, got {}".format(path, len(expected), len(actual))]
        for index, (actual_item, expected_item) in enumerate(zip(actual, expected)):
            differences.extend(compare_subset(actual_item, expected_item, "{}[{}]".format(path, index)))
        return differences
    if actual != expected:
        return ["{} expected {!r}, got {!r}".format(path, expected, actual)]
    return differences


def run_validation_cases(case_document=None, registry=None):
    document = case_document if case_document is not None else load_validation_cases()
    rules = registry if registry is not None else load_rule_registry()
    results = []
    failed = 0
    for case in document["cases"]:
        result = execute_validation_case(case)
        differences = compare_subset(result, case["expected"])
        unknown = unknown_rule_ids(result, rules)
        if unknown:
            differences.append("unregistered rule ids: {}".format(", ".join(unknown)))
        if differences:
            failed += 1
        results.append({
            "case_id": case["case_id"],
            "system": case["system"],
            "method": case["method"],
            "passed": not differences,
            "differences": differences,
        })
    return {"total": len(document["cases"]), "failed": failed, "results": results}
