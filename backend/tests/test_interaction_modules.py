"""测试：交互模块 A-G（backend/app/interaction）。

各模块针对性强覆盖：
- info_completion（模块A）：缺失检测、3 项上限、ready 分支、答案回填
- reality_check（模块B）：三种回复、模糊匹配、未冻结快照异常、快照不变
- multi_party（模块E）：人物识别、默认映射、聚焦人物、无盘面报错
- multi_choice（模块F）：分支推演、吉凶 → 风险等级、方案不足、排序建议
- review（模块G）：吉凶应验对比、因素/应期归因、分析维度、复盘状态
- deep_question（D②）：符号识别、关联盘面数据、解读文本分支
- angle_shift（D③）：预设/关键词匹配、未知角度兜底、重解读文本分支

铁律共用断言：所有交互都不修改已冻结的 snapshot。
"""

import importlib
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.interaction import (
    analyze_branches,
    analyze_multi_party,
    angle_shift,
    apply_completion_answers,
    deep_question,
    detect_missing,
    detect_parties,
    generate_completion_prompt,
    process_reality_response,
    review_outcome,
)
# 包 __init__ 把同名函数导出了，取模块要走 import_module，避免拿到函数对象
angle_shift_module = importlib.import_module("app.interaction.angle_shift")
deep_question_module = importlib.import_module("app.interaction.deep_question")
multi_choice_module = importlib.import_module("app.interaction.multi_choice")
reality_check_module = importlib.import_module("app.interaction.reality_check")
review_module = importlib.import_module("app.interaction.review")
from app.session import create_session, freeze_snapshot
from app.session.models import DivinationSnapshot


# ============================================================
# 测试辅助
# ============================================================

RAW_PLATE = {
    "ben_gua": "乾为天",
    "bian_gua": "坤为地",
    "hu_gua": "泽天夬",
    "ti_gua": "乾",
    "yong_gua": "坤",
    "moving_line": 3,
    "yao_ci": "九三（第3爻）",
    "bian_yao": "第3爻由阳变阴",
}


def _cast_session(question="事业能否推进", category="career", workflow=None,
                  raw_plate=None):
    session = create_session(question=question, category=category, casting_method="time",
                            casting_source={"local_datetime": "2026-08-26T10:00:00"})
    session = freeze_snapshot(
        session,
        dict(RAW_PLATE if raw_plate is None else raw_plate),
        [],
        {"question": question},
    )
    if workflow is not None:
        session.workflow_result = workflow
    return session


def _workflow(fortune="大吉", trend="趋势向好", timing="7日内",
              favorable=None, obstacles=None, primary="官鬼", level="旺（得令）"):
    return {
        "step3": {"primary_yongshen": primary, "secondary_yongshen": "父母",
                  "logic": "事业看官鬼"},
        "step4": {"yongshen_wangshuai": {"level": level},
                  "analysis_chain": ["用神得令而旺"]},
        "step6": {
            "fortune_level": fortune,
            "fortune_basis": ["用神旺，力量充足", "体用比和"],
            "trend": trend,
            "timing": timing,
            "favorable": ["用神旺相，具备推进条件"] if favorable is None else favorable,
            "obstacles": ["推进阻力较大"] if obstacles is None else obstacles,
        },
    }


# ============================================================
# 模块A：信息补全
# ============================================================

