"""典籍库、六爻进阶推导、四化变体、八宅、玄空、房屋档案存储测试。"""

import json
import tempfile
from pathlib import Path

import pytest

from app.common.classics import ClassicsLibrary
from app.fengshui.bazhai import calculate_bazhai, life_trigram
from app.fengshui.xuankong import calculate_xuankong, period_for_year, opposite_mountain
from app.fengshui import storage
from app.liuyao import advanced
from app.liuyao.engine import line_cast
from app.ziwei.rules import SIHUA_TABLE, SIHUA_VARIANTS

MOMENT = "2026-08-15T16:00:00"
TIMEZONE = "Asia/Shanghai"


@pytest.fixture(scope="module")
def library():
    return ClassicsLibrary()


class TestClassicsLibrary:
    def test_corpus_is_available_and_traceable(self, library):
        assert library.available
        status = library.status()
        assert status["documents"] >= 50
        assert status["chunks"] >= 2000
        assert any("八宅明鏡" in item["title"] for item in status["sourcing_backlog"])

    def test_search_finds_zengshanbuyi_passages(self, library):
        passages = library.search("三合局", category="liuyao", limit=3)
        assert passages
        assert any(p["title"] == "增刪卜易" for p in passages)
        first = passages[0]
        assert first["classic_id"] and first["source_url"].startswith("https://")
        assert "三合局" in first["excerpt"]

    def test_evidence_merges_and_dedupes(self, library):
        rows = library.evidence(["三合局", "元神"], category="liuyao", limit=6)
        ids = [row["classic_id"] for row in rows]
        assert len(ids) == len(set(ids))
        assert rows


class TestLiuyaoAdvanced:
    def test_yongshen_candidates_and_meta_relatives(self):
        result = line_cast([9, 7, 7, 7, 7, 7], MOMENT, TIMEZONE, focus="求财买卖")
        yongshen = result["facts"]["yongshen"]
        assert yongshen["normalized_focus"] == "求财买卖"
        assert yongshen["targets"] == ["妻财"]
        assert yongshen["support"] == "子孙"
        assert isinstance(yongshen["candidates"], list)
        assert yongshen["candidates"] == sorted(yongshen["candidates"], key=lambda c: (-c["rank_score"], c["position"]))
        assert yongshen["yuan_shen"]["relative"] == "子孙"
        assert yongshen["ji_shen"]["relative"] == "兄弟"

    def test_unknown_focus_is_ignored(self):
        result = line_cast([9, 7, 7, 7, 7, 7], MOMENT, TIMEZONE, focus="不存在的事项")
        assert result["facts"]["yongshen"] is None

    def test_engine_steps_and_evidence_with_focus(self):
        result = line_cast([9, 7, 7, 7, 7, 7], MOMENT, TIMEZONE, focus="自身")
        sequences = [step["sequence"] for step in result["steps"]]
        assert sequences == [1, 2, 3, 4, 5, 6, 7]
        assert result["steps"][6]["rule_ids"] == ["LY-YONGSHEN-001"]
        assert result["evidence"], "本地语料存在时应给出典籍原文"
        assert any(item["category"] == "liuyao" for item in result["evidence"])

    def test_hidden_emerge_blockers(self):
        result = line_cast([9, 7, 7, 7, 7, 7], MOMENT, TIMEZONE)
        coverage = result["facts"]["hidden_flying_spirits"]
        for hidden in coverage["hidden_spirits"]:
            assert "emerge_blockers" in hidden and "can_emerge" in hidden
        assert coverage["emerge_note"]

    def test_punishments_and_harms_pair_tables(self):
        marks = advanced._relation_marks("寅", "巳")
        assert ("三刑", frozenset(("寅", "巳"))) in marks
        assert ("六害", frozenset(("寅", "巳"))) in marks
        assert ("自刑", frozenset(("辰", "辰"))) in advanced._relation_marks("辰", "辰")
        assert advanced._relation_marks("子", "丑") == []

    def test_punishments_harms_collects_day_month_pairs(self):
        result = line_cast([9, 7, 7, 7, 7, 7], MOMENT, TIMEZONE)
        facts = result["facts"]["punishments_harms"]
        assert set(facts) == {"marks", "note"}

    def test_sanhe_conditions_full_moving_forms_line(self):
        from app.liuyao.engine import _branch_structures

        lines = [
            {"position": i, "najia_branch": branch, "is_moving": True,
             "void_state": "", "is_month_break": False, "is_dark_move": False,
             "month_strength": "旺"}
            for i, branch in enumerate(("申", "子", "辰", "午", "戌", "寅"), 1)
        ]
        structures = _branch_structures(["申", "子", "辰"], "巳", "酉")
        assessments = advanced.assess_sanhe_conditions(structures, lines)
        assert assessments[0]["status"] == "成局"
        assert assessments[0]["moving_member_count"] == 3

    def test_sanhe_conditions_two_moving_pending(self):
        from app.liuyao.engine import _branch_structures

        lines = [
            {"position": 1, "najia_branch": "申", "is_moving": True, "void_state": "",
             "is_month_break": False, "is_dark_move": False, "month_strength": "旺"},
            {"position": 2, "najia_branch": "子", "is_moving": True, "void_state": "",
             "is_month_break": False, "is_dark_move": False, "month_strength": "旺"},
            {"position": 3, "najia_branch": "辰", "is_moving": False, "void_state": "",
             "is_month_break": False, "is_dark_move": False, "month_strength": "旺"},
        ]
        structures = _branch_structures(["申", "子"], "辰", "酉")
        assessments = advanced.assess_sanhe_conditions(structures, lines)
        assert assessments[0]["status"].startswith("不成局")
        assert any("辰" in item for item in assessments[0]["conditions"])


