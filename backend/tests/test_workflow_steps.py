"""测试：七步工作流 steps.py 的可独立调用逻辑。

覆盖范围：
1. 月令 → 节气（近似）映射表 MONTH_BRANCH：12 地支全覆盖、节气名唯一、未知输入兜底
2. step1 信息校验：缺失字段识别、别名归一的分类标签
3. step2 盘面格式化：calendar 单独提取、其它体系字段默认值、未知模块标签兜底
4. step3 用神定位：分类映射完整性、别名归一、多方人物取象、按体系输出
5. 六爻盘面辅助函数：爻表提取、动爻地支去重、用神五行推导、世应关系、干支冲合
6. step4 旺衰五档（按 WF-WANGSHUAI-001 口径：旺/相/休/囚/死）
7. step5 象义映射（卦象解释数据层用 mock 隔离，不依赖真实语料）
8. step6 吉凶打分（WF-FORTUNE-001 全部分支）、step7 建议与免责
9. _calculate_trend / _calculate_timing 趋势与应期推算

不覆盖：需要 FastAPI Request / 真实排盘引擎上下文的编排入口（见最终报告说明）。
"""

import sys
import unittest
from pathlib import Path
from unittest import mock


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.common.categories import CATEGORIES
from app.session import create_session
from app.workflow import steps as wf
from app.workflow.engine import WorkflowEngine
from app.workflow.format import render_fixed_format, render_plate_text


# ============================================================
# 测试辅助
# ============================================================

def _line(
    position,
    six_relative="",
    element="",
    branch="",
    roles=(),
    moving=False,
    spirit="",
):
    return {
        "position": position,
        "six_relative": six_relative,
        "element": element,
        "najia_branch": branch,
        "roles": list(roles),
        "is_moving": moving,
        "six_spirit": spirit,
        "yin_yang": "阳",
    }


def _plate(calendar=None, lines=None, meihua_facts=None):
    """构造 step4/step5 需要的 plate_data 结构。"""
    plates = {}
    if lines is not None:
        plates["liuyao"] = {"facts": {"line_chart": lines}}
    if meihua_facts is not None:
        plates["meihua"] = {"facts": meihua_facts}
    return {"calendar": calendar or {}, "plates": plates}


def _calendar(month_branch, day_branch, month_text="", day_text=""):
    return {
        "ganzhi": {
            "month": {"branch": month_branch, "text": month_text or month_branch},
            "day": {"branch": day_branch, "text": day_text or day_branch},
        }
    }


def _wangshuai(level, tiyong_code="", tiyong_type=""):
    tiyong = {}
    if tiyong_code:
        tiyong = {"code": tiyong_code, "type": tiyong_type or tiyong_code}
    return {
        "yongshen_wangshuai": {"level": level},
        "tiyong_relation": tiyong,
    }


# ============================================================
# 月令 → 节气（近似）映射表
# ============================================================

class TestMonthBranchMapping(unittest.TestCase):
    EXPECTED = {
        "寅": "立春", "卯": "惊蛰", "辰": "清明", "巳": "立夏",
        "午": "芒种", "未": "小暑", "申": "立秋", "酉": "白露",
        "戌": "寒露", "亥": "立冬", "子": "大雪", "丑": "小寒",
    }

    def test_covers_all_twelve_branches(self):
        self.assertEqual(len(wf.MONTH_BRANCH), 12)
        self.assertEqual(set(wf.MONTH_BRANCH), set(self.EXPECTED))

    def test_every_branch_maps_to_its_expected_solar_term(self):
        for branch, term in self.EXPECTED.items():
            with self.subTest(branch=branch):
                self.assertEqual(wf.MONTH_BRANCH[branch], term)

    def test_values_are_unique(self):
        values = list(wf.MONTH_BRANCH.values())
        self.assertEqual(len(values), len(set(values)))

    def test_unknown_branch_has_no_mapping(self):
        # 未知输入必须拿不到节气，不能静默返回某个默认节气
        self.assertEqual(wf.MONTH_BRANCH.get("甲", ""), "")
        self.assertEqual(wf.MONTH_BRANCH.get("unknown", ""), "")
        self.assertNotIn("子丑", wf.MONTH_BRANCH)

    def test_unknown_month_branch_does_not_break_timing(self):
        plate = _plate(calendar=_calendar("X", "子"))
        text = wf._calculate_timing(plate, _wangshuai("平"), {}, "平")
        self.assertIn("月令「X」", text)
        # 未知月支回落为无节气，不能输出「（）」这种空括号占位
        self.assertNotIn("（）", text)
        self.assertNotIn("(）", text)

    def test_known_month_branch_still_keeps_solar_term_in_parentheses(self):
        plate = _plate(calendar=_calendar("寅", "子"))
        text = wf._calculate_timing(plate, _wangshuai("平"), {}, "平")
        self.assertIn("月令「寅」（立春）", text)


# ============================================================
# step1：信息校验
# ============================================================

class TestStep1InfoValidation(unittest.TestCase):
    def test_complete_session_is_ready(self):
        session = create_session(
            question="是否接受新工作",
            category="career",
            casting_method="time",
            casting_source={"local_datetime": "2026-08-26T10:00:00"},
        )
        result = wf.step1_info_validation(session)
        self.assertEqual(result["step"], 1)
        self.assertEqual(result["missing_fields"], [])
        self.assertTrue(result["ready"])
        self.assertEqual(result["category_label"], "事业")
        self.assertEqual(result["question"], "是否接受新工作")

    def test_blank_question_is_missing(self):
        session = create_session(question="   ", casting_method="time",
                                 casting_source={"local_datetime": "2026-08-26T10:00:00"})
        result = wf.step1_info_validation(session)
        self.assertIn("求测事由", result["missing_fields"])
        self.assertFalse(result["ready"])

    def test_time_method_without_datetime_is_missing(self):
        for method in ("auto", "time"):
            with self.subTest(method=method):
                session = create_session(question="测试", casting_method=method)
                result = wf.step1_info_validation(session)
                self.assertIn("起盘时间", result["missing_fields"])
                self.assertFalse(result["ready"])

    def test_numbers_method_without_numbers_is_missing(self):
        session = create_session(question="测试", casting_method="numbers")
        result = wf.step1_info_validation(session)
        self.assertIn("报数", result["missing_fields"])
        self.assertFalse(result["ready"])

    def test_numbers_method_with_numbers_is_ready(self):
        session = create_session(question="测试", casting_method="numbers",
                                 casting_source={"numbers": [1, 2, 3]})
        result = wf.step1_info_validation(session)
        self.assertEqual(result["missing_fields"], [])
        self.assertTrue(result["ready"])

    def test_manual_method_needs_no_casting_source(self):
        session = create_session(question="测试", casting_method="manual")
        result = wf.step1_info_validation(session)
        self.assertEqual(result["missing_fields"], [])

    def test_legacy_category_alias_is_normalized_in_label(self):
        session = create_session(question="测试", category="wealth",
                                 casting_method="manual")
        result = wf.step1_info_validation(session)
        self.assertEqual(result["category_label"], "财运")

    def test_unknown_category_falls_back_to_other_label(self):
        session = create_session(question="测试", category="not-a-category",
                                 casting_method="manual")
        result = wf.step1_info_validation(session)
        self.assertEqual(result["category_label"], "其他谋事")


# ============================================================
# step2：盘面格式化
# ============================================================

class TestStep2FormatPlate(unittest.TestCase):
    def test_calendar_is_extracted_separately(self):
        module_results = [
            {"module": "calendar", "result": {"ganzhi": {"day": {"branch": "子"}}}},
            {"module": "liuyao", "result": {
                "facts": {"moving_line": 3},
                "calculation_trace": ["step"],
                "steps": [{"name": "装卦"}],
                "warnings": ["w1"],
                "engine_version": "1.0",
                "rule_version": "r1",
            }},
        ]
        result = wf.step2_format_plate(module_results, ["calendar", "liuyao"])

        self.assertEqual(result["step"], 2)
        self.assertEqual(result["systems"], ["calendar", "liuyao"])
        self.assertEqual(result["calendar"], {"ganzhi": {"day": {"branch": "子"}}})
        self.assertNotIn("calendar", result["plates"])

        plate = result["plates"]["liuyao"]
        self.assertEqual(plate["system_label"], "六爻")
        self.assertEqual(plate["facts"], {"moving_line": 3})
        self.assertEqual(plate["calculation_trace"], ["step"])
        self.assertEqual(plate["steps"], [{"name": "装卦"}])
        self.assertEqual(plate["warnings"], ["w1"])
        self.assertEqual(plate["engine_version"], "1.0")
        self.assertEqual(plate["rule_version"], "r1")

    def test_missing_optional_fields_use_defaults(self):
        module_results = [{"module": "meihua", "result": {}}]
        plate = wf.step2_format_plate(module_results, ["meihua"])["plates"]["meihua"]
        self.assertEqual(plate["system_label"], "梅花易数")
        self.assertEqual(plate["facts"], {})
        self.assertEqual(plate["calculation_trace"], [])
        self.assertEqual(plate["steps"], [])
        self.assertEqual(plate["warnings"], [])
        self.assertEqual(plate["engine_version"], "")
        self.assertEqual(plate["rule_version"], "")

    def test_unknown_module_label_falls_back_to_module_key(self):
        module_results = [{"module": "unknown_system", "result": {}}]
        plate = wf.step2_format_plate(module_results, ["unknown_system"])["plates"]["unknown_system"]
        self.assertEqual(plate["system_label"], "unknown_system")

    def test_every_dispatchable_system_has_a_chinese_label(self):
        """标签表缺项时 step2 会直接把 qimen/bazi 当标签发给前端。"""
        from app.core.interpretation import MODULE_LABELS
        from app.workflow.scheduler import SYSTEM_LABELS

        missing = [
            key for key in SYSTEM_LABELS
            if key != "calendar" and key not in MODULE_LABELS
        ]
        self.assertEqual(missing, [])
        for key, label in SYSTEM_LABELS.items():
            if key == "calendar":
                continue
            self.assertTrue(
                MODULE_LABELS[key].startswith(label.split("神课")[0].split("纳甲")[0]),
                f"{key} 标签不一致：{MODULE_LABELS[key]} vs {label}",
            )

    def test_empty_module_results(self):
        result = wf.step2_format_plate([], [])
        self.assertEqual(result["plates"], {})
        self.assertIsNone(result["calendar"])
        self.assertEqual(result["systems"], [])

    def test_none_calendar_when_no_calendar_module(self):
        result = wf.step2_format_plate([{"module": "liuyao", "result": {}}], ["liuyao"])
        self.assertIsNone(result["calendar"])


# ============================================================
# step3：用神定位
# ============================================================

class TestStep3Yongshen(unittest.TestCase):
    def test_both_yongshen_tables_cover_every_category(self):
        self.assertEqual(set(wf.CATEGORY_YONGSHEN), set(CATEGORIES))
        self.assertEqual(set(wf.MEIHUA_YONGSHEN), set(CATEGORIES))

    def test_career_uses_guangui(self):
        session = create_session(question="能否升职", category="career")
        result = wf.step3_identify_yongshen(session, {"systems": ["liuyao"]})
        self.assertEqual(result["primary_yongshen"], "官鬼")
        self.assertEqual(result["secondary_yongshen"], "父母")
        self.assertEqual(result["category"], "career")
        self.assertEqual(result["category_label"], "事业")
        self.assertIn("官鬼", result["logic"])

    def test_legacy_alias_is_normalized(self):
        session = create_session(question="投资是否可行", category="wealth")
        result = wf.step3_identify_yongshen(session, {"systems": []})
        self.assertEqual(result["category"], "finance")
        self.assertEqual(result["primary_yongshen"], "妻财")

    def test_unknown_category_falls_back_to_other(self):
        session = create_session(question="随便问问", category="???")
        result = wf.step3_identify_yongshen(session, {"systems": []})
        self.assertEqual(result["category"], "other")
        self.assertEqual(result["primary_yongshen"], "世爻")

    def test_yongshen_by_system_only_for_selected_systems(self):
        session = create_session(question="测试", category="study")
        meihua_only = wf.step3_identify_yongshen(session, {"systems": ["meihua"]})
        self.assertEqual(set(meihua_only["yongshen_by_system"]), {"meihua"})

        both = wf.step3_identify_yongshen(session, {"systems": ["meihua", "liuyao"]})
        self.assertEqual(set(both["yongshen_by_system"]), {"meihua", "liuyao"})
        self.assertEqual(both["yongshen_by_system"]["liuyao"]["primary"], "父母")

    def test_party_yongshen_detected_from_question(self):
        session = create_session(question="我和对方合作能否成功", category="career")
        result = wf.step3_identify_yongshen(session, {"systems": []})
        self.assertEqual(len(result["party_yongshen"]), 2)
        self.assertEqual([p["party"] for p in result["party_yongshen"]],
                         ["求测人（世爻/体卦）", "对方（应爻/用卦）"])

    def test_no_party_yongshen_for_single_person_question(self):
        session = create_session(question="这份工作能否顺利入职", category="career")
        result = wf.step3_identify_yongshen(session, {"systems": []})
        self.assertEqual(result["party_yongshen"], [])

    def test_empty_question_does_not_raise(self):
        session = create_session(question="", category="career")
        result = wf.step3_identify_yongshen(session, {})
        self.assertEqual(result["party_yongshen"], [])
        self.assertEqual(result["yongshen_by_system"], {})