class TestInfoCompletion(unittest.TestCase):
    def test_new_session_missing_is_capped_at_three(self):
        session = create_session(question="测试")
        missing = detect_missing(session)
        self.assertEqual(len(missing), 3)
        self.assertEqual(missing, ["casting_method", "gender_age", "current_stage"])

    def test_complete_session_reports_nothing_missing(self):
        session = create_session(
            question="测试",
            category="career",
            system="meihua",
            casting_method="time",
            casting_source={"cast_nonce": "nonce-1",
                            "local_datetime": "2026-08-26T10:00:00"},
            user_profile={"gender": "男", "current_stage": "进行中"},
        )
        self.assertEqual(detect_missing(session), [])

    def test_relationship_category_requires_gender(self):
        session = create_session(
            question="感情走向",
            category="relationship",
            system="meihua",
            casting_method="time",
            casting_source={"cast_nonce": "nonce-1"},
            user_profile={"current_stage": "进行中"},
        )
        self.assertIn("gender_age", detect_missing(session))

    def test_gender_not_required_for_non_personal_category(self):
        session = create_session(
            question="项目能否中标",
            category="career",
            system="meihua",
            casting_method="time",
            casting_source={"cast_nonce": "nonce-1"},
            user_profile={"current_stage": "进行中"},
        )
        self.assertEqual(detect_missing(session), [])

    def test_bazi_system_requires_gender(self):
        session = create_session(
            question="事业运",
            category="career",
            system="bazi",
            casting_method="time",
            casting_source={"cast_nonce": "nonce-1"},
            user_profile={"current_stage": "进行中"},
        )
        self.assertIn("gender_age", detect_missing(session))

    def test_auto_system_is_reported_missing_last(self):
        session = create_session(
            question="测试",
            category="career",
            system="auto",
            casting_method="time",
            casting_source={"cast_nonce": "nonce-1"},
            user_profile={"gender": "女", "current_stage": "进行中"},
        )
        self.assertEqual(detect_missing(session), ["system"])

    def test_prompt_is_ready_when_nothing_missing(self):
        session = create_session(
            question="测试",
            category="career",
            system="meihua",
            casting_method="time",
            casting_source={"cast_nonce": "nonce-1"},
            user_profile={"gender": "男", "current_stage": "进行中"},
        )
        prompt = generate_completion_prompt(session)
        self.assertTrue(prompt["ready"])
        self.assertEqual(prompt["questions"], [])
        self.assertIn("信息已充足", prompt["instruction"])
        self.assertNotIn("skip_keyword", prompt)

    def test_prompt_maps_missing_fields_to_templates(self):
        session = create_session(question="测试")
        prompt = generate_completion_prompt(session)
        self.assertFalse(prompt["ready"])
        self.assertEqual(
            [item["field"] for item in prompt["questions"]],
            ["casting_method", "user_profile.gender_age", "user_profile.current_stage"],
        )
        self.assertEqual(prompt["skip_keyword"], "直接起盘，不用多问")
        for item in prompt["questions"]:
            self.assertTrue(item["question"])

    def test_apply_completion_answers_updates_session(self):
        session = create_session(question="测试")
        returned = apply_completion_answers(session, {
            "casting_method": "numbers",
            "system": "liuyao",
            "user_profile.gender_age": "男 30 岁",
            "user_profile.current_stage": "进行中",
        })
        self.assertIs(returned, session)
        self.assertEqual(session.casting_method, "numbers")
        self.assertEqual(session.system, "liuyao")
        self.assertEqual(session.user_profile["gender_age"], "男 30 岁")
        self.assertEqual(session.user_profile["current_stage"], "进行中")

    def test_apply_completion_answers_ignores_unknown_fields(self):
        session = create_session(question="测试")
        apply_completion_answers(session, {"unknown_field": "x", "casting_method": "manual"})
        self.assertFalse(hasattr(session, "unknown_field"))
        self.assertEqual(session.casting_method, "manual")

    def test_apply_completion_answers_with_empty_dict(self):
        session = create_session(question="测试")
        before = (session.casting_method, session.system, dict(session.user_profile))
        apply_completion_answers(session, {})
        self.assertEqual((session.casting_method, session.system, session.user_profile), before)

    def test_answers_resolve_missing_fields(self):
        session = create_session(question="测试")
        apply_completion_answers(session, {
            "casting_method": "time",
            "system": "meihua",
            "user_profile.gender_age": "女",
            "user_profile.current_stage": "已出结果",
        })
        self.assertEqual(detect_missing(session), [])


# ============================================================
# 模块B：现实校验
# ============================================================

