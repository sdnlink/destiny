from app.core.calendar import calendar_analysis
from app.core.iching import manual_cast as yi_manual_cast
from app.core.iching import number_cast as yi_number_cast
from app.core.meihua import number_cast as meihua_number_cast
from app.core.meihua import time_cast as meihua_time_cast
from app.core.registry import load_rule_registry, load_validation_cases, unknown_rule_ids


def execute_validation_case(case):
    system = case["system"]
    method = case["method"]
    payload = case["input"]
    if system == "calendar" and method == "analyze":
        return calendar_analysis(**payload)
    if system == "zhouyi" and method == "manual":
        return yi_manual_cast(payload["lines"])
    if system == "zhouyi" and method == "numbers":
        return yi_number_cast(payload["lower_number"], payload["upper_number"])
    if system == "meihua" and method == "time":
        return meihua_time_cast(**payload)
    if system == "meihua" and method == "numbers":
        return meihua_number_cast(payload["upper_number"], payload["lower_number"])
    raise ValueError("unsupported validation case: {}/{}".format(system, method))


def compare_subset(actual, expected, path="result"):
    differences = []
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return ["{} expected object, got {}".format(path, type(actual).__name__)]
        for key, expected_value in expected.items():
            child_path = "{}.{}".format(path, key)
            if key not in actual:
                differences.append("{} is missing".format(child_path))
            else:
                differences.extend(compare_subset(actual[key], expected_value, child_path))
        return differences
    if actual != expected:
        differences.append("{} expected {!r}, got {!r}".format(path, expected, actual))
    return differences


def run_validation_cases(case_document=None, registry=None):
    case_document = case_document or load_validation_cases()
    registry = registry or load_rule_registry()
    results = []
    for case in case_document["cases"]:
        try:
            actual = execute_validation_case(case)
            differences = compare_subset(actual, case["expected"])
            unknown = unknown_rule_ids(actual, registry)
            if unknown:
                differences.append("unknown rule ids: {}".format(", ".join(unknown)))
        except Exception as exc:
            differences = ["execution failed: {}".format(exc)]
        results.append({
            "case_id": case["case_id"],
            "system": case["system"],
            "passed": not differences,
            "differences": differences,
        })
    passed = sum(1 for result in results if result["passed"])
    return {
        "case_set_id": case_document["case_set_id"],
        "qualification": case_document["qualification"],
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }
