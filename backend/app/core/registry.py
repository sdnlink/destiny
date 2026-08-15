import hashlib
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RULE_REGISTRY_PATH = PROJECT_ROOT / "data" / "rules" / "mvp-engineering-baseline.json"
VALIDATION_CASES_PATH = PROJECT_ROOT / "data" / "validation-cases" / "mvp-engineering-baseline.json"


def _load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def content_checksum(value):
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_rule_registry(path=RULE_REGISTRY_PATH):
    registry = _load_json(Path(path))
    errors = validate_rule_registry(registry)
    if errors:
        raise ValueError("invalid rule registry: " + "; ".join(errors))
    return {**registry, "checksum": content_checksum(registry)}


def validate_rule_registry(registry):
    errors = []
    required_rule_fields = {
        "rule_id", "version", "system", "school", "status", "title",
        "purpose", "preconditions", "inputs", "procedure", "outputs",
        "source_refs", "limitations", "owner", "reviewers", "implementation",
    }
    rules = registry.get("rules", [])
    identities = set()
    for index, rule in enumerate(rules):
        missing = sorted(required_rule_fields - set(rule))
        if missing:
            errors.append("rule {} missing {}".format(index, ",".join(missing)))
        identity = (rule.get("rule_id"), rule.get("version"))
        if identity in identities:
            errors.append("duplicate rule {}/{}".format(*identity))
        identities.add(identity)
        if rule.get("status") not in {"draft", "in_review", "approved", "published", "deprecated", "retired"}:
            errors.append("rule {} has invalid status".format(rule.get("rule_id")))
        if not rule.get("source_refs"):
            errors.append("rule {} has no source references".format(rule.get("rule_id")))

    rule_ids = {rule.get("rule_id") for rule in rules}
    for rule_set in registry.get("rule_sets", []):
        for reference in rule_set.get("rules", []):
            identity = (reference.get("rule_id"), reference.get("version"))
            if identity not in identities:
                errors.append("rule set references unknown rule {}/{}".format(*identity))
    if len(rule_ids) != len(rules):
        errors.append("MVP registry allows one active version per rule id")
    return errors


def load_validation_cases(path=VALIDATION_CASES_PATH):
    document = _load_json(Path(path))
    cases = document.get("cases", [])
    required = {"case_id", "system", "school", "method", "input", "expected", "tags", "review_status", "source_refs", "reviewers"}
    errors = []
    seen = set()
    for index, case in enumerate(cases):
        missing = sorted(required - set(case))
        if missing:
            errors.append("case {} missing {}".format(index, ",".join(missing)))
        if case.get("case_id") in seen:
            errors.append("duplicate case {}".format(case.get("case_id")))
        seen.add(case.get("case_id"))
    if errors:
        raise ValueError("invalid validation cases: " + "; ".join(errors))
    return {**document, "checksum": content_checksum(document)}


def rule_index(registry=None):
    registry = registry or load_rule_registry()
    return {rule["rule_id"]: rule for rule in registry["rules"]}


def referenced_rule_ids(result):
    references = set()
    for section in ("steps", "evidence", "judgements"):
        for item in result.get(section, []):
            references.update(item.get("rule_ids", []))
    return references


def unknown_rule_ids(result, registry=None):
    known = set(rule_index(registry))
    return sorted(referenced_rule_ids(result) - known)