class TestRealityCheck(unittest.TestCase):
    def test_exact_fit_enters_extended(self):
        session = _cast_session()
        result = process_reality_response(session, "符合")
        self.assertEqual(result["response_type"], "符合")
        self.assertEqual(result["action"], "enter_extended")
        self.assertNotIn("interpretation_shift", result)
        self.assertNotIn("options", result)
        self.assertTrue(result["snapshot_unchanged"])

    def test_partial_fit_offers_two_angles(self):
        session = _cast_session()
        result = process_reality_response(session, "部分符合", details="事业方向符合，时间不符")
        shift = result["interpretation_shift"]
        self.assertEqual(shift["shift_type"], "reality_mismatch")
        self.assertEqual(shift["details"], "事业方向符合，时间不符")
        self.assertEqual(len(shift["suggested_angles"]), 2)
        self.assertIn("snapshot", shift["note"])

    def test_mismatch_offers_two_options_and_four_angles(self):
        session = _cast_session()
        result = process_reality_response(session, "不符合")
        self.assertEqual(result["action"], "offer_choice")
        self.assertEqual(len(result["options"]), 2)
        self.assertIn("更换起盘方式", result["options"][0])
        self.assertEqual(len(result["interpretation_shift"]["suggested_angles"]), 4)

    def test_details_default_to_empty_string(self):
        session = _cast_session()
        result = process_reality_response(session, "不符合")
        self.assertEqual(result["interpretation_shift"]["details"], "")

    def test_surrounding_whitespace_is_stripped(self):
        session = _cast_session()
        result = process_reality_response(session, "  符合 \n")
        self.assertEqual(result["response_type"], "符合")

    def test_fuzzy_match_accepts_embedded_keyword(self):
        session = _cast_session()
        result = process_reality_response(session, "我觉得基本符合")
        self.assertEqual(result["response_type"], "符合")

    def test_unrecognized_answer_asks_retry(self):
        session = _cast_session()
        result = process_reality_response(session, "不知道")
        self.assertEqual(result["response_type"], "unknown")
        self.assertEqual(result["action"], "retry")
        self.assertNotIn("interpretation_shift", result)
        self.assertTrue(result["snapshot_unchanged"])

    def test_negated_answer_is_not_read_as_fit(self):
        """「不太符合」属于否定语义，不应被模糊匹配判成「符合」。

        已改为长关键词优先 + 否定表达归一，此处钉住语义方向。
        """
        session = _cast_session()
        result = process_reality_response(session, "不太符合")
        self.assertNotEqual(result["response_type"], "符合")

    def test_negated_variants_all_map_to_mismatch(self):
        session = _cast_session()
        for answer in ("不太符合", "并不完全符合", "不是完全符合", "未符合", "没有符合"):
            with self.subTest(answer=answer):
                result = process_reality_response(session, answer)
                self.assertEqual(result["response_type"], "不符合")
                self.assertEqual(result["action"], "offer_choice")

    def test_negation_like_char_away_from_keyword_is_ignored(self):
        """「未来符合预期」里的「未」不紧邻关键词，不应被当成否定。"""
        session = _cast_session()
        self.assertEqual(process_reality_response(session, "未来符合预期")["response_type"], "符合")
        self.assertEqual(process_reality_response(session, "未确定但基本符合")["response_type"], "符合")

    def test_longer_positive_answer_keeps_partial_type(self):
        session = _cast_session()
        self.assertEqual(process_reality_response(session, "部分符合吧")["response_type"], "部分符合")

    def test_missing_snapshot_raises(self):
        session = create_session(question="未排盘")
        with self.assertRaises(RuntimeError) as ctx:
            process_reality_response(session, "符合")
        self.assertIn("盘面尚未生成", str(ctx.exception))

    def test_unfrozen_snapshot_raises(self):
        session = create_session(question="状态异常")
        session.snapshot = DivinationSnapshot(snapshot_id="snap_broken", frozen=False)
        with self.assertRaises(RuntimeError) as ctx:
            process_reality_response(session, "符合")
        self.assertIn("未冻结", str(ctx.exception))

    def test_snapshot_is_byte_identical_after_response(self):
        session = _cast_session()
        before = (session.snapshot.snapshot_id, session.snapshot.input_hash,
                  dict(session.snapshot.raw_plate))
        process_reality_response(session, "不符合", details="完全反了")
        after = (session.snapshot.snapshot_id, session.snapshot.input_hash,
                 dict(session.snapshot.raw_plate))
        self.assertEqual(before, after)
        self.assertTrue(session.snapshot.frozen)

    def test_response_table_covers_three_answers(self):
        self.assertEqual(set(reality_check_module.REALITY_RESPONSES),
                         {"符合", "部分符合", "不符合"})


# ============================================================
# 模块E：多方人物取象
# ============================================================

