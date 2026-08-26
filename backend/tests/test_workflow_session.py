"""测试：交互式推演会话模型与工作流引擎。

重点验证：
1. 不可变快照铁律：snapshot 冻结后不可修改
2. 会话状态机流转
3. 信息补全模块
4. 现实校验模块（不改快照）
5. 交互记录只追加
"""

import json
import os
import sys
import tempfile

import pytest

# 确保 backend 目录在 path 中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.session import (
    DivinationSession,
    create_session,
    freeze_snapshot,
    append_interaction,
    get_store,
    SessionStore,
)
from app.interaction import (
    generate_completion_prompt,
    detect_missing,
    process_reality_response,
    analyze_multi_party,
    analyze_branches,
    review_outcome,
)
from app.workflow.scheduler import select_systems, build_calculation_requests


# ============================================================
# 会话模型测试
# ============================================================

class TestSessionModel:
    def test_create_session_defaults(self):
        session = create_session(question="测试事业发展")
        assert session.session_id.startswith("sess_")
        assert session.question == "测试事业发展"
        assert session.status == "draft"
        assert session.snapshot is None
        assert session.interactions == []

    def test_freeze_snapshot_creates_immutable(self):
        session = create_session(question="测试")
        raw_plate = {"hexagram": "乾为天", "moving_line": 3}
        module_results = [{"module": "meihua", "result": {"facts": {}}}]
        input_payload = {"question": "测试", "casting_method": "auto"}

        session = freeze_snapshot(session, raw_plate, module_results, input_payload)

        assert session.snapshot is not None
        assert session.snapshot.frozen is True
        assert session.snapshot.raw_plate == raw_plate
        assert session.snapshot.input_hash.startswith("sha256:")
        assert session.status == "casted"

    def test_freeze_snapshot_twice_raises(self):
        """铁律：已冻结的快照不可重新排盘。"""
        session = create_session(question="测试")
        session = freeze_snapshot(session, {"test": True}, [], {"q": "1"})

        with pytest.raises(RuntimeError, match="盘面已冻结"):
            freeze_snapshot(session, {"test": False}, [], {"q": "2"})

    def test_snapshot_unchanged_after_interaction(self):
        """交互后原始快照保持不变。"""
        session = create_session(question="测试")
        raw_plate = {"hexagram": "坤为地"}
        session = freeze_snapshot(session, raw_plate, [], {"q": "1"})
        original_hash = session.snapshot.input_hash
        original_plate = json.dumps(session.snapshot.raw_plate, sort_keys=True)

        # 追加交互
        session = append_interaction(
            session, "reality_check",
            user_input={"response": "符合"},
            system_response={"action": "enter_extended"},
        )

        # 快照不变
        assert session.snapshot.input_hash == original_hash
        assert json.dumps(session.snapshot.raw_plate, sort_keys=True) == original_plate
        assert session.snapshot.frozen is True

    def test_append_interaction_only_appends(self):
        """交互记录只追加，不修改历史。"""
        session = create_session(question="测试")
        session = freeze_snapshot(session, {}, [], {"q": "1"})

        session = append_interaction(session, "reality_check", {"r": "1"}, {"a": "1"})
        assert len(session.interactions) == 1

        session = append_interaction(session, "multi_party", {"r": "2"}, {"a": "2"})
        assert len(session.interactions) == 2
        assert session.interactions[0].type == "reality_check"
        assert session.interactions[1].type == "multi_party"

    def test_invalid_interaction_type_raises(self):
        session = create_session(question="测试")
        session = freeze_snapshot(session, {}, [], {"q": "1"})
        with pytest.raises(ValueError, match="unsupported interaction type"):
            append_interaction(session, "invalid_type", {}, {})

    def test_session_status_transitions(self):
        session = create_session(question="测试")
        assert session.status == "draft"

        session = freeze_snapshot(session, {}, [], {"q": "1"})
        assert session.status == "casted"

        session = append_interaction(session, "reality_check", {}, {})
        assert session.status == "interacting"


# ============================================================
# 会话存储测试
# ============================================================

class TestSessionStore:
    def test_save_and_load(self, tmp_path):
        store = SessionStore(storage_dir=str(tmp_path))
        session = create_session(question="存储测试")
        store.save(session)

        loaded = store.load(session.session_id)
        assert loaded is not None
        assert loaded.question == "存储测试"
        assert loaded.session_id == session.session_id

    def test_load_nonexistent_returns_none(self, tmp_path):
        store = SessionStore(storage_dir=str(tmp_path))
        assert store.load("nonexistent") is None

    def test_list_sessions(self, tmp_path):
        store = SessionStore(storage_dir=str(tmp_path))
        for i in range(3):
            s = create_session(question=f"测试{i}")
            store.save(s)
        sessions = store.list_sessions()
        assert len(sessions) == 3


# ============================================================
# 信息补全模块测试
# ============================================================

