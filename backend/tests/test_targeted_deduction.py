import pytest
from app.core.inquiry_parser import parse_inquiry_intent
from app.core.targeted_deduction import generate_targeted_deduction
from app.core.interpretation import explain_correspondences


def test_inquiry_parser_clothing_and_activity():
    q = "推算李笑穿的是什么颜色的衣服，他正在做什么事情"
    res = parse_inquiry_intent(q, "other")
    assert res["has_clothing_color"] is True
    assert res["has_current_activity"] is True
    assert res["subject"] == "李笑"
    assert "clothing_color" in res["intents"]
    assert "current_activity" in res["intents"]


def test_inquiry_parser_location_and_item():
    q = "丢失的钱包在什么方位，能找到吗"
    res = parse_inquiry_intent(q, "other")
    assert res["has_location_direction"] is True
    assert res["has_item_nature"] is True
    assert "location_direction" in res["intents"]


def test_targeted_deduction_with_meihua_and_liuyao():
    module_results = [
        {
            "module": "meihua",
            "result": {
                "facts": {
                    "body_use": {
                        "body_trigram": {"name": "艮", "element": "土"},
                        "use_trigram": {"name": "离", "element": "火"},
                        "changed_use_trigram": {"name": "离", "element": "火"},
                    },
                    "moving_line": 1,
                },
                "evidence": [{"stage": "original", "code": "use_generates_body"}],
            },
        },
        {
            "module": "liuyao",
            "result": {
                "facts": {
                    "palace": {"host_line": 1},
                    "line_chart": [
                        {
                            "position": 1,
                            "is_moving": True,
                            "six_relative": "父母",
                            "six_spirit": "朱雀",
                            "element": "火",
                        }
                    ],
                }
            },
        },
    ]
    context = {
        "category": "other",
        "question_summary": "推算李笑穿的是什么颜色的衣服，他正在做什么事情",
    }
    deduction = generate_targeted_deduction(module_results, context)
    assert deduction["findings_count"] >= 2
    assert deduction["subject"] == "李笑"

    keys = [f["key"] for f in deduction["findings"]]
    assert "clothing_color" in keys
    assert "current_activity" in keys

    color_finding = next(f for f in deduction["findings"] if f["key"] == "clothing_color")
    assert "大红色" in color_finding["conclusion"] or "赤红色" in color_finding["conclusion"] or "亮橙色" in color_finding["conclusion"]
    assert len(color_finding["palette"]) > 0

    activity_finding = next(f for f in deduction["findings"] if f["key"] == "current_activity")
    assert "屏幕" in activity_finding["conclusion"] or "文书" in activity_finding["conclusion"] or "手机" in activity_finding["conclusion"]
    assert "朱雀" in activity_finding["conclusion"] or "父母" in activity_finding["conclusion"]


def test_explain_correspondences_includes_targeted_findings():
    module_results = [
        {
            "module": "zhouyi",
            "result": {
                "facts": {
                    "original": {"name": "旅", "ordinal": 56, "upper_trigram": {"name": "离"}, "lower_trigram": {"name": "艮"}},
                    "changed": {"name": "离", "ordinal": 30, "upper_trigram": {"name": "离"}, "lower_trigram": {"name": "离"}},
                    "mutual": {"name": "大过", "ordinal": 28},
                    "opposite": {"name": "丰", "ordinal": 55},
                    "reversed": {"name": "节", "ordinal": 60},
                    "moving_lines": [1],
                }
            },
        }
    ]
    context = {
        "category": "other",
        "question_summary": "推算李笑穿的是什么颜色的衣服，他正在做什么事情",
    }
    res = explain_correspondences(module_results, context)
    assert res is not None
    assert "targeted_findings" in res
    assert res["targeted_findings"]["findings_count"] >= 2