class TestMultiParty(unittest.TestCase):
    def test_always_includes_the_asker(self):
        self.assertEqual(detect_parties(""), ["求测人"])
        self.assertEqual(detect_parties("今天天气如何"), ["求测人"])

    def test_generic_words_containing_pronoun_char_are_not_parties(self):
        """「其他/其它」是泛指词，其中的单字「他」不能触发「对方」。"""
        self.assertEqual(detect_parties("其他事情怎么办"), ["求测人"])
        self.assertEqual(detect_parties("其它方案可行吗"), ["求测人"])

    def test_pronoun_still_detected_when_really_used(self):
        self.assertIn("对方", detect_parties("他说要再等等"))
        self.assertIn("对方", detect_parties("她还没表态"))
        self.assertIn("对方", detect_parties("他们内部已定"))

    def test_leader_and_colleague_are_detected(self):
        parties = detect_parties("领导安排的同事协作项目")
        self.assertIn("领导/上级", parties)
        self.assertIn("同事/同级", parties)
        self.assertEqual(parties[0], "求测人")

    def test_client_role_and_relationship_fallback(self):
        parties = detect_parties("和客户谈判合作能否达成")
        self.assertIn("客户/合作方", parties)
        self.assertIn("对方", parties)

    def test_romance_question_adds_counterparty(self):
        self.assertIn("对方", detect_parties("这段感情还有救吗"))

    def test_roles_are_not_duplicated(self):
        parties = detect_parties("对方和我都在等对方表态")
        self.assertEqual(parties.count("对方"), 1)

    def test_analysis_covers_requested_party(self):
        session = _cast_session()
        result = analyze_multi_party(session, parties=["求测人", "领导/上级"])
        self.assertEqual([item["party"] for item in result["parties"]],
                         ["求测人", "领导/上级"])
        self.assertEqual(result["parties"][1]["yongshen"], "官鬼爻/父母爻")
        self.assertTrue(result["snapshot_unchanged"])

    def test_auto_detect_from_session_question(self):
        session = _cast_session(question="我和对方合作能否成功")
        result = analyze_multi_party(session)
        parties = [item["party"] for item in result["parties"]]
        self.assertIn("求测人", parties)
        self.assertIn("对方", parties)

    def test_unknown_party_uses_generic_mapping(self):
        session = _cast_session()
        result = analyze_multi_party(session, parties=["路人"])
        item = result["parties"][0]
        self.assertEqual(item["yongshen"], "应爻")
        self.assertEqual(item["nature"], "相关方")
        self.assertIn("路人", item["position"])
        self.assertIn("路人", item["mindset"])
        self.assertIn("路人", item["demands"])

    def test_asker_demands_mention_category(self):
        session = _cast_session(category="finance")
        result = analyze_multi_party(session, parties=["求测人"])
        self.assertIn("finance", result["parties"][0]["demands"])

    def test_focus_party_adds_deep_analysis(self):
        session = _cast_session()
        result = analyze_multi_party(session, parties=["求测人", "对方"],
                                     focus_party="对方")
        self.assertIn("focus_party", result)
        self.assertEqual(result["focus_party"]["party"], "对方")
        self.assertIn("用神定位", result["focus_party"]["deep_analysis"])

    def test_focus_party_not_in_list_is_omitted(self):
        session = _cast_session()
        result = analyze_multi_party(session, parties=["求测人"], focus_party="竞争者")
        self.assertNotIn("focus_party", result)

    def test_empty_party_list_returns_empty_analysis(self):
        session = _cast_session()
        result = analyze_multi_party(session, parties=[])
        self.assertEqual(result["parties"], [])

    def test_missing_snapshot_returns_error(self):
        session = create_session(question="未排盘")
        self.assertIn("error", analyze_multi_party(session))
        self.assertIn("error", analyze_multi_party(session, parties=["求测人"]))


# ============================================================
# 模块F：多抉择分支
# ============================================================

class TestMultiChoice(unittest.TestCase):
    def test_favorable_fortune_yields_low_risk(self):
        session = _cast_session(workflow=_workflow("大吉"))
        result = analyze_branches(session, ["方案A", "方案B"])
        self.assertEqual(len(result["choices"]), 2)
        for item in result["choices"]:
            self.assertEqual(item["risk_level"], "低")
            self.assertEqual(len(item["pros"]), 2)
            self.assertEqual(len(item["cons"]), 2)
        self.assertIn("方案A", result["recommendation"])
        self.assertIn("风险较低", result["recommendation"])
        self.assertTrue(result["snapshot_unchanged"])
        self.assertIn("原盘", result["note"])

    def test_neutral_fortune_yields_medium_risk(self):
        session = _cast_session(workflow=_workflow("平"))
        result = analyze_branches(session, ["方案A", "方案B"])
        self.assertTrue(all(item["risk_level"] == "中" for item in result["choices"]))
        self.assertIn("小范围试点", result["recommendation"])

    def test_unfavorable_fortune_yields_high_risk(self):
        for fortune in ("小凶", "大凶"):
            with self.subTest(fortune=fortune):
                session = _cast_session(workflow=_workflow(fortune))
                result = analyze_branches(session, ["方案A", "方案B"])
                self.assertTrue(all(item["risk_level"] == "高" for item in result["choices"]))
                self.assertIn("暂缓重大决策", result["recommendation"])

    def test_angles_cycle_when_more_than_four_choices(self):
        session = _cast_session(workflow=_workflow("大吉"))
        result = analyze_branches(session, ["A", "B", "C", "D", "E"])
        self.assertEqual(
            [item["analysis_angle"] for item in result["choices"]],
            ["世爻视角", "应爻视角", "动爻视角", "用神视角", "世爻视角"],
        )

    def test_defaults_without_workflow_result(self):
        session = _cast_session()
        result = analyze_branches(session, ["A", "B"])
        self.assertEqual(result["choices"][0]["risk_level"], "中")

    def test_single_choice_is_rejected(self):
        session = _cast_session(workflow=_workflow())
        self.assertIn("error", analyze_branches(session, ["只有一个"]))

    def test_empty_choices_are_rejected(self):
        session = _cast_session(workflow=_workflow())
        self.assertIn("error", analyze_branches(session, []))

    def test_missing_snapshot_returns_error(self):
        session = create_session(question="未排盘")
        self.assertIn("error", analyze_branches(session, ["A", "B"]))

    def test_recommendation_sorts_by_risk_level(self):
        analyses = [
            {"choice": "高风险方案", "risk_level": "高"},
            {"choice": "稳妥方案", "risk_level": "低"},
            {"choice": "折中方案", "risk_level": "中"},
        ]
        text = multi_choice_module._generate_recommendation(analyses, "平")
        self.assertIn("稳妥方案", text)
        self.assertNotIn("高风险方案", text)


