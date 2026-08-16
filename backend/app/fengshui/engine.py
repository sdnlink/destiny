from .models import DirectionInput
from .rules import MOUNTAINS


ENGINE_VERSION = "fengshui-direction-engine-2.0.0"
RULE_VERSION = "fengshui-direction-engineering-baseline-2.0.0"
BOUNDARY_WARNING_DEGREES = 1.0


def _normalize(degree):
    return round(degree % 360.0, 10)


def _mountain_at(degree):
    index = int((_normalize(degree) + 7.5) // 15.0) % 24
    return MOUNTAINS[index]


def _angular_distance(first, second):
    difference = abs(_normalize(first) - _normalize(second))
    return min(difference, 360.0 - difference)


def _boundary_distance(degree):
    position = (_normalize(degree) + 7.5) % 15.0
    return round(min(position, 15.0 - position), 10)


def _candidate_mountains(degree, error):
    primary = _mountain_at(degree)
    if error == 0:
        return [primary]
    if error >= 180:
        return list(MOUNTAINS)
    candidates = [
        mountain for mountain in MOUNTAINS
        if _angular_distance(degree, mountain.center_degree) <= error + 7.5
    ]
    return sorted(candidates, key=lambda mountain: _angular_distance(degree, mountain.center_degree))


def _direction_fact(degree, error):
    mountain = _mountain_at(degree)
    candidates = _candidate_mountains(degree, error)
    return {
        "degree": degree,
        "mountain": mountain.to_dict(),
        "distance_to_boundary": _boundary_distance(degree),
        "measurement_interval": {
            "start_degree": _normalize(degree - error),
            "end_degree": _normalize(degree + error),
            "wraps_north": error < 180 and _normalize(degree - error) > _normalize(degree + error),
        },
        "classification_stable": len(candidates) == 1,
        "candidate_mountains": [candidate.to_dict() for candidate in candidates],
    }


def classify_direction(degree, measurement_error=0.0):
    request = DirectionInput(degree, input_reference="true", measurement_error=measurement_error)
    return _direction_fact(_normalize(request.facing_degree), request.measurement_error)


def calculate_direction(
    facing_degree,
    input_reference="magnetic",
    magnetic_declination=0.0,
    measurement_error=0.0,
    declination_source=None,
    measurement_method=None,
):
    request = DirectionInput(
        facing_degree=facing_degree,
        input_reference=input_reference,
        magnetic_declination=magnetic_declination,
        measurement_error=measurement_error,
        declination_source=declination_source,
        measurement_method=measurement_method,
    )
    normalized_input_degree = _normalize(request.facing_degree)
    applied_declination = request.magnetic_declination if request.input_reference == "magnetic" else 0.0
    true_facing = _normalize(normalized_input_degree + applied_declination)
    true_sitting = _normalize(true_facing + 180.0)
    facing = _direction_fact(true_facing, request.measurement_error)
    sitting = _direction_fact(true_sitting, request.measurement_error)
    boundary_warning = (
        facing["distance_to_boundary"] < BOUNDARY_WARNING_DEGREES
        or not facing["classification_stable"]
    )
    warnings = []
    if request.input_reference == "true" and request.magnetic_declination != 0:
        warnings.append("输入已基于真北，所填磁偏角未参与修正。")
    if boundary_warning:
        warnings.append("向首测量接近二十四山分界或误差跨界，应在不同位置和时段复测。")
    warnings.append("本结果仅为真北坐向和二十四山事实，不包含八宅、玄空飞星或吉凶判断。")
    raw_input = {
        "facing_degree": request.facing_degree,
        "input_reference": request.input_reference,
        "magnetic_declination": request.magnetic_declination,
        "measurement_error": request.measurement_error,
        "declination_source": request.declination_source,
        "measurement_method": request.measurement_method,
    }
    normalized = {
        "input_degree": normalized_input_degree,
        "input_reference": request.input_reference,
        "applied_declination": applied_declination,
        "true_facing_degree": true_facing,
        "true_sitting_degree": true_sitting,
        "measurement_error": request.measurement_error,
    }
    return {
        "schema_version": "2.0",
        "system": "fengshui",
        "school": "twenty-four-mountains-engineering-baseline",
        "engine_version": ENGINE_VERSION,
        "algorithm_version": ENGINE_VERSION,
        "rule_version": RULE_VERSION,
        "input": raw_input,
        "normalized_input": normalized,
        "facts": {
            "true_facing_degree": true_facing,
            "true_sitting_degree": true_sitting,
            "facing": facing,
            "sitting": sitting,
            "boundary_warning": boundary_warning,
            "classification_stable": facing["classification_stable"] and sitting["classification_stable"],
        },
        "calculation_trace": [
            "normalize input angle to [0, 360): {} degrees".format(normalized_input_degree),
            "apply magnetic declination {} degrees: true facing {} degrees".format(applied_declination, true_facing),
            "rotate 180 degrees: true sitting {} degrees".format(true_sitting),
            "classify facing as {} and sitting as {} with left-closed right-open sectors".format(
                facing["mountain"]["name"], sitting["mountain"]["name"]
            ),
            "propagate +/-{} degree measurement error to candidate mountains".format(request.measurement_error),
        ],
        "steps": [
            {
                "sequence": 1, "operation": "normalize_compass_degree",
                "inputs": {"facing_degree": request.facing_degree},
                "output": {"normalized_degree": normalized_input_degree},
                "rule_ids": ["FS-DIRECTION-NORMALIZE-001"],
            },
            {
                "sequence": 2, "operation": "convert_magnetic_to_true_north",
                "inputs": {"reference": request.input_reference, "magnetic_declination": request.magnetic_declination},
                "output": {"applied_declination": applied_declination, "true_facing_degree": true_facing},
                "rule_ids": ["FS-DECLINATION-001"],
            },
            {
                "sequence": 3, "operation": "derive_sitting_and_twenty_four_mountains",
                "inputs": {"true_facing_degree": true_facing},
                "output": {"true_sitting_degree": true_sitting, "facing": facing["mountain"], "sitting": sitting["mountain"]},
                "rule_ids": ["FS-24MOUNTAIN-001"],
            },
            {
                "sequence": 4, "operation": "propagate_measurement_uncertainty",
                "inputs": {"measurement_error": request.measurement_error},
                "output": {
                    "classification_stable": facing["classification_stable"],
                    "facing_candidates": [item["name"] for item in facing["candidate_mountains"]],
                    "sitting_candidates": [item["name"] for item in sitting["candidate_mountains"]],
                    "distance_to_boundary": facing["distance_to_boundary"],
                    "boundary_warning": boundary_warning,
                },
                "rule_ids": ["FS-UNCERTAINTY-001"],
            },
        ],
        "evidence": [],
        "judgements": [],
        "warnings": warnings,
    }