# ============================================================
# 六爻盘面辅助函数
# ============================================================

class TestLiuyaoPlateHelpers(unittest.TestCase):
    def test_line_chart_returns_empty_for_non_liuyao_plate(self):
        self.assertEqual(wf._liuyao_line_chart({}), [])
        self.assertEqual(wf._liuyao_line_chart({"plates": {"meihua": {"facts": {}}}}), [])
        self.assertEqual(wf._liuyao_line_chart({"plates": {"liuyao": {"facts": {"line_chart": None}}}}), [])

    def test_line_chart_filters_non_dict_entries(self):
        plate = _plate(lines=[_line(1, "官鬼", "木", "寅"), "bad", None, 3])
        self.assertEqual(len(wf._liuyao_line_chart(plate)), 1)

    def test_extract_moving_branches_only_moving_and_deduplicated(self):
        plate = _plate(lines=[
            _line(1, "官鬼", "木", "寅", moving=True),
            _line(2, "妻财", "土", "辰", moving=False),
            _line(3, "父母", "水", "子", moving=True),
            _line(4, "兄弟", "土", "辰", moving=True),
            _line(5, "子孙", "火", "午", moving=True),
        ])
        self.assertEqual(wf._extract_moving_branches(plate), ["寅", "子", "辰", "午"])

    def test_extract_moving_branches_skips_missing_branch(self):
        plate = _plate(lines=[_line(1, "官鬼", "木", "", moving=True)])
        self.assertEqual(wf._extract_moving_branches(plate), [])

    def test_extract_moving_branches_without_liuyao_plate(self):
        self.assertEqual(wf._extract_moving_branches({"plates": {}}), [])

    # ---- 用神五行推导 ----

    def test_resolve_yongshen_element_without_primary(self):
        element, note = wf._resolve_yongshen_element(_plate(lines=[]), "")
        self.assertEqual(element, "")
        self.assertIn("未提供用神", note)

    def test_resolve_yongshen_element_from_six_relative_line(self):
        plate = _plate(lines=[_line(3, "官鬼", "火", "午"), _line(1, "妻财", "土", "辰")])
        element, note = wf._resolve_yongshen_element(plate, "官鬼")
        self.assertEqual(element, "火")
        self.assertIn("取第3爻", note)
        self.assertIn("火", note)

    def test_resolve_yongshen_element_prefers_moving_line_when_two_appear(self):
        plate = _plate(lines=[
            _line(1, "官鬼", "木", "寅", moving=False),
            _line(4, "官鬼", "火", "午", moving=True),
        ])
        element, note = wf._resolve_yongshen_element(plate, "官鬼")
        self.assertEqual(element, "火")
        self.assertIn("取第4爻", note)
        self.assertIn("两现", note)
        self.assertIn("动爻", note)

    def test_resolve_yongshen_element_for_shi_and_ying(self):
        plate = _plate(lines=[
            _line(1, "父母", "水", "子", roles=["世"]),
            _line(4, "妻财", "土", "未", roles=["应"]),
        ])
        self.assertEqual(wf._resolve_yongshen_element(plate, "世爻")[0], "水")
        self.assertEqual(wf._resolve_yongshen_element(plate, "应爻")[0], "土")
        # 寻人等「按关系」定用神 -> 取应爻
        self.assertEqual(wf._resolve_yongshen_element(plate, "用神（按关系）")[0], "土")

    def test_resolve_yongshen_element_supports_slash_alternatives(self):
        plate = _plate(lines=[
            _line(1, "妻财", "土", "辰"),
            _line(2, "官鬼", "金", "申"),
        ])
        element, _ = wf._resolve_yongshen_element(plate, "妻财/官鬼")
        self.assertEqual(element, "土")

    def test_resolve_yongshen_element_falls_back_to_meihua_use_trigram(self):
        plate = _plate(meihua_facts={
            "body_use": {
                "body_trigram": {"name": "艮", "element": "土"},
                "use_trigram": {"name": "离", "element": "火"},
            }
        })
        element, note = wf._resolve_yongshen_element(plate, "官鬼")
        self.assertEqual(element, "火")
        self.assertIn("梅花", note)
        self.assertIn("离", note)

    def test_resolve_yongshen_element_without_any_basis(self):
        element, note = wf._resolve_yongshen_element({"plates": {}}, "官鬼")
        self.assertEqual(element, "")
        self.assertIn("缺少可用的用神定位依据", note)

    def test_resolve_yongshen_element_ignores_line_without_element(self):
        plate = _plate(
            lines=[_line(1, "官鬼", "", "寅")],
            meihua_facts={"body_use": {"use_trigram": {"name": "坎", "element": "水"}}},
        )
        self.assertEqual(wf._resolve_yongshen_element(plate, "官鬼")[0], "水")

    # ---- 世应关系 ----

    def test_shiying_relation_without_line_chart(self):
        result = wf._extract_shiying_relation({"plates": {}})
        self.assertEqual(result, {"note": "当前盘面无六爻纳甲，世应关系不适用"})

    def test_shiying_relation_without_shi_line(self):
        plate = _plate(lines=[_line(4, "妻财", "土", "未", roles=["应"])])
        self.assertIn("note", wf._extract_shiying_relation(plate))

    def test_shiying_relation_body_controls_use(self):
        plate = _plate(lines=[
            _line(1, "父母", "木", "寅", roles=["世"]),
            _line(4, "妻财", "土", "未", roles=["应"]),
        ])
        result = wf._extract_shiying_relation(plate)
        self.assertEqual(result["shi"]["position"], 1)
        self.assertEqual(result["ying"]["position"], 4)
        self.assertEqual(result["shi"]["element"], "木")
        self.assertEqual(result["relation"]["code"], "body_controls_use")
        self.assertEqual(result["relation"]["label"], "世克应")
        self.assertTrue(result["relation"]["meaning"])

    def test_shiying_relation_same_element(self):
        plate = _plate(lines=[
            _line(1, "父母", "水", "子", roles=["世"]),
            _line(4, "妻财", "水", "亥", roles=["应"]),
        ])
        self.assertEqual(wf._extract_shiying_relation(plate)["relation"]["code"], "same_element")
        self.assertEqual(wf._extract_shiying_relation(plate)["relation"]["label"], "世应比和")

    def test_shiying_relation_use_controls_body(self):
        plate = _plate(lines=[
            _line(1, "父母", "木", "寅", roles=["世"]),
            _line(4, "官鬼", "金", "申", roles=["应"]),
        ])
        relation = wf._extract_shiying_relation(plate)["relation"]
        self.assertEqual(relation["code"], "use_controls_body")
        self.assertEqual(relation["label"], "应克世")

    def test_shiying_relation_missing_element_omits_relation(self):
        plate = _plate(lines=[
            _line(1, "父母", "", "", roles=["世"]),
            _line(4, "妻财", "土", "未", roles=["应"]),
        ])
        result = wf._extract_shiying_relation(plate)
        self.assertIn("shi", result)
        self.assertNotIn("relation", result)

    # ---- 干支冲合 ----

    def test_ganzhi_interactions_clash_with_day(self):
        items = wf._extract_ganzhi_interactions(["午"], "子", "寅")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["day_relation"], "冲")
        self.assertEqual(items[0]["month_relation"], "")
        self.assertIn("与日辰子相冲", items[0]["detail"])
        self.assertIn("午（火）", items[0]["detail"])

    def test_ganzhi_interactions_combine_with_day(self):
        items = wf._extract_ganzhi_interactions(["午"], "未", "寅")
        self.assertEqual(items[0]["day_relation"], "合")
        self.assertIn("与日辰未相合", items[0]["detail"])

    def test_ganzhi_interactions_clash_and_combine_with_month(self):
        items = wf._extract_ganzhi_interactions(["午"], "卯", "子")
        self.assertEqual(items[0]["month_relation"], "冲")
        self.assertIn("与月令子相冲", items[0]["detail"])

        items = wf._extract_ganzhi_interactions(["午"], "卯", "未")
        self.assertEqual(items[0]["month_relation"], "合")
        self.assertIn("与月令未相合", items[0]["detail"])

    def test_ganzhi_interactions_without_any_relation(self):
        items = wf._extract_ganzhi_interactions(["寅"], "卯", "辰")
        self.assertEqual(items[0]["day_relation"], "")
        self.assertEqual(items[0]["month_relation"], "")
        self.assertIn("与日辰月令无冲合，应期以逢值逢冲论", items[0]["detail"])

    def test_ganzhi_interactions_empty_input(self):
        self.assertEqual(wf._extract_ganzhi_interactions([], "子", "丑"), [])

    def test_ganzhi_interactions_unknown_branch(self):
        items = wf._extract_ganzhi_interactions(["X"], "子", "丑")
        self.assertEqual(items[0]["branch"], "X")
        self.assertEqual(items[0]["day_relation"], "")
        self.assertIn("动爻X", items[0]["detail"])