# ============================================================
# 模块G：事后复盘
# ============================================================

class TestReview(unittest.TestCase):
    def test_favorable_outcome_matches_favorable_prediction(self):
        session = _cast_session(workflow=_workflow("大吉"))
        result = review_outcome(session, "项目顺利通过，成功签约")
        self.assertEqual(result["actual_outcome"], "项目顺利通过，成功签约")
        self.assertTrue(result["verified"])
        self.assertEqual(result["unverified"], [])
        self.assertIn("方向一致", result["verified"][0])
        self.assertTrue(result["snapshot_unchanged"])
        self.assertEqual(session.status, "reviewed")

    def test_unfavorable_outcome_contradicts_favorable_prediction(self):
        session = _cast_session(workflow=_workflow("大吉"))
        result = review_outcome(session, "项目最终失败，合作终止")
        self.assertEqual(result["verified"], [])
        self.assertEqual(len(result["unverified"]), 1)
        self.assertIn("方向相反", result["unverified"][0])

    def test_prediction_defaults_without_workflow_result(self):
        session = _cast_session()
        result = review_outcome(session, "结果一般")
        self.assertEqual(result["predicted_outcome"]["fortune_level"], "平")
        self.assertEqual(result["predicted_outcome"]["trend"], "")
        self.assertEqual(result["predicted_outcome"]["timing"], "")

    def test_key_factors_without_match_are_listed_as_unforeseen(self):
        session = _cast_session(workflow=_workflow("小吉"))
        result = review_outcome(
            session, "顺利完成",
            {"key_factors": ["临时政策变化", "对方临时换人"]},
        )
        self.assertEqual(len(result["unverified"]), 2)
        self.assertTrue(all("未预见因素" in item for item in result["unverified"]))

    def test_key_factor_matching_uses_containment_both_ways(self):
        """用户给的关键因素「用神旺相」应命中预测里的有利因素条目。

        已改为双向包含匹配，避免预测长句永远匹配不上用户短语。
        """
        session = _cast_session(workflow=_workflow("大吉"))
        result = review_outcome(
            session, "顺利完成",
            {"key_factors": ["用神旺相"]},
        )
        self.assertTrue(any("有利因素应验" in item for item in result["verified"]))

    def test_key_factor_longer_than_prediction_still_matches(self):
        """反方向也要成立：用户因素比预测句更长时，预测句应作为子串命中。"""
        session = _cast_session(workflow=_workflow("大吉"))
        result = review_outcome(
            session, "顺利完成",
            {"key_factors": ["实际推进阻力较大，比预期严重得多"]},
        )
        self.assertTrue(any("阻碍因素应验" in item for item in result["verified"]))

    def test_actual_timing_is_recorded(self):
        session = _cast_session(workflow=_workflow("大吉", timing="7日内"))
        result = review_outcome(session, "顺利达成", {"timing": "第 5 天"})
        self.assertTrue(any("应期参考" in item for item in result["verified"]))
        self.assertTrue(any("第 5 天" in item for item in result["verified"]))

    def test_timing_skipped_when_prediction_has_none(self):
        session = _cast_session(workflow=_workflow("大吉", timing=""))
        result = review_outcome(session, "顺利达成", {"timing": "第 5 天"})
        self.assertFalse(any("应期参考" in item for item in result["verified"]))

    def test_analysis_covers_four_dimensions(self):
        session = _cast_session(workflow=_workflow("大吉"))
        result = review_outcome(session, "顺利达成")
        self.assertEqual(set(result["analysis"]),
                         {"yongshen", "wangshuai", "timing", "external_interference"})
        self.assertIn("官鬼", result["analysis"]["yongshen"])
        self.assertIn("旺（得令）", result["analysis"]["wangshuai"])

    def test_unexpected_events_are_reported(self):
        session = _cast_session(workflow=_workflow("大吉"))
        result = review_outcome(session, "顺利达成",
                                {"unexpected": ["上游延期", "合作方换人"]})
        text = result["analysis"]["external_interference"]
        self.assertIn("上游延期；合作方换人", text)

    def test_no_unexpected_events_uses_reflective_prompt(self):
        result = review_outcome(_cast_session(workflow=_workflow("大吉")), "顺利达成")
        self.assertIn("是否存在未预见", result["analysis"]["external_interference"])

    def test_lessons_count_follows_verified_and_unverified(self):
        session = _cast_session(workflow=_workflow("大吉"))
        result = review_outcome(session, "顺利达成", {"key_factors": ["突发事件"]})
        self.assertEqual(len(result["lessons"]), 4)
        self.assertIn("应验方面", result["lessons"][0])
        self.assertIn("未应验方面", result["lessons"][1])
        self.assertIn("非绝对预言", result["lessons"][2])

    def test_favorable_only_lessons_omit_unverified_entry(self):
        session = _cast_session(workflow=_workflow("大吉"))
        result = review_outcome(session, "顺利达成")
        self.assertEqual(len(result["lessons"]), 3)
        self.assertFalse(any("未应验方面" in item for item in result["lessons"]))

    def test_missing_snapshot_returns_error(self):
        session = create_session(question="未排盘")
        self.assertIn("error", review_outcome(session, "有结果了"))

    def test_outcome_classifier_keywords(self):
        self.assertTrue(review_module._classify_outcome("考试录取"))
        self.assertFalse(review_module._classify_outcome("投资亏损"))
        self.assertFalse(review_module._classify_outcome("项目失败"))
        # 未命中关键词时默认按偏有利处理（中性）
        self.assertTrue(review_module._classify_outcome("结果不好也不坏"))

    def test_negated_keyword_is_not_classified_as_favorable(self):
        """「未通过」是否定结果，虽包含「通过」但必须先判不利关键词。"""
        self.assertFalse(review_module._classify_outcome("考试未通过"))