class TestSihuaVariant:
    def test_diverging_stems_differ_between_variants(self):
        quanshu = SIHUA_VARIANTS["quanshu"]["table"]
        bieben = SIHUA_VARIANTS["bieben"]["table"]
        for stem in ("庚", "壬"):
            assert quanshu[stem] != bieben[stem]
            assert bieben[stem]["化科"] == "天府"
            for key in ("化禄", "化权", "化忌"):
                assert quanshu[stem][key] == bieben[stem][key]

    def test_other_stems_are_identical(self):
        quanshu = SIHUA_VARIANTS["quanshu"]["table"]
        bieben = SIHUA_VARIANTS["bieben"]["table"]
        for stem in ("甲", "乙", "丙", "丁", "戊", "己", "辛", "癸"):
            assert quanshu[stem] == bieben[stem]

    def test_primary_table_unchanged(self):
        assert SIHUA_TABLE["庚"]["化科"] == "太阴"
        assert SIHUA_TABLE["壬"]["化科"] == "左辅"


class TestBazhai:
    def test_dayou_nian_song_for_kan_house(self):
        result = calculate_bazhai("子")
        facts = result["facts"]
        assert facts["sitting_trigram"] == "坎"
        assert facts["house_group"] == "东四宅"
        stars = {row["palace"]: row["star"] for row in facts["directions"]}
        # 坎宅：生气巽、延年离、天医震、绝命坤、五鬼艮、六煞乾、祸害兑
        assert stars == {"坎": "伏位", "艮": "五鬼", "震": "天医", "巽": "生气",
                         "离": "延年", "坤": "绝命", "兑": "祸害", "乾": "六煞"}

    def test_life_trigram_formula(self):
        assert life_trigram(1990, "男") == "坎"
        assert life_trigram(1990, "女") == "艮"
        assert life_trigram(2005, "男") == "巽"
        assert life_trigram(1962, "男") == "坤"

    def test_life_match_group(self):
        result = calculate_bazhai("子", birth_year=1990, gender="男")
        match = result["facts"]["life_match"]
        assert match["group_match"] is True
        assert match["life_group"] == "东四命"
        assert match["auspicious_directions"]

    def test_west_four_house(self):
        result = calculate_bazhai("乾")
        assert result["facts"]["house_group"] == "西四宅"