# ============================================================
# step4：旺衰
# ============================================================

class TestStep4Wangshuai(unittest.TestCase):
    def _session(self, category="career"):
        return create_session(question="事业能否推进", category=category)

    def _analyze(self, month, day, lines, primary="官鬼"):
        plate = _plate(calendar=_calendar(month, day), lines=lines)
        return wf.step4_wangshuai_analysis(self._session(), plate,
                                          {"primary_yongshen": primary})

    def test_same_element_as_month_is_wang(self):
        result = self._analyze("寅", "卯", [_line(1, "官鬼", "木", "寅")])
        self.assertEqual(result["step"], 4)
        self.assertEqual(result["yongshen_wangshuai"]["level"], "旺（得令）")
        self.assertIn("同气", result["yongshen_wangshuai"]["reason"])
        self.assertEqual(result["calendar_context"]["month_element"], "木")
        self.assertIn("WF-WANGSHUAI-001", result["rule_ids"])

    def test_month_generates_yongshen_is_xiang(self):
        result = self._analyze("子", "卯", [_line(1, "官鬼", "木", "寅")])
        self.assertEqual(result["yongshen_wangshuai"]["level"], "相（月令生用）")
        self.assertIn("益", result["yongshen_wangshuai"]["reason"].replace("得生", "益"))

    def test_wangshuai_level_is_always_one_of_five_grades(self):
        cases = [("寅", "木"), ("申", "木"), ("午", "木"), ("辰", "木")]
        for month, element in cases:
            with self.subTest(month=month):
                result = self._analyze(month, "卯", [_line(1, "官鬼", element, "寅")])
                level = result["yongshen_wangshuai"]["level"]
                self.assertTrue(
                    any(level.startswith(prefix) for prefix in ("旺", "相", "休", "囚", "死")),
                    level,
                )
                self.assertTrue(result["yongshen_wangshuai"]["reason"])

    def test_documented_five_grade_rule(self):
        """WF-WANGSHUAI-001 文档口径：月令克用=囚、用神生月令=休、用神克月令=死。

        此前实现把三档判反，已按 ADR-015 与规则登记表修正，此处钉住口径。
        """
        # 月令木 克 用神土 -> 囚
        self.assertTrue(
            self._analyze("寅", "卯", [_line(1, "官鬼", "土", "辰")])
            ["yongshen_wangshuai"]["level"].startswith("囚")
        )
        # 用神木 生 月令火 -> 休
        self.assertTrue(
            self._analyze("午", "卯", [_line(1, "官鬼", "木", "寅")])
            ["yongshen_wangshuai"]["level"].startswith("休")
        )
        # 用神木 克 月令土 -> 死
        self.assertTrue(
            self._analyze("辰", "卯", [_line(1, "官鬼", "木", "寅")])
            ["yongshen_wangshuai"]["level"].startswith("死")
        )

    def test_five_grades_drive_fortune_score(self):
        """step4 档位直接决定 step6 打分：旺/相 +2、休 0、囚/死 -2。

        同时校验 reason 文案与档位一致（旧实现里理由和档位互相矛盾）。
        """
        session = self._session()
        cases = [
            ("寅", "木", "旺", "同气", 2),
            ("子", "木", "相", "生用神", 2),
            ("午", "木", "休", "生月令", 0),
            ("寅", "土", "囚", "克用神", -2),
            ("辰", "木", "死", "克月令", -2),
        ]
        for month, element, prefix, reason_keyword, expected_score in cases:
            with self.subTest(month=month, element=element):
                plate = _plate(calendar=_calendar(month, "卯"),
                               lines=[_line(1, "官鬼", element, "寅")])
                step4 = wf.step4_wangshuai_analysis(
                    session, plate, {"primary_yongshen": "官鬼"})
                wangshuai = step4["yongshen_wangshuai"]
                self.assertTrue(wangshuai["level"].startswith(prefix), wangshuai["level"])
                self.assertIn(reason_keyword, wangshuai["reason"])

                step6 = wf.step6_synthesis_judgement(
                    session, [], plate, {"primary_yongshen": "官鬼"}, step4, {})
                self.assertEqual(step6["fortune_score"], expected_score)

    def test_missing_yongshen_element_reports_source(self):
        result = self._analyze("寅", "卯", [], primary="")
        self.assertEqual(result["yongshen_wangshuai"]["element"], "")
        self.assertEqual(result["yongshen_wangshuai"]["level"], "平")
        self.assertIn("未提供用神", result["yongshen_wangshuai"]["reason"])

    def test_yongshen_element_without_month_element_stays_flat(self):
        plate = _plate(lines=[_line(1, "官鬼", "木", "寅")])
        result = wf.step4_wangshuai_analysis(self._session(), plate,
                                             {"primary_yongshen": "官鬼"})
        self.assertEqual(result["yongshen_wangshuai"]["element"], "木")
        self.assertEqual(result["yongshen_wangshuai"]["level"], "平")
        self.assertEqual(result["yongshen_wangshuai"]["reason"], "")
        self.assertEqual(result["calendar_context"]["month_element"], "")

    def test_plain_string_pillars_are_supported(self):
        plate = {
            "calendar": {"ganzhi": {"month": "寅", "day": "午"}},
            "plates": {},
        }
        result = wf.step4_wangshuai_analysis(self._session(), plate, {"primary_yongshen": ""})
        self.assertEqual(result["calendar_context"]["month_pillar"], "寅")
        self.assertEqual(result["calendar_context"]["day_pillar"], "午")
        self.assertEqual(result["calendar_context"]["month_branch"], "寅")

    def test_tiyong_relation_comes_from_meihua_facts(self):
        plate = _plate(meihua_facts={
            "body_use": {
                "body_trigram": {"name": "艮", "element": "土"},
                "use_trigram": {"name": "离", "element": "火"},
            },
            "body_use_relation": {"original": {"code": "use_generates_body", "label": "用生体"}},
        })
        result = wf.step4_wangshuai_analysis(self._session(), plate, {"primary_yongshen": ""})
        self.assertEqual(result["tiyong_relation"]["code"], "use_generates_body")
        self.assertEqual(result["tiyong_relation"]["body_element"], "土")
        self.assertEqual(result["tiyong_relation"]["use_element"], "火")
        self.assertTrue(result["tiyong_relation"]["meaning"])
        self.assertTrue(any(line.startswith("体用关系：") for line in result["analysis_chain"]))

    def test_tiyong_relation_absent_without_meihua_relation(self):
        result = wf.step4_wangshuai_analysis(self._session(), _plate(), {"primary_yongshen": ""})
        self.assertIsNone(result["tiyong_relation"])

    def test_analysis_chain_contains_day_reference_and_interactions(self):
        result = self._analyze("寅", "子", [_line(1, "官鬼", "木", "午", moving=True)])
        self.assertTrue(result["analysis_chain"])
        self.assertTrue(any("日辰为子" in line for line in result["analysis_chain"]))
        self.assertEqual(result["ganzhi_interactions"][0]["day_relation"], "冲")

    def test_shiying_relation_included_for_liuyao_plate(self):
        result = self._analyze("寅", "卯", [
            _line(1, "父母", "木", "寅", roles=["世"]),
            _line(4, "妻财", "土", "未", roles=["应"]),
        ])
        self.assertEqual(result["shiying_relation"]["relation"]["label"], "世克应")

    def test_empty_plate_does_not_raise(self):
        result = wf.step4_wangshuai_analysis(self._session(), {}, {"primary_yongshen": "官鬼"})
        self.assertEqual(result["calendar_context"]["month_branch"], "")
        self.assertEqual(result["ganzhi_interactions"], [])
        self.assertIn("note", result["shiying_relation"])


