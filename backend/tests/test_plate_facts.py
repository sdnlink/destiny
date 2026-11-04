"""盘面事实归一层（workflow/plate_facts.py）的单元测试。

这层的价值在于「交互层只读一处」：快照里 facts 的形状各不相同，
归一后才有稳定的卦名、动爻、体用可读。归一出错时下游全是静默空值，
所以这里直接钉住关键语义。
"""

import unittest

from app.workflow.plate_facts import (
    _changed_line_desc,
    _moving_line_desc,
    build_plate_facts,
    build_plate_view,
    compact_plate_output,
)


class MovingLineTitleTests(unittest.TestCase):
    def test_first_line_uses_chu_prefix(self):
        self.assertEqual(_moving_line_desc({"lines": [1, 0, 0, 1, 0, 1]}, 1), "初九（第1爻）")
        self.assertEqual(_moving_line_desc({"lines": [0, 0, 0, 1, 0, 1]}, 1), "初六（第1爻）")

    def test_middle_lines_put_polarity_first(self):
        # 传统爻题是「九二/六三」，不是「二九/三六」
        self.assertEqual(_moving_line_desc({"lines": [1, 0, 1, 0, 1, 0]}, 2), "六二（第2爻）")
        self.assertEqual(_moving_line_desc({"lines": [0, 0, 1, 0, 1, 0]}, 3), "九三（第3爻）")

    def test_top_line_uses_shang_prefix(self):
        self.assertEqual(_moving_line_desc({"lines": [0, 0, 0, 0, 0, 1]}, 6), "上九（第6爻）")

    def test_missing_moving_line_returns_empty(self):
        self.assertEqual(_moving_line_desc({"lines": [1, 0, 1, 0, 1, 0]}, None), "")


class ChangedLineTests(unittest.TestCase):
    def test_changed_line_describes_polarity_flip(self):
        original = {"lines": [0, 0, 0, 1, 0, 1]}
        changed = {"lines": [0, 1, 0, 1, 0, 1]}
        self.assertEqual(_changed_line_desc(original, changed, 2), "第2爻由阴变阳")

    def test_changed_line_without_changed_hexagram(self):
        self.assertEqual(_changed_line_desc({"lines": [1, 0, 0]}, None, 1), "第1爻变")


class BuildPlateFactsTests(unittest.TestCase):
    def _liuyao_result(self):
        return {
            "module": "liuyao",
            "result": {
                "facts": {
                    "original": {"lines": [0, 0, 0, 1, 0, 1], "name": "蛊", "ordinal": 18, "symbol": "䷑"},
                    "changed": {"lines": [0, 0, 1, 1, 0, 1], "name": "蒙", "ordinal": 4, "symbol": "䷃"},
                    "mutual": {"name": "归妹", "ordinal": 54, "symbol": "䷵"},
                    "moving_lines": [3],
                    "line_chart": [
                        {"position": 3, "is_moving": True, "najia_branch": "酉", "element": "金"},
                    ],
                    "month_branch": "戌",
                    "day_pillar": "壬午",
                }
            },
        }

    def test_moving_line_backfilled_and_titled(self):
        facts = build_plate_facts([self._liuyao_result()])
        liuyao = facts["liuyao"]
        self.assertEqual(liuyao["moving_line"], 3)
        self.assertEqual(liuyao["moving_line_text"], "六三（第3爻）")
        self.assertEqual(liuyao["moving_branches"], ["酉"])

    def test_bian_yao_is_the_flipped_line_not_the_hexagram_name(self):
        facts = build_plate_facts([self._liuyao_result()])

        class _Snapshot:
            raw_plate = {"plate_facts": facts}

        view = build_plate_view(_Snapshot())
        self.assertEqual(view["ben_gua"], "蛊")
        self.assertEqual(view["bian_gua"], "蒙")
        self.assertEqual(view["bian_yao"], "第3爻由阴变阳")

    def test_results_without_facts_are_skipped(self):
        facts = build_plate_facts([{"module": "calendar", "result": {"solar": {}}}])
        self.assertEqual(facts, {})