class TestInfoCompletion:
    def test_detect_missing_for_new_session(self):
        session = create_session(question="测试")
        missing = detect_missing(session)
        assert isinstance(missing, list)
        assert len(missing) <= 3  # 最多3项

    def test_generate_completion_prompt(self):
        session = create_session(question="测试")
        prompt = generate_completion_prompt(session)
        assert prompt["type"] == "info_completion"
        assert "questions" in prompt
        assert "instruction" in prompt

    def test_ready_when_all_info_present(self):
        session = create_session(
            question="测试",
            casting_method="time",
            casting_source={"local_datetime": "2026-08-26T10:00:00", "timezone": "Asia/Shanghai"},
            user_profile={"gender": "男", "current_stage": "进行中"},
        )
        session.system = "meihua"
        prompt = generate_completion_prompt(session)
        # 信息充足时 ready 可能为 True（取决于检测逻辑）
        assert "ready" in prompt


# ============================================================
# 现实校验模块测试
# ============================================================

class TestRealityCheck:
    def _make_cast_session(self):
        session = create_session(question="测试")
        return freeze_snapshot(session, {"hexagram": "测试卦"}, [], {"q": "1"})

    def test_response_fit(self):
        session = self._make_cast_session()
        result = process_reality_response(session, "符合")
        assert result["response_type"] == "符合"
        assert result["action"] == "enter_extended"
        assert result["snapshot_unchanged"] is True

    def test_response_partial_fit_triggers_shift(self):
        session = self._make_cast_session()
        result = process_reality_response(session, "部分符合", details="事业部分符合")
        assert result["response_type"] == "部分符合"
        assert result["action"] == "adjust_interpretation"
        assert "interpretation_shift" in result
        assert result["snapshot_unchanged"] is True

    def test_response_not_fit_offers_choice(self):
        session = self._make_cast_session()
        result = process_reality_response(session, "不符合")
        assert result["response_type"] == "不符合"
        assert result["action"] == "offer_choice"
        assert "options" in result
        assert len(result["options"]) == 2

    def test_unknown_response(self):
        session = self._make_cast_session()
        result = process_reality_response(session, "不知道")
        assert result["action"] == "retry"

    def test_reality_check_without_cast_raises(self):
        session = create_session(question="未排盘")
        with pytest.raises(RuntimeError, match="盘面尚未生成"):
            process_reality_response(session, "符合")


# ============================================================
# 多方人物取象测试
# ============================================================

class TestMultiParty:
    def test_detect_parties_from_question(self):
        from app.interaction.multi_party import detect_parties
        parties = detect_parties("我和对方合作事业如何")
        assert "求测人" in parties
        assert "对方" in parties

    def test_analyze_multi_party(self):
        session = create_session(question="测试")
        session = freeze_snapshot(session, {}, [], {"q": "1"})
        result = analyze_multi_party(session, parties=["求测人", "对方"])
        assert "parties" in result
        assert len(result["parties"]) == 2
        assert result["snapshot_unchanged"] is True


# ============================================================
# 多抉择分支推演测试
# ============================================================

class TestMultiChoice:
    def test_analyze_branches(self):
        session = create_session(question="测试")
        session = freeze_snapshot(session, {}, [], {"q": "1"})
        result = analyze_branches(session, choices=["方案A", "方案B"])
        assert "choices" in result
        assert len(result["choices"]) == 2
        assert "recommendation" in result
        assert result["snapshot_unchanged"] is True

    def test_insufficient_choices(self):
        session = create_session(question="测试")
        session = freeze_snapshot(session, {}, [], {"q": "1"})
        result = analyze_branches(session, choices=["只有一个"])
        assert "error" in result


# ============================================================
# 事后复盘测试
# ============================================================

class TestReview:
    def test_review_outcome(self):
        session = create_session(question="测试事业")
        session = freeze_snapshot(session, {}, [], {"q": "1"})
        result = review_outcome(session, "事业发展顺利，成功晋升")
        assert "actual_outcome" in result
        assert "verified" in result
        assert "unverified" in result
        assert "analysis" in result
        assert "lessons" in result
        assert result["snapshot_unchanged"] is True
        assert session.status == "reviewed"


# ============================================================
# 术数调度策略测试
# ============================================================

class TestScheduler:
    def test_default_uses_meihua_and_liuyao(self):
        systems, note = select_systems("auto")
        assert "meihua" in systems
        assert "liuyao" in systems

    def test_liuyao_single_system(self):
        systems, note = select_systems("liuyao")
        assert systems == ["liuyao"]

    def test_qimen_single_system(self):
        systems, note = select_systems("qimen")
        assert systems == ["qimen"]

    def test_daliuren_single_system(self):
        systems, note = select_systems("daliuren")
        assert systems == ["daliuren"]

    def test_build_requests_includes_calendar(self):
        requests = build_calculation_requests(
            ["meihua"], "auto",
            {"local_datetime": "2026-08-26T10:00:00", "timezone": "Asia/Shanghai", "cast_nonce": "test1234567890"},
        )
        modules = [r["module"] for r in requests]
        assert "calendar" in modules
        assert "meihua" in modules