# ============================================================
# 深度追问（D②）
# ============================================================

class TestDeepQuestion(unittest.TestCase):
    def test_missing_snapshot_returns_error(self):
        session = create_session(question="未排盘")
        self.assertIn("error", deep_question(session, "本卦如何"))

    def test_general_question_gets_general_section(self):
        session = _cast_session(workflow=_workflow())
        result = deep_question(session, "再说说看")
        self.assertEqual(result["detected_symbols"], ["general"])
        self.assertIn("未明确指向特定符号类型", result["analysis"])
        self.assertIn(session.snapshot.snapshot_id, result["analysis"])
        self.assertTrue(result["snapshot_unchanged"])
        self.assertEqual(result["question"], "再说说看")

    def test_all_symbol_types_detected_in_mapping_order(self):
        question = "卦中动爻的用神六亲六神五行旺衰冲合吉凶"
        self.assertEqual(
            deep_question_module._detect_symbols(question),
            ["hexagram", "moving_line", "yongshen", "liugin",
             "liushen", "wuxing", "wangshuai", "chonghe", "fortune"],
        )

    def test_hexagram_section_uses_frozen_plate(self):
        session = _cast_session()
        result = deep_question(session, "本卦和变卦怎么理解")
        info = result["related_plate_data"]["hexagram_info"]
        self.assertEqual(info["ben_gua"], "乾为天")
        self.assertEqual(info["bian_gua"], "坤为地")
        self.assertEqual(info["hu_gua"], "泽天夬")
        self.assertEqual(info["ti_gua"], "乾")
        self.assertEqual(info["yong_gua"], "坤")
        self.assertIn("本卦：乾为天", result["analysis"])
        self.assertIn("体用关系", result["analysis"])

    def test_moving_line_section_includes_yao_ci(self):
        session = _cast_session()
        result = deep_question(session, "动爻在哪里")
        info = result["related_plate_data"]["moving_line_info"]
        self.assertEqual(info["moving_line"], 3)
        self.assertEqual(info["yao_ci"], "九三（第3爻）")
        self.assertEqual(info["bian_yao"], "第3爻由阳变阴")
        self.assertIn("第3爻", result["analysis"])
        self.assertIn("九三（第3爻）", result["analysis"])

    def test_empty_plate_yields_none_fields(self):
        session = _cast_session(raw_plate={})
        result = deep_question(session, "本卦是什么")
        info = result["related_plate_data"]["hexagram_info"]
        self.assertIsNone(info["ben_gua"])
        self.assertIsNone(info["bian_gua"])
        self.assertNotIn("本卦：", result["analysis"])

    def test_yongshen_section_reads_step3(self):
        session = _cast_session(workflow=_workflow(primary="妻财"))
        result = deep_question(session, "用神取得对不对")
        info = result["related_plate_data"]["yongshen_info"]
        self.assertEqual(info["primary"], "妻财")
        self.assertEqual(info["logic"], "事业看官鬼")
        self.assertIn("主用神：妻财", result["analysis"])
        self.assertIn("取用逻辑", result["analysis"])

    def test_yongshen_section_without_workflow(self):
        session = _cast_session()
        result = deep_question(session, "用神")
        self.assertIsNone(result["related_plate_data"]["yongshen_info"]["primary"])
        self.assertIn("用神旺衰直接决定吉凶", result["analysis"])

    def test_wangshuai_section_reads_step4(self):
        session = _cast_session(workflow=_workflow(level="相（月令生用）"))
        result = deep_question(session, "旺衰如何")
        info = result["related_plate_data"]["wangshuai_info"]
        self.assertEqual(info["yongshen_wangshuai"]["level"], "相（月令生用）")
        self.assertIn("用神旺衰：相（月令生用）", result["analysis"])

    def test_wangshuai_section_without_level(self):
        session = _cast_session(workflow={"step4": {}})
        result = deep_question(session, "旺衰")
        self.assertEqual(result["related_plate_data"]["wangshuai_info"], {})
        self.assertIn("旺相休囚死", result["analysis"])
        self.assertNotIn("用神旺衰：", result["analysis"])

    def test_fortune_section_joins_reason_list(self):
        session = _cast_session(workflow=_workflow("小吉"))
        result = deep_question(session, "吉凶和应期")
        info = result["related_plate_data"]["fortune_info"]
        self.assertEqual(info["level"], "小吉")
        self.assertIn("判定依据：用神旺，力量充足；体用比和", result["analysis"])
        self.assertIn("参考应期：7日内", result["analysis"])

    def test_fortune_section_accepts_plain_string_basis(self):
        session = _cast_session(workflow={"step6": {
            "fortune_level": "平", "fortune_basis": "单一依据",
            "trend": "平稳", "timing": "本月",
        }})
        result = deep_question(session, "吉凶")
        self.assertIn("判定依据：单一依据", result["analysis"])

    def test_liuqin_section_lists_only_mentioned_relatives(self):
        session = _cast_session()
        result = deep_question(session, "父母和妻财分别代表什么")
        self.assertIn("父母：主长辈、文书", result["analysis"])
        self.assertIn("妻财：主妻子、财运", result["analysis"])
        self.assertNotIn("官鬼：主官职", result["analysis"])

    def test_liushen_section_handles_tengshe_alias(self):
        session = _cast_session()
        result = deep_question(session, "腾蛇和白虎的象义")
        self.assertIn("螣蛇：主惊恐", result["analysis"])
        self.assertIn("白虎：主刑伤", result["analysis"])

    def test_basic_block_is_always_present(self):
        session = _cast_session(category="study")
        info = deep_question(session, "随便")["related_plate_data"]["basic"]
        self.assertEqual(info["category"], "study")
        self.assertEqual(info["system"], "auto")
        self.assertEqual(info["casting_method"], "time")
        self.assertEqual(info["snapshot_id"], session.snapshot.snapshot_id)

    def test_analysis_ends_with_iron_rule_statement(self):
        session = _cast_session()
        text = deep_question(session, "本卦")["analysis"]
        self.assertTrue(text.endswith("盘面本身未做任何修改。"))

    def test_snapshot_remains_frozen(self):
        session = _cast_session()
        before = dict(session.snapshot.raw_plate)
        deep_question(session, "本卦、动爻、用神、旺衰、吉凶")
        self.assertEqual(session.snapshot.raw_plate, before)
        self.assertTrue(session.snapshot.frozen)


