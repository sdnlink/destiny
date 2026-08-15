#!/usr/bin/env python3
"""Classify a measured bearing into the traditional 24 mountains."""

import argparse
import json


MOUNTAINS = [
    ("子", "坎", "水", "北"), ("癸", "坎", "水", "北"),
    ("丑", "艮", "土", "东北"), ("艮", "艮", "土", "东北"),
    ("寅", "艮", "木", "东北"), ("甲", "震", "木", "东"),
    ("卯", "震", "木", "东"), ("乙", "震", "木", "东"),
    ("辰", "巽", "土", "东南"), ("巽", "巽", "木", "东南"),
    ("巳", "巽", "火", "东南"), ("丙", "离", "火", "南"),
    ("午", "离", "火", "南"), ("丁", "离", "火", "南"),
    ("未", "坤", "土", "西南"), ("坤", "坤", "土", "西南"),
    ("申", "坤", "金", "西南"), ("庚", "兑", "金", "西"),
    ("酉", "兑", "金", "西"), ("辛", "兑", "金", "西"),
    ("戌", "乾", "土", "西北"), ("乾", "乾", "金", "西北"),
    ("亥", "乾", "水", "西北"), ("壬", "坎", "水", "北"),
]


def normalize(degree):
    return degree % 360.0


def signed_delta(degree, center):
    return (degree - center + 180.0) % 360.0 - 180.0


def classify(degree):
    normalized = normalize(degree)
    index = int((normalized + 7.5) // 15.0) % 24
    name, trigram, element, direction = MOUNTAINS[index]
    center = index * 15.0
    offset = signed_delta(normalized, center)
    return {
        "degree": round(normalized, 6),
        "mountain": name,
        "trigram": trigram,
        "element": element,
        "direction": direction,
        "center_degree": center,
        "offset_from_center": round(offset, 6),
        "distance_to_boundary": round(7.5 - abs(offset), 6),
        "start_degree": normalize(center - 7.5),
        "end_degree": normalize(center + 7.5),
    }


def calculate(facing_degree, magnetic_declination=0.0, input_reference="magnetic"):
    if input_reference == "magnetic":
        true_facing = normalize(facing_degree + magnetic_declination)
    else:
        true_facing = normalize(facing_degree)
    true_sitting = normalize(true_facing + 180.0)
    return {
        "input": {
            "facing_degree": facing_degree,
            "reference": input_reference,
            "magnetic_declination": magnetic_declination,
        },
        "true_facing_degree": round(true_facing, 6),
        "true_sitting_degree": round(true_sitting, 6),
        "facing": classify(true_facing),
        "sitting": classify(true_sitting),
        "boundary_warning": classify(true_facing)["distance_to_boundary"] < 1.0,
        "rule_version": "fengshui-direction-1.0.0",
    }


def main():
    parser = argparse.ArgumentParser(description="计算坐向及二十四山归属")
    parser.add_argument("facing_degree", type=float, help="向首方位角，正北为0度，顺时针增加")
    parser.add_argument("--declination", type=float, default=0.0, help="磁偏角：真北角度减磁北角度")
    parser.add_argument("--reference", choices=("magnetic", "true"), default="magnetic",
                        help="输入角度以磁北或真北为基准")
    args = parser.parse_args()
    print(json.dumps(calculate(args.facing_degree, args.declination, args.reference),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
