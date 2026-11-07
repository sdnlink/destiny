"""典籍库、六爻进阶推导、四化变体、八宅、玄空、房屋档案存储测试。"""

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
    instance = ClassicsLibrary()
    if not instance.available:
        pytest.skip("本地典籍语料未生成（data/generated/ 与 cache/ 不入库）："
                    "按 docs/sources/wikisource.md 复现命令生成后再跑真实语料断言")
    return instance


class TestClassicsLibrary:
    def test_corpus_is_available_and_traceable(self, library):
        assert library.available
        status = library.status()
        assert status["documents"] >= 85
        assert status["chunks"] >= 4000
        backlog = {item["title"]: item["note"] for item in status["sourcing_backlog"]}
        assert "已由" in backlog["八宅明鏡"], "八宅明鏡应由公开来源补齐"
        assert "daozhige" in backlog["卜筮正宗"]

    def test_multi_source_coverage_for_new_books(self, library):
        for query, category in (("游年歌", "yangzhai"), ("挨星", "kanyu"), ("太微赋", "ziwei"), ("黄金策", "liuyao")):
            passages = library.search(query, category=category, limit=2)
            assert passages, "扩库后应能检索到：{}".format(query)

    def test_search_supports_simplified_traditional_variants(self, library):
        # 殆知阁六壬语料为简体（月将），繁体查询应经变体展开命中
        traditional = library.search("月將", category="liuren", limit=2)
        assert traditional, "繁体查询应命中简体语料"
        assert traditional[0]["match_count"] >= 1
        # 摘录必须展示语料原文（简体文本保持简体），保证可回溯
        assert "月將" not in traditional[0]["excerpt"] or "月将" in traditional[0]["excerpt"]
        # 反方向：维基文库繁体语料用简体查询也应命中
        simplified = library.search("大游年", category="yangzhai", limit=3)
        assert any("遊年" in p["excerpt"] or "游年" in p["excerpt"] for p in simplified)

    def test_title_query_accepts_both_scripts(self, library):
        # 标题为繁体（奇門遁甲統宗），简体 title_query 经变体展开也应命中
        for title_query in ("奇門遁甲統宗", "奇门遁甲统宗"):
            passages = library.search("八門", title_query=title_query, limit=1)
            assert passages, "title_query 应命中：{}".format(title_query)

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

    def test_calendar_corpus_search(self, library):
        # 历法语料库补强测试：步天歌、历法常数
        passages = library.search("步天歌", limit=2)
        assert passages, "历法语料库应能被检索"
        assert any("步天歌" in p["title"] or "步天歌" in p["excerpt"] for p in passages)


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
        assert isinstance(result["evidence"], list)
        if ClassicsLibrary().available:
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

    def test_ddl_file_contains_tenant_key(self):
        from pathlib import Path

        sql = (Path(__file__).resolve().parents[2] / "scripts" / "sql" /
               "fengshui_building_profiles.sql").read_text(encoding="utf-8")
        assert "PRIMARY KEY (tenant_id, building_id)" in sql

    def test_source_and_degree_are_required(self):
        payload = self._profile()
        del payload["source"]
        with pytest.raises(ValueError, match="source"):
            storage.upsert_profile("tenant-a", "b-001", payload)
        payload = self._profile()
        payload["measurements"] = [{"facing_degree": 999}]
        with pytest.raises(ValueError, match="facing_degree"):
            storage.upsert_profile("tenant-a", "b-001", payload)
        payload = self._profile()
        payload["owner_consent"] = "false"
        with pytest.raises(ValueError, match="owner_consent"):
            storage.upsert_profile("tenant-a", "b-001", payload)

    def test_server_bound_tenant_ignores_client_declaration(self, monkeypatch):
        monkeypatch.setenv("FENGSHUI_TENANT_ID", "server-tenant")
        row = storage.upsert_profile("client-declared", "b-001", self._profile())
        assert row["tenant_id"] == "server-tenant"
        assert storage.get_profile("any-other", "b-001")["tenant_id"] == "server-tenant"
        assert len(storage.list_profiles("client-declared")) == 1
        monkeypatch.delenv("FENGSHUI_TENANT_ID")

    def test_record_dto_is_stable(self):
        from app.fengshui.storage import make_record

        record = storage.upsert_profile("tenant-a", "b-001", self._profile())
        expected = {"schema_version", "tenant_id", "building_id", "created_at", "updated_at", "profile"}
        assert set(record) == expected
        assert set(make_record("t", "b", {})) == expected
        assert storage.get_profile("tenant-a", "b-001")["building_id"] == "b-001"