# ============================================================
# step5：象义拆解
# ============================================================

class TestStep5Xiangyi(unittest.TestCase):
    def _session(self, category="career"):
        return create_session(question="事业能否推进", category=category)

    def test_symbol_mappings_use_hexagram_explanation(self):
        plate = {"plates": {"meihua": {"facts": {"original": {"name": "乾为天"}}}}}
        fake = {
            "summary": "刚健中正，自强不息",
            "career_interpretation": "事业上宜主动进取",
        }
        with mock.patch.object(wf, "get_hexagram_explanation", return_value=fake) as lookup:
            result = wf.step5_xiangyi_deduction(self._session(), plate, {})
        lookup.assert_called_once_with("乾为天")

        self.assertEqual(result["step"], 5)
        self.assertEqual(result["hexagram_name"], "乾为天")
        symbols = [item["symbol"] for item in result["symbol_mappings"]]
        self.assertIn("本卦「乾为天」", symbols)
        self.assertIn("「乾为天」之事业象", symbols)
        self.assertTrue(any("在事业事项中" in item["event_mapping"]
                            for item in result["symbol_mappings"]))

    def test_only_summary_mapping_when_category_field_absent(self):
        plate = {"plates": {"meihua": {"facts": {"original": {"name": "乾为天"}}}}}
        with mock.patch.object(wf, "get_hexagram_explanation", return_value={"summary": "摘要"}):
            result = wf.step5_xiangyi_deduction(self._session("finance"), plate, {})
        self.assertEqual(len(result["symbol_mappings"]), 1)

    def test_unknown_hexagram_yields_no_mapping(self):
        plate = {"plates": {"meihua": {"facts": {"original": {"name": "不存在的卦"}}}}}
        with mock.patch.object(wf, "get_hexagram_explanation", return_value=None):
            result = wf.step5_xiangyi_deduction(self._session(), plate, {})
        self.assertEqual(result["hexagram_name"], "不存在的卦")
        self.assertIsNone(result["hexagram_explanation"])
        self.assertEqual(result["symbol_mappings"], [])

    def test_explanation_lookup_failure_is_swallowed(self):
        plate = {"plates": {"meihua": {"facts": {"original": {"name": "乾为天"}}}}}
        with mock.patch.object(wf, "get_hexagram_explanation", side_effect=RuntimeError("db down")):
            result = wf.step5_xiangyi_deduction(self._session(), plate, {})
        self.assertIsNone(result["hexagram_explanation"])

    def test_string_original_hexagram_name_is_accepted(self):
        plate = {"plates": {"zhouyi": {"facts": {"original": "坤为地"}}}}
        with mock.patch.object(wf, "get_hexagram_explanation", return_value=None):
            result = wf.step5_xiangyi_deduction(self._session(), plate, {})
        self.assertEqual(result["hexagram_name"], "坤为地")

    def test_six_spirit_mapping_is_deduplicated_and_skips_unknown(self):
        plate = _plate(lines=[
            _line(1, "官鬼", "木", "寅", spirit="青龙"),
            _line(2, "妻财", "土", "辰", spirit="青龙"),
            _line(3, "父母", "水", "子", spirit="不存在的六神"),
            _line(4, "兄弟", "土", "未", spirit="白虎"),
        ])
        result = wf.step5_xiangyi_deduction(self._session(), plate, {})
        symbols = [item["symbol"] for item in result["symbol_mappings"]]
        self.assertEqual(symbols.count("六神「青龙」"), 1)
        self.assertIn("六神「白虎」", symbols)
        self.assertEqual(len(symbols), 2)
        self.assertTrue(any("第1爻" in item["event_mapping"] for item in result["symbol_mappings"]))

    def test_empty_plate_returns_empty_structure(self):
        result = wf.step5_xiangyi_deduction(self._session(), {}, {})
        self.assertEqual(result["hexagram_name"], "")
        self.assertEqual(result["symbol_mappings"], [])
        self.assertIsNone(result["hexagram_explanation"])


