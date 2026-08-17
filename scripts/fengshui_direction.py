#!/usr/bin/env python3
"""Classify a measured bearing into the traditional 24 mountains."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.fengshui import calculate_direction, classify_direction  # noqa: E402


def classify(degree):
    fact = classify_direction(degree)
    mountain = fact["mountain"]
    return {
        "degree": fact["degree"],
        "mountain": mountain["name"],
        "trigram": mountain["trigram"],
        "element": mountain["element"],
        "direction": mountain["direction"],
        "center_degree": mountain["center_degree"],
        "distance_to_boundary": fact["distance_to_boundary"],
        "start_degree": mountain["start_degree"],
        "end_degree": mountain["end_degree"],
    }


def calculate(facing_degree, magnetic_declination=0.0, input_reference="magnetic", measurement_error=0.0):
    result = calculate_direction(
        facing_degree, input_reference, magnetic_declination, measurement_error
    )
    facts = result["facts"]
    return {
        "input": result["input"],
        "true_facing_degree": facts["true_facing_degree"],
        "true_sitting_degree": facts["true_sitting_degree"],
        "facing": classify(facts["true_facing_degree"]),
        "sitting": classify(facts["true_sitting_degree"]),
        "classification_stable": facts["classification_stable"],
        "boundary_warning": facts["boundary_warning"],
        "rule_version": result["rule_version"],
    }


def main():
    parser = argparse.ArgumentParser(description="计算坐向及二十四山归属")
    parser.add_argument("facing_degree", type=float, help="向首方位角，正北为0度，顺时针增加")
    parser.add_argument("--declination", type=float, default=0.0, help="磁偏角：真北角度减磁北角度")
    parser.add_argument("--reference", choices=("magnetic", "true"), default="magnetic",
                        help="输入角度以磁北或真北为基准")
    parser.add_argument("--error", type=float, default=0.0, help="测量正负误差，单位为度")
    args = parser.parse_args()
    print(json.dumps(calculate_direction(args.facing_degree, args.reference, args.declination, args.error),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