class TestXuankong:
    def test_period_boundaries(self):
        assert period_for_year(1864) == 1
        assert period_for_year(1984) == 7
        assert period_for_year(2026) == 9
        assert period_for_year(2043) == 9

    def test_period_9_wu_shing_wang_shan_wang_xiang(self):
        result = calculate_xuankong("午", year=2026)
        facts = result["facts"]
        assert facts["period"] == 9
        assert facts["sitting_mountain"] == "午" and facts["facing_mountain"] == "子"
        assert facts["sitting_yuan_dragon"] == "天"
        met = {row["name"] for row in facts["conditions"] if row["met"]}
        assert "旺山旺向" in met
        grid = {row["palace"]: row for row in facts["grid"]}
        assert grid["离"]["mountain_star"] == 9
        assert grid["坎"]["facing_star"] == 9

    def test_yin_yang_fly_direction(self):
        result = calculate_xuankong("子", year=2026)
        fly = result["facts"]["fly_direction"]
        assert fly["sitting"] == "逆飞"
        result2 = calculate_xuankong("壬", year=2026)
        assert result2["facts"]["fly_direction"]["sitting"] == "顺飞"

    def test_opposite_mountain(self):
        assert opposite_mountain("子") == "午"
        assert opposite_mountain("艮") == "坤"

    def test_ti_pu_requires_measured_degree(self):
        result = calculate_xuankong("午", year=2026)
        assert result["facts"]["ti_pu"]["in_ti_pu_region"] is None
        near_boundary = calculate_xuankong("午", year=2026, sitting_degree=172.0)
        assert near_boundary["facts"]["ti_pu"]["in_ti_pu_region"] is True
        center = calculate_xuankong("午", year=2026, sitting_degree=180.0)
        assert center["facts"]["ti_pu"]["in_ti_pu_region"] is False

    def test_evidence_from_kanyu_corpus(self):
        result = calculate_xuankong("午", year=2026)
        assert isinstance(result["evidence"], list)


class TestStorage:
    @pytest.fixture(autouse=True)
    def file_backend(self, tmp_path, monkeypatch):
        monkeypatch.setenv("FENGSHUI_FILE_ROOT", str(tmp_path / "buildings"))
        monkeypatch.delenv("FENGSHUI_STORAGE", raising=False)
        storage.reset_backend()
        yield
        storage.reset_backend()

    def _profile(self, name="临江雅苑"):
        return {
            "name": name,
            "address_hint": "示例市示例路1号",
            "owner_consent": True,
            "consent_recorded_at": "2026-11-04T10:00:00+08:00",
            "source": "manual_compass",
            "measurements": [{"facing_degree": 178.0, "measurement_error": 1.0}],
        }

    def test_upsert_get_list_delete(self):
        row = storage.upsert_profile("tenant-a", "b-001", self._profile())
        assert row["tenant_id"] == "tenant-a"
        assert storage.get_profile("tenant-a", "b-001")["profile"]["name"] == "临江雅苑"
        assert len(storage.list_profiles("tenant-a")) == 1
        assert storage.delete_profile("tenant-a", "b-001") is True
        assert storage.get_profile("tenant-a", "b-001") is None

    def test_tenant_isolation(self):
        storage.upsert_profile("tenant-a", "b-001", self._profile())
        assert storage.list_profiles("tenant-b") == []
        assert storage.get_profile("tenant-b", "b-001") is None
        assert storage.delete_profile("tenant-b", "b-001") is False

    def test_update_preserves_created_at(self):
        first = storage.upsert_profile("tenant-a", "b-001", self._profile())
        second = storage.upsert_profile("tenant-a", "b-001", self._profile(name="改名苑"))
        assert second["created_at"] == first["created_at"]
        assert second["updated_at"] >= first["updated_at"]

    def test_consent_is_required(self):
        payload = self._profile()
        payload["owner_consent"] = False
        with pytest.raises(ValueError, match="owner_consent"):
            storage.upsert_profile("tenant-a", "b-001", payload)

    def test_identifier_validation(self):
        with pytest.raises(ValueError):
            storage.upsert_profile("../evil", "b-001", self._profile())
        with pytest.raises(ValueError):
            storage.upsert_profile("tenant-a", "b/001", self._profile())

    def test_ddl_contains_tenant_key(self):
        from app.fengshui.storage import DDL

        assert "PRIMARY KEY (tenant_id, building_id)" in DDL