# ============================================================
# step6：吉凶定性
# ============================================================

class TestStep6Synthesis(unittest.TestCase):
    def _judge(self, wangshuai_level="平", tiyong_code="", category="career"):
        session = create_session(question="事业能否推进", category=category)
        return wf.step6_synthesis_judgement(
            session, [], {}, {"primary_yongshen": "官鬼"},
            _wangshuai(wangshuai_level, tiyong_code), {},
        )

    def test_neutral_signals_give_ping(self):
        result = self._judge()
        self.assertEqual(result["step"], 6)
        self.assertEqual(result["fortune_level"], "平")
        self.assertEqual(result["fortune_score"], 0)
        self.assertTrue(any("力量中等" in item for item in result["fortune_basis"]))

    def test_wang_plus_use_generates_body_is_daji(self):
        result = self._judge("旺（得令）", "use_generates_body")
        self.assertEqual(result["fortune_level"], "大吉")
        self.assertEqual(result["fortune_score"], 4)
        self.assertTrue(any("外部条件滋养自身" in item for item in result["fortune_basis"]))
        self.assertTrue(any("用神旺相" in item for item in result["favorable"]))
        self.assertTrue(any("体用关系有利" in item for item in result["favorable"]))

    def test_same_element_scores_xiaoji(self):
        result = self._judge("平", "same_element")
        self.assertEqual(result["fortune_score"], 1)
        self.assertEqual(result["fortune_level"], "小吉")

    def test_body_generates_use_scores_xiaoxiong(self):
        result = self._judge("平", "body_generates_use")
        self.assertEqual(result["fortune_score"], -1)
        self.assertEqual(result["fortune_level"], "小凶")
        self.assertTrue(any("体生用" in item for item in result["obstacles"]))

    def test_use_controls_body_scores_daxiong(self):
        result = self._judge("囚（月令克用）", "use_controls_body")
        self.assertEqual(result["fortune_score"], -4)
        self.assertEqual(result["fortune_level"], "大凶")
        self.assertTrue(any("用克体" in item for item in result["obstacles"]))
        self.assertTrue(any("休囚死" in item for item in result["obstacles"]))

    def test_xiu_alone_is_ping_but_lists_obstacle(self):
        result = self._judge("休（用神生月令）")
        self.assertEqual(result["fortune_level"], "平")
        self.assertTrue(any("休囚死" in item for item in result["obstacles"]))

    def test_body_controls_use_counts_as_favorable(self):
        result = self._judge("相（月令生用）", "body_controls_use")
        self.assertEqual(result["fortune_score"], 3)
        self.assertEqual(result["fortune_level"], "大吉")
        self.assertTrue(any("体克用" in item for item in result["fortune_basis"]))

    def test_unknown_tiyong_code_contributes_nothing(self):
        result = self._judge("平", "unknown_code")
        self.assertEqual(result["fortune_score"], 0)
        self.assertFalse(any("体用" in item and "比和" in item for item in result["fortune_basis"]))

    def test_output_contains_trend_timing_and_rule_ids(self):
        result = self._judge("旺（得令）", "same_element", category="finance")
        self.assertIn("财运", result["current_status"])
        self.assertTrue(result["trend"])
        self.assertTrue(result["timing"])
        self.assertIn("WF-FORTUNE-001", result["rule_ids"])
        self.assertIn("WF-TIMING-001", result["rule_ids"])
        self.assertIn("synthesis", result)
        self.assertIn("advisory", result)
        self.assertIn("imagery", result)
        self.assertIn("yuanhui", result)
        self.assertIn("literature", result)

    def test_empty_wangshuai_data_defaults_to_ping(self):
        session = create_session(question="测试", category="other")
        result = wf.step6_synthesis_judgement(session, [], {}, {}, {}, {})
        self.assertEqual(result["fortune_level"], "平")

    def test_unknown_category_is_normalized(self):
        result = self._judge(category="???")
        self.assertIn("其他谋事", result["current_status"])


# ============================================================
# 趋势与应期
# ============================================================

class TestCalculateTrend(unittest.TestCase):
    def test_tiyong_trend_table_covers_all_relation_codes(self):
        expected = {
            "use_generates_body", "body_generates_use",
            "use_controls_body", "body_controls_use", "same_element",
        }
        self.assertEqual(set(wf.TIYONG_TREND), expected)

    def test_upward_phase_with_favorable_fortune(self):
        text = wf._calculate_trend("career", "旺（得令）", "use_generates_body", "大吉")
        self.assertIn("上升期", text)
        self.assertIn("用生体格局", text)
        self.assertIn("趋势偏吉", text)
        self.assertTrue(text.endswith("。"))
        self.assertNotIn("。。", text)

    def test_flat_phase_for_xiu(self):
        text = wf._calculate_trend("career", "休（用神生月令）", "", "平")
        self.assertIn("平稳期", text)
        self.assertIn("吉凶参半", text)

    def test_downward_phase_for_qiu_and_si(self):
        for level in ("囚（月令克用）", "死（用神克月令）"):
            with self.subTest(level=level):
                text = wf._calculate_trend("career", level, "", "大凶")
                self.assertIn("下降期", text)
                self.assertIn("趋势偏凶", text)

    def test_stalemate_for_neutral_level(self):
        text = wf._calculate_trend("other", "平", "", "小凶")
        self.assertIn("胶着期", text)
        self.assertIn("趋势偏凶", text)

    def test_unknown_tiyong_code_is_ignored(self):
        text = wf._calculate_trend("career", "平", "not_a_code", "平")
        self.assertNotIn("体用", text)


