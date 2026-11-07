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

    def test_six_spirits_and_relatives_come_from_line_chart(self):
        """六神/六亲必须从逐爻事实收上来，且按爻位顺序（初→上）排列。

        此前这两个键只存在于引擎 steps 的输出里，盘面事实没有它们，
        前端就只能按「青龙起」的固定序列画——和真实日干起的六神无关。
        """
        lines = [
            {"position": 1, "six_spirit": "玄武", "six_relative": "妻财"},
            {"position": 2, "six_spirit": "青龙", "six_relative": "官鬼"},
            {"position": 3, "six_spirit": "朱雀", "six_relative": "兄弟", "is_moving": True},
            {"position": 4, "six_spirit": "勾陈", "six_relative": "妻财"},
            {"position": 5, "six_spirit": "螣蛇", "six_relative": "子孙"},
            {"position": 6, "six_spirit": "白虎", "six_relative": "兄弟"},
        ]
        result = self._liuyao_result()
        result["result"]["facts"]["line_chart"] = lines
        facts = build_plate_facts([result])["liuyao"]
        self.assertEqual(facts["six_spirits"], ["玄武", "青龙", "朱雀", "勾陈", "螣蛇", "白虎"])
        self.assertEqual(facts["liuqin"], ["妻财", "官鬼", "兄弟", "妻财", "子孙", "兄弟"])

    def test_incomplete_line_chart_leaves_arrays_empty(self):
        """缺爻时不返回半份数组：宁可让前端走回退分支，也不画一份半真半假的盘。"""
        result = self._liuyao_result()
        result["result"]["facts"]["line_chart"] = [
            {"position": 3, "six_spirit": "朱雀", "six_relative": "兄弟"},
        ]
        facts = build_plate_facts([result])["liuyao"]
        self.assertEqual(facts["six_spirits"], [])
        self.assertEqual(facts["liuqin"], [])


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
                        "original": {"name": "蛊", "ordinal": 18, "symbol": "䷑", "upper": "艮", "lower": "巽", "lines": [0, 0, 0, 1, 0, 1]},
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
        # 爻线随卦象一起保留：前端据此直接画爻，不再按上下卦名反查八卦表
        self.assertEqual(facts["original"]["lines"], [0, 0, 0, 1, 0, 1])
        self.assertEqual(facts["changed"]["name"], "蒙")
        self.assertEqual(facts["moving_lines"], [3])
        self.assertEqual(len(facts["six_spirits"]), 6)
        self.assertEqual(compact["plates"]["liuyao"]["system_label"], "六爻纳甲")

    def test_compact_derives_six_spirits_from_line_chart(self):
        """step2 的 facts 与引擎原始 facts 同源，同样没有六神顶层键。

        compact 这一步必须自己从 line_chart 补出来，否则前端仍然只能画默认序列。
        """
        step2 = self._full_step2()
        facts = step2["plates"]["liuyao"]["facts"]
        # 引擎真实输出没有这两个顶层键，这里去掉夹具里的预置值，逼 compact 自行推导
        facts.pop("six_spirits", None)
        facts["line_chart"] = [
            {"position": i + 1, "six_spirit": spirit, "six_relative": relative}
            for i, (spirit, relative) in enumerate([
                ("玄武", "妻财"), ("青龙", "官鬼"), ("朱雀", "兄弟"),
                ("勾陈", "妻财"), ("螣蛇", "子孙"), ("白虎", "兄弟"),
            ])
        ]
        compact = compact_plate_output(step2)
        compact_facts = compact["plates"]["liuyao"]["facts"]
        self.assertEqual(compact_facts["six_spirits"], ["玄武", "青龙", "朱雀", "勾陈", "螣蛇", "白虎"])
        self.assertEqual(compact_facts["liuqin"], ["妻财", "官鬼", "兄弟", "妻财", "子孙", "兄弟"])

    def test_keeps_body_use_relation_for_step4(self):
        """体用生克是 step4 判定体用关系的真源，compact 丢掉它会让评分少一项。"""
        step2 = {
            "step": 2,
            "systems": ["meihua"],
            "plates": {
                "meihua": {
                    "system_label": "梅花易数",
                    "facts": {
                        "original": {"name": "遁", "lines": [1, 1, 1, 0, 0, 1]},
                        "moving_lines": [1],
                        "body_use": {
                            "body_trigram": {"name": "乾", "element": "金"},
                            "use_trigram": {"name": "艮", "element": "土"},
                        },
                        "body_use_relation": {
                            "original": {"code": "use_generates_body", "label": "用生体"},
                            "changed": {"code": "same_element", "label": "体用比和"},
                        },
                    },
                }
            },
        }
        facts = compact_plate_output(step2)["plates"]["meihua"]["facts"]
        self.assertEqual(facts["body_use"]["body_trigram"]["name"], "乾")
        self.assertEqual(facts["body_use_relation"]["original"]["code"], "use_generates_body")

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

    def test_domain_summary_covers_non_hexagram_systems(self):
        """八字/紫微/奇门/六壬的盘面不在卦象字段里，compact 必须另给一份摘要。"""
        bazi_facts = {
            "day_master": "癸",
            "day_master_element": "水",
            "pillars": {
                "year": {"ganzhi": "丙午"}, "month": {"ganzhi": "戊戌"},
                "day": {"ganzhi": "癸未"}, "hour": {"ganzhi": "丁巳"},
            },
            "day_master_strength": {"level": "偏弱"},
            "luck_pillars": [{"ganzhi": "甲午"}, {"ganzhi": "乙未"}],
        }
        qimen_facts = {
            "dun_type": "阴遁", "ju_number": 6, "yuan_type": "上元", "solar_term": "立冬",
            "zhi_fu_star": "天心", "zhi_fu_palace": 6, "zhi_shi_gate": "开门", "zhi_shi_palace": 8,
            "favorable_directions": [{"direction": "西北", "gate": "开门", "palace_name": "乾六宫"}],
        }
        ziwei_facts = {
            "bureau": {"name": "水二局"},
            "ming_palace": {"palace_stem_branch": "癸巳"},
            "shen_palace": {"palace_stem_branch": "辛卯"},
            "si_hua": {"化禄": "太阳"},
            "palaces_by_order": [{"name": "命宫"}, {"name": "兄弟宫"}],
        }
        liuren_facts = {
            "day_pillar": "癸未",
            "actual_time_branch": "巳",
            "month_general": {"name": "登明"},
            "three_transmissions": {"transmissions": ["寅", "午", "戌"], "lesson_type": "涉害课"},
        }
        step2 = {
            "systems": ["bazi", "ziwei", "qimen", "daliuren"],
            "plates": {
                "bazi": {"system_label": "八字命理", "facts": bazi_facts},
                "ziwei": {"system_label": "紫微斗数", "facts": ziwei_facts},
                "qimen": {"system_label": "奇门遁甲", "facts": qimen_facts},
                "daliuren": {"system_label": "大六壬", "facts": liuren_facts},
            },
        }
        compact = compact_plate_output(step2)

        bazi = compact["plates"]["bazi"]["summary"]
        self.assertEqual(bazi["日主"], "癸（水）")
        self.assertEqual(bazi["四柱"], "丙午 戊戌 癸未 丁巳")
        self.assertEqual(bazi["日主旺衰"], "偏弱")
        self.assertEqual(bazi["大运"], "2 步")

        ziwei = compact["plates"]["ziwei"]["summary"]
        self.assertEqual(ziwei["五行局"], "水二局")
        self.assertEqual(ziwei["命宫"], "癸巳")
        self.assertEqual(ziwei["身宫"], "辛卯")
        self.assertEqual(ziwei["四化"], "化禄 太阳")
        self.assertEqual(ziwei["宫位"], "2 宫")

        qimen = compact["plates"]["qimen"]["summary"]
        self.assertEqual(qimen["局象"], "阴遁6局·上元")
        self.assertEqual(qimen["值符"], "天心 落 6 宫")
        self.assertEqual(qimen["首选吉方"], "西北方 · 开门 · 乾六宫")

        liuren = compact["plates"]["daliuren"]["summary"]
        self.assertEqual(liuren["三传"], "寅 → 午 → 戌")
        self.assertEqual(liuren["课体"], "涉害课")

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