# ============================================================
# 换角度解读（D③）
# ============================================================

class TestAngleShift(unittest.TestCase):
    def test_missing_snapshot_returns_error(self):
        session = create_session(question="未排盘")
        self.assertIn("error", angle_shift(session, "对方立场"))

    def test_exact_preset_match(self):
        result = angle_shift(_cast_session(), "对方立场")
        self.assertEqual(result["matched_preset"], "对方立场")
        self.assertEqual(result["shift_description"], "从对方/对手的立场重新解读卦象")
        self.assertEqual(len(result["key_questions"]), 4)
        self.assertTrue(result["snapshot_unchanged"])

    def test_keyword_match_for_longer_phrasing(self):
        result = angle_shift(_cast_session(), "我想从对方的角度再看一次")
        self.assertEqual(result["matched_preset"], "对方立场")

    def test_keyword_match_table(self):
        cases = {
            "看长远一点": "长期视角",
            "聊聊资金": "财务角度",
            "说说恋爱关系": "感情角度",
            "职场晋升": "事业角度",
            "有什么隐患": "风险角度",
            "哪里有机会": "机会角度",
        }
        for phrase, preset in cases.items():
            with self.subTest(phrase=phrase):
                self.assertEqual(angle_shift_module._match_preset(phrase), preset)

    def test_unknown_angle_falls_back_to_generic(self):
        result = angle_shift(_cast_session(), "玄学视角")
        self.assertIsNone(result["matched_preset"])
        self.assertIn("玄学视角", result["shift_description"])
        self.assertEqual(len(result["key_questions"]), 3)
        self.assertIn("玄学视角", result["key_questions"][0])

    def test_empty_angle_should_not_match_a_preset(self):
        """空角度不应命中任何预设（已对空白输入短路返回 None）。"""
        self.assertIsNone(angle_shift_module._match_preset(""))
        self.assertIsNone(angle_shift_module._match_preset("   "))

    def test_suggested_angles_exclude_matched_preset(self):
        result = angle_shift(_cast_session(), "风险角度")
        self.assertEqual(len(result["suggested_angles"]), 4)
        self.assertNotIn("风险角度", result["suggested_angles"])

    def test_suggested_angles_for_unknown_angle_takes_first_five(self):
        result = angle_shift(_cast_session(), "玄学视角")
        self.assertEqual(result["suggested_angles"],
                         ["对方立场", "长期视角", "财务角度", "感情角度", "事业角度"])

    def test_counterparty_branch_reflects_favorable_fortune(self):
        session = _cast_session(workflow=_workflow("大吉"))
        text = angle_shift(session, "对方立场")["reinterpretation"]
        self.assertIn("对方力量较强", text)
        self.assertIn("应爻/用卦所反映的对方状态", text)

    def test_counterparty_branch_reflects_neutral_fortune(self):
        session = _cast_session(workflow=_workflow("平"))
        text = angle_shift(session, "对方立场")["reinterpretation"]
        self.assertIn("需结合旺衰判断", text)

    def test_long_term_branch_mentions_changed_hexagram(self):
        session = _cast_session(workflow=_workflow("大吉"))
        text = angle_shift(session, "长期视角")["reinterpretation"]
        self.assertIn("变卦「坤为地」", text)
        self.assertIn("长期走向需重点看变卦", text)

    def test_finance_branch_mentions_wealth_line(self):
        text = angle_shift(_cast_session(), "财务角度")["reinterpretation"]
        self.assertIn("妻财爻是本角度的核心用神", text)

    def test_risk_and_opportunity_branches_differ(self):
        session = _cast_session(workflow=_workflow("小吉"))
        risk = angle_shift(session, "风险角度")["reinterpretation"]
        chance = angle_shift(session, "机会角度")["reinterpretation"]
        self.assertIn("忌神、凶神、冲克", risk)
        self.assertIn("原神、吉神", chance)

    def test_moving_line_present_and_absent(self):
        with_moving = angle_shift(_cast_session(), "事业角度")["reinterpretation"]
        self.assertIn("第3爻动", with_moving)

        without = angle_shift(_cast_session(raw_plate={"ben_gua": "乾为天"}),
                              "事业角度")["reinterpretation"]
        self.assertIn("本卦无动爻", without)

    def test_empty_plate_uses_placeholder_names(self):
        text = angle_shift(_cast_session(raw_plate={}), "事业角度")["reinterpretation"]
        self.assertIn("本卦「本卦」", text)
        self.assertIn("变卦「变卦」", text)

    def test_original_fortune_is_restated(self):
        session = _cast_session(workflow=_workflow("大凶"))
        text = angle_shift(session, "事业角度")["reinterpretation"]
        self.assertIn("原吉凶定性「大凶」", text)
        self.assertIn("需要谨慎应对", text)

    def test_output_always_declares_iron_rule(self):
        result = angle_shift(_cast_session(), "长期视角")
        self.assertIn("suggested_angles", result)
        self.assertIn("snapshot", result["reinterpretation"])

    def test_snapshot_remains_frozen(self):
        session = _cast_session()
        before = dict(session.snapshot.raw_plate)
        angle_shift(session, "对方立场")
        self.assertEqual(session.snapshot.raw_plate, before)
        self.assertTrue(session.snapshot.frozen)


if __name__ == "__main__":
    unittest.main()