class TestCalculateTiming(unittest.TestCase):
    def _plate(self, month="寅", day="子", branches=("午",)):
        lines = [_line(i + 1, "官鬼", "火", branch, moving=True)
                 for i, branch in enumerate(branches)]
        return _plate(calendar=_calendar(month, day), lines=lines)

    def test_moving_line_gives_value_and_clash_days(self):
        text = wf._calculate_timing(self._plate(), _wangshuai("平"), {}, "平")
        self.assertIn("动爻临「午」", text)
        self.assertIn("逢值（午日）或逢冲（子日）", text)
        self.assertIn("逢合（未日）", text)
        # 日子 0 -> 午 6 -> 6 日逢值；子 0 -> 0 日逢冲
        self.assertIn("距今日约6日逢值，约0日逢冲", text)

    def test_month_branch_maps_to_solar_term(self):
        text = wf._calculate_timing(self._plate(month="寅"), _wangshuai("平"), {}, "平")
        self.assertIn("月令「寅」（立春）", text)

    def test_only_first_two_moving_branches_are_used(self):
        plate = self._plate(branches=("午", "申", "辰"))
        text = wf._calculate_timing(plate, _wangshuai("平"), {}, "平")
        self.assertIn("动爻临「午」", text)
        self.assertIn("动爻临「申」", text)
        self.assertNotIn("动爻临「辰」", text)

    def test_no_moving_line_falls_back_to_day_branch(self):
        plate = _plate(calendar=_calendar("寅", "卯"), lines=[])
        text = wf._calculate_timing(plate, _wangshuai("平"), {}, "平")
        self.assertIn("无明确动爻，以日辰「卯」为基准", text)

    def test_wangshuai_controls_near_or_far_window(self):
        plate = self._plate()
        self.assertIn("应期偏近", wf._calculate_timing(plate, _wangshuai("相（月令生用）"), {}, "平"))
        self.assertIn("应期偏中", wf._calculate_timing(plate, _wangshuai("休（用神生月令）"), {}, "平"))
        self.assertIn("应期偏远", wf._calculate_timing(plate, _wangshuai("死（用神克月令）"), {}, "平"))
        self.assertIn("近中远之间", wf._calculate_timing(plate, _wangshuai("平"), {}, "平"))

    def test_fortune_affects_timing_note(self):
        plate = self._plate()
        self.assertIn("3日内", wf._calculate_timing(plate, _wangshuai("平"), {}, "大凶"))
        self.assertIn("渐进", wf._calculate_timing(plate, _wangshuai("平"), {}, "小吉"))

    def test_always_ends_with_traditional_caveat(self):
        text = wf._calculate_timing(self._plate(), _wangshuai("平"), {}, "平")
        self.assertTrue(text.splitlines()[-1].startswith("注：应期为传统术数推算"))

    def test_empty_plate_does_not_raise(self):
        text = wf._calculate_timing({}, _wangshuai("平"), {}, "平")
        self.assertIn("应期", text)

    def test_string_pillars_are_supported(self):
        plate = {"calendar": {"ganzhi": {"month": "寅", "day": "子"}}, "plates": {}}
        text = wf._calculate_timing(plate, _wangshuai("平"), {}, "平")
        self.assertIn("月令「寅」（立春）", text)
        self.assertIn("以日辰「子」为基准", text)


# ============================================================
# step7：建议与免责
# ============================================================

class TestStep7Advice(unittest.TestCase):
    def _advice(self, fortune, category="career"):
        session = create_session(question="测试", category=category)
        return wf.step7_advice_and_disclaimer(session, {"fortune_level": fortune})

    def test_favorable_fortune_advice(self):
        result = self._advice("大吉")
        self.assertEqual(result["step"], 7)
        self.assertIn("当前卦象有利", result["advice"][0])

    def test_neutral_fortune_advice(self):
        self.assertIn("吉凶参半", self._advice("平")["advice"][0])

    def test_unfavorable_fortune_advice(self):
        for fortune in ("小凶", "大凶"):
            with self.subTest(fortune=fortune):
                self.assertIn("当前卦象有阻", self._advice(fortune)["advice"][0])

    def test_missing_fortune_defaults_to_neutral(self):
        session = create_session(question="测试", category="career")
        result = wf.step7_advice_and_disclaimer(session, {})
        self.assertIn("吉凶参半", result["advice"][0])

    def test_category_recommendations_and_checklist_appended(self):
        advice = self._advice("平", "career")["advice"]
        self.assertTrue(any(item.startswith("理清核心权责与验收指标：") for item in advice))
        self.assertTrue(advice[-1].startswith("核实清单："))
        self.assertGreaterEqual(len(advice), 4)

    def test_unknown_category_uses_other_profile(self):
        advice = self._advice("平", "???")["advice"]
        self.assertTrue(any(item.startswith("定义核心诉求与根本矛盾：") for item in advice))

    def test_disclaimer_is_always_returned(self):
        result = self._advice("大吉", "health")
        self.assertIn("仅作参考", result["disclaimer"])
        self.assertIn("不构成任何决策依据", result["disclaimer"])
        self.assertEqual(result["name"], "趋吉避凶建议")

    def test_unrated_plan_does_not_claim_hexagram_obstruction(self):
        session = create_session(question="测试", category="career")
        result = wf.step7_advice_and_disclaimer(
            session, {"fortune_level": "未评级", "yongshen_framework": "八字命理"}
        )
        self.assertIn("未排卦象体系", result["advice"][0])
        self.assertNotIn("卦象有阻", result["advice"][0])


# ============================================================
# 非卦象体系（八字/紫微/奇门/六壬）用神口径
# ============================================================