class CompactPlateOutputTests(unittest.TestCase):
    """step2 只保存展示字段，完整盘面留在快照 module_results。"""

    def _full_step2(self):
        return {
            "step": 2,
            "name": "完整排盘输出",
            "systems": ["meihua", "liuyao"],
            "calendar": {
                "pillars": {"year": "丙午", "month": "戊戌", "day": "壬午", "time": "乙巳"},
                "ganzhi": {
                    "year": {"text": "丙午", "stem": "丙", "branch": "午", "stem_element": "火"},
                    "hour": {"stem": "乙", "branch": "巳"},
                },
                "solar_term": "寒露",
                "lunar": {"year": 2026, "month_name": "九月", "day_name": "廿四"},
                "almanac": {"yi": ["祭祀"], "ji": ["动土"]},
                "calculation_trace": ["step-a", "step-b"],
            },
            "plates": {
                "liuyao": {
                    "system_label": "六爻纳甲",
                    "facts": {
                        "original": {"name": "蛊", "ordinal": 18, "symbol": "䷑", "upper": "艮", "lower": "巽"},
                        "changed": {"name": "蒙", "ordinal": 4, "symbol": "䷃"},
                        "mutual": {"name": "归妹", "ordinal": 54, "symbol": "䷵"},
                        "moving_lines": [3],
                        "six_spirits": ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"],
                        "line_chart": [{"position": 1, "najia_branch": "丑", "element": "土"}],
                        "hidden_flying_spirits": [{"position": 2, "relative": "妻财"}],
                    },
                    "calculation_trace": ["装卦", "纳甲", "定世应"],
                    "steps": [{"name": "纳甲", "detail": "x" * 100}],
                    "warnings": [],
                    "engine_version": "1.0",
                    "rule_version": "1.0",
                }
            },
        }

    def test_drops_duplicated_plate_payload(self):
        compact = compact_plate_output(self._full_step2())
        plate = compact["plates"]["liuyao"]
        self.assertNotIn("calculation_trace", plate)
        self.assertNotIn("steps", plate)
        self.assertNotIn("line_chart", plate["facts"])
        self.assertNotIn("hidden_flying_spirits", plate["facts"])

    def test_keeps_fields_the_frontend_renders(self):
        compact = compact_plate_output(self._full_step2())
        facts = compact["plates"]["liuyao"]["facts"]
        self.assertEqual(facts["original"]["name"], "蛊")
        self.assertEqual(facts["original"]["upper"], "艮")
        self.assertEqual(facts["original"]["lower"], "巽")
        self.assertEqual(facts["changed"]["name"], "蒙")
        self.assertEqual(facts["moving_lines"], [3])
        self.assertEqual(len(facts["six_spirits"]), 6)
        self.assertEqual(compact["plates"]["liuyao"]["system_label"], "六爻纳甲")

    def test_calendar_becomes_renderable_strings(self):
        compact = compact_plate_output(self._full_step2())
        calendar = compact["calendar"]
        self.assertEqual(calendar["pillars"]["year"], "丙午")
        self.assertEqual(calendar["ganzhi"]["year"], "丙午")
        self.assertEqual(calendar["ganzhi"]["hour"], "乙巳", "缺 text 时应拼 stem+branch")
        self.assertEqual(calendar["solar_term"], "寒露")
        self.assertNotIn("almanac", calendar)
        self.assertNotIn("calculation_trace", calendar)

    def test_solar_term_object_is_reduced_to_current_name(self):
        """后端节气是 {previous/current/next} 结构，直接插值会渲染成 [object Object]。"""
        step2 = {
            "calendar": {
                "solar_term": {
                    "previous": {"name": "秋分"},
                    "current": {"name": "寒露", "datetime": "2026-10-08 09:00:00"},
                    "next": {"name": "霜降"},
                }
            },
            "plates": {},
        }
        compact = compact_plate_output(step2)
        self.assertEqual(compact["calendar"]["solar_term"], "寒露")
        self.assertEqual(compact["calendar"]["solar_term_note"], "当前节气")
        self.assertIsInstance(compact["calendar"]["solar_term"], str)

    def test_solar_term_falls_back_to_next_when_not_on_a_term_day(self):
        """非节气当天 current 为 null，应退回下一节气并标注关系。"""
        step2 = {
            "calendar": {
                "solar_term": {
                    "previous": {"name": "霜降"},
                    "current": None,
                    "next": {"name": "立冬", "datetime": "2026-11-07 17:52:05"},
                }
            },
            "plates": {},
        }
        compact = compact_plate_output(step2)
        self.assertEqual(compact["calendar"]["solar_term"], "立冬")
        self.assertEqual(compact["calendar"]["solar_term_note"], "下一节气")

    def test_compact_is_much_smaller_than_input(self):
        import json

        full = self._full_step2()
        compact = compact_plate_output(full)
        self.assertLess(
            len(json.dumps(compact, ensure_ascii=False)),
            len(json.dumps(full, ensure_ascii=False)),
        )

    def test_trigram_dict_names_are_flattened_for_frontend(self):
        """引擎把上下卦存成字典，展示层需要字符串卦名才能画出爻线。"""
        facts = {
            "original": {
                "name": "蛊",
                "ordinal": 18,
                "upper_trigram": {"number": 7, "name": "艮", "element": "土"},
                "lower_trigram": {"number": 5, "name": "巽", "element": "木"},
            }
        }
        step2 = {
            "systems": ["liuyao"],
            "plates": {"liuyao": {"system_label": "六爻", "facts": facts}},
        }
        compact = compact_plate_output(step2)
        original = compact["plates"]["liuyao"]["facts"]["original"]
        self.assertEqual(original["upper"], "艮")
        self.assertEqual(original["lower"], "巽")


if __name__ == "__main__":
    unittest.main()
