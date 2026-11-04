from app.core.inquiry_parser import parse_inquiry_intent
from app.core.targeted_deduction import generate_targeted_deduction
from app.core.interpretation import explain_correspondences


def test_inquiry_parser_clothing_and_activity():
    q = "推算李笑穿的是什么颜色的衣服，他正在做什么事情"
    res = parse_inquiry_intent(q, "other")
    assert res["subject"] == "李笑"
    assert "clothing_color" in res["intents"]
    assert "current_activity" in res["intents"]


def test_inquiry_parser_location_and_item():
    q = "丢失的钱包在什么方位，能找到吗"
    res = parse_inquiry_intent(q, "other")
    assert "location_direction" in res["intents"]
    assert "item_nature" in res["intents"]


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


def test_targeted_deduction_accessories_and_transport():
    module_results = [
        {
            "module": "meihua",
            "result": {
                "facts": {
                    "body_use": {
                        "body_trigram": {"name": "乾", "element": "金"},
                        "use_trigram": {"name": "震", "element": "木"},
                        "changed_use_trigram": {"name": "离", "element": "火"},
                    },
                    "moving_line": 3,
                },
                "evidence": [{"stage": "original", "code": "body_controls_use"}],
            },
        },
        {
            "module": "qimen",
            "result": {
                "facts": {
                    "zhi_shi_gate": "开门",
                    "zhi_fu_star": "天心",
                }
            },
        },
        {
            "module": "ziwei",
            "result": {
                "facts": {
                    "palaces_by_order": [
                        {
                            "name": "命宫",
                            "main_stars": [{"name": "紫微"}, {"name": "天府"}],
                        }
                    ],
                    "si_hua": {"禄": "廉贞", "权": "破军", "科": "武曲", "忌": "太阳"},
                }
            },
        },
    ]
    context = {
        "category": "travel",
        "question_summary": "推算李笑身上带了什么配饰，怎么坐车出行，他正在干什么",
    }
    res = generate_targeted_deduction(module_results, context)
    assert res["findings_count"] >= 3
    assert res["subject"] == "李笑"

    keys = [f["key"] for f in res["findings"]]
    assert "accessories_items" in keys
    assert "transport_travel" in keys
    assert "current_activity" in keys

    acc_finding = next(f for f in res["findings"] if f["key"] == "accessories_items")
    assert "手表" in acc_finding["conclusion"] or "手环" in acc_finding["conclusion"] or "钥匙" in acc_finding["conclusion"]

    trans_finding = next(f for f in res["findings"] if f["key"] == "transport_travel")
    assert "车" in trans_finding["conclusion"] or "动车" in trans_finding["conclusion"]

    act_finding = next(f for f in res["findings"] if f["key"] == "current_activity")
    assert "开门" in act_finding["conclusion"]


def test_targeted_deduction_health():
    module_results = [
        {
            "module": "meihua",
            "result": {
                "facts": {
                    "body_use": {
                        "body_trigram": {"name": "坎", "element": "水"},
                        "use_trigram": {"name": "离", "element": "火"},
                    },
                    "moving_line": 2,
                },
                "evidence": [{"stage": "original", "code": "body_controls_use"}],
            },
        }
    ]
    context = {
        "category": "other",
        "question_summary": "推算王五最近身体健康怎么样，哪个部位需要注意",
    }
    res = generate_targeted_deduction(module_results, context)
    keys = [f["key"] for f in res["findings"]]
    assert "health_body" in keys
    health_finding = next(f for f in res["findings"] if f["key"] == "health_body")
    assert "肾" in health_finding["conclusion"] or "耳" in health_finding["conclusion"] or "泌尿" in health_finding["conclusion"]