class TestNonHexagramYongshen(unittest.TestCase):
    """纯命理/式盘的盘面不该出现「官鬼/父母」这类六亲爻位。"""

    def _qimen_plate(self):
        return {
            "systems": ["qimen"],
            "plates": {"qimen": {"facts": {"dun_type": "阴遁", "ju_number": 3}}},
        }

    def _bazi_plate(self):
        return {
            "systems": ["bazi"],
            "plates": {
                "bazi": {
                    "facts": {
                        "day_master": "癸",
                        "day_master_strength": {
                            "level": "极弱",
                            "favorable_elements": ["火", "木"],
                            "unfavorable_elements": ["水", "金"],
                            "analysis": {"summary": "日主【癸水】极弱。喜用五行：火、木。"},
                        },
                    }
                }
            },
        }

    def test_qimen_uses_day_stem_instead_of_six_relatives(self):
        session = create_session(question="能否升职", category="career")
        result = wf.step3_identify_yongshen(session, self._qimen_plate())
        self.assertEqual(result["primary_yongshen"], "日干（求测人）")
        self.assertNotIn("官鬼", result["logic"])
        self.assertEqual(set(result["yongshen_by_system"]), {"qimen"})
        self.assertEqual(result["yongshen_framework"], "奇门遁甲")

    def test_non_hexagram_party_yongshen_uses_domain_symbols(self):
        """奇门盘面提到「对方」时，多方用神不能写成世爻/应爻。"""
        session = create_session(question="我和对方合作能否成功", category="career")
        result = wf.step3_identify_yongshen(session, self._qimen_plate())
        self.assertEqual(len(result["party_yongshen"]), 2)
        self.assertEqual(result["party_yongshen"][0]["yongshen"], "日干")
        self.assertEqual(result["party_yongshen"][1]["yongshen"], "时干")
        for item in result["party_yongshen"]:
            self.assertNotIn("世爻", item["party"])
            self.assertNotIn("应爻", item["party"])

    def test_bazi_uses_favorable_elements(self):
        session = create_session(question="能否升职", category="career")
        result = wf.step3_identify_yongshen(session, self._bazi_plate())
        self.assertEqual(result["primary_yongshen"], "喜用五行（火、木）")
        self.assertEqual(result["secondary_yongshen"], "忌神五行（水、金）")
        self.assertIn("喜用五行：火、木", result["logic"])
        self.assertEqual(result["yongshen_framework"], "八字命理")

    def test_ziwei_uses_palace_by_category(self):
        session = create_session(question="财运如何", category="finance")
        plate = {"systems": ["ziwei"], "plates": {"ziwei": {"facts": {}}}}
        result = wf.step3_identify_yongshen(session, plate)
        self.assertIn("财帛宫", result["primary_yongshen"])
        self.assertEqual(result["yongshen_framework"], "紫微斗数")

    def test_domain_plan_marks_wangshuai_not_applicable(self):
        session = create_session(question="能否升职", category="career")
        result = wf.step4_wangshuai_analysis(
            session, self._qimen_plate(), {"primary_yongshen": "日干（求测人）"}
        )
        self.assertEqual(result["yongshen_wangshuai"]["level"], "不适用")
        self.assertIsNone(result["tiyong_relation"])
        self.assertEqual(result["rule_ids"], [])
        self.assertTrue(any("不取卦爻六亲" in item for item in result["analysis_chain"]))

    def test_domain_plan_has_no_fortune_rating(self):
        session = create_session(question="能否升职", category="career")
        result = wf.step6_synthesis_judgement(
            session, [], self._bazi_plate(),
            {"primary_yongshen": "喜用五行（火、木）"},
            {"yongshen_wangshuai": {"level": "不适用"}},
            {},
        )
        self.assertEqual(result["fortune_level"], "未评级")
        self.assertIsNone(result["fortune_score"])
        self.assertIsNone(result["timing"])
        self.assertEqual(result["favorable"], [])
        self.assertTrue(any("未排卦象体系" in item for item in result["fortune_basis"]))

    def test_hexagram_plan_still_uses_six_relatives(self):
        session = create_session(question="能否升职", category="career")
        result = wf.step3_identify_yongshen(session, {"systems": ["liuyao"]})
        self.assertEqual(result["primary_yongshen"], "官鬼")
        self.assertEqual(result["yongshen_framework"], "卦象体系")

    def test_reference_library_does_not_invent_a_hexagram(self):
        library = WorkflowEngine._build_reference_library(
            None, {"plates": {}}, {"hexagram_name": "", "symbol_mappings": []},
            {"fortune_level": "未评级", "obstacles": []},
        )
        self.assertNotIn("本卦「」", library["core_symbols"])
        self.assertIn("未排卦象体系", library["core_symbols"])
        self.assertNotIn("待用神得令", library["time_window"])

    def test_plate_text_for_non_hexagram_shows_summary(self):
        """固定文本输出此前对非卦象体系只剩一个空标题，必须补盘面摘要。"""
        text = render_plate_text({"plates": {"qimen": {
            "system_label": "奇门",
            "facts": {
                "dun_type": "阴遁", "ju_number": 3, "yuan_type": "下元",
                "solar_term": "寒露", "zhi_fu_star": "天柱", "zhi_fu_palace": 6,
                "zhi_shi_gate": "惊门", "zhi_shi_palace": 4,
            },
        }}})
        self.assertIn("盘面摘要", text)
        self.assertIn("阴遁3局", text)
        self.assertNotIn("本卦", text)

    def test_plate_text_reads_meihua_body_use(self):
        """梅花体用存在 facts.body_use 下，固定文本必须按真实结构取到体卦/用卦。"""
        text = render_plate_text({"plates": {"meihua": {
            "system_label": "梅花",
            "facts": {
                "body_use": {
                    "body_trigram": {"name": "乾", "element": "金"},
                    "use_trigram": {"name": "兑", "element": "金"},
                },
            },
        }}})
        self.assertIn("体卦：乾（金）", text)
        self.assertIn("用卦：兑（金）", text)

    def test_reality_check_describes_unrated_plan(self):
        check = WorkflowEngine._build_reality_check(
            None, {"plates": {}}, {"primary_yongshen": "喜用五行（火、木）"},
            {"fortune_level": "未评级"},
        )
        self.assertTrue(any("未评级" in item and "不输出吉凶倾向" in item for item in check["items"]))

    def test_fixed_format_has_no_none_or_raw_dict(self):
        class _Session:
            question = "测试事项"
            casting_method = "auto"

        text = render_fixed_format(
            _Session(),
            {"system": "qimen", "casting_method": "auto",
             "casting_source": {"local_datetime": "2026-11-05T10:00"}},
            {"plates": {}},
            {"primary_yongshen": "日干（求测人）"},
            {"yongshen_wangshuai": {"yongshen": "日干（求测人）", "element": "", "level": "不适用"},
             "analysis_chain": []},
            {"hexagram_name": "", "symbol_mappings": []},
            {"fortune_level": "未评级", "fortune_basis": [], "favorable": [], "obstacles": [],
             "trend": "未评级，不作趋势推演", "timing": None},
            {"advice": [], "disclaimer": ""},
            {"core_symbols": ""},
            {"items": []},
            {"options": []},
        )["text"]
        self.assertNotIn("None", text)
        self.assertNotIn("{'", text)
        self.assertIn("qimen · auto · 2026-11-05T10:00", text)
        self.assertIn("====盘面符号事理解读====", text)
        self.assertNotIn("====卦象符号事理解读====", text)
        self.assertIn("盘面事实见步骤 2 盘面摘要", text)


if __name__ == "__main__":
    unittest.main()
