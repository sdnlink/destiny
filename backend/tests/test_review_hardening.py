"""本轮全项目审查修复的回归测试：端点异常分支、输入边界与统一契约。"""
import importlib.util
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.common.classics import ClassicsLibrary
from app.main import app


def _load_script(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def client():
    return TestClient(app)


def _profile(**overrides):
    payload = {
        "name": "审查测试宅",
        "owner_consent": True,
        "source": "manual_compass",
        "measurements": [{"facing_degree": 178.0}],
    }
    payload.update(overrides)
    return payload


class TestFengshuiBuildingEndpoints:
    """HTTPException 之前未导入，异常分支会返回 500；这里逐个验证。"""

    def test_invalid_tenant_returns_422(self, client):
        response = client.get("/v1/fengshui/buildings", params={"tenant_id": "../evil"})
        assert response.status_code == 422

    def test_missing_profile_returns_404(self, client):
        response = client.get("/v1/fengshui/buildings/not-exist", params={"tenant_id": "review-tenant"})
        assert response.status_code == 404

    def test_missing_source_returns_422(self, client):
        payload = _profile()
        del payload["source"]
        response = client.post("/v1/fengshui/buildings", json={
            "tenant_id": "review-tenant", "building_id": "b-001", "profile": payload,
        })
        assert response.status_code == 422

    def test_delete_missing_returns_404(self, client):
        response = client.delete("/v1/fengshui/buildings/not-exist", params={"tenant_id": "review-tenant"})
        assert response.status_code == 404


class TestClassicsEndpoints:
    def test_status_reports_all_manifests(self, client):
        data = client.get("/v1/classics/status").json()["data"]
        if not data["available"]:
            pytest.skip("本地典籍语料未生成（data/generated/ 与 cache/ 不入库）")
        assert data["documents"] >= 85
        assert data["manifest_not_stored"] == [], "三个来源清单的书目都应已入库"

    def test_search_query_bounds(self, client):
        assert client.get("/v1/classics/search", params={"q": ""}).status_code == 422
        assert client.get("/v1/classics/search", params={"q": "甲" * 101}).status_code == 422
        assert client.get("/v1/classics/search", params={"q": "用神", "limit": 0}).status_code == 422
        assert client.get("/v1/classics/search", params={"q": "用神", "limit": 21}).status_code == 422

    def test_library_rejects_invalid_limits_and_long_queries(self):
        library = ClassicsLibrary()
        with pytest.raises(ValueError):
            library.search("用神", limit=0)
        with pytest.raises(ValueError):
            library.search("甲" * 101)

    def test_corrupted_corpus_degrades_without_500(self, tmp_path):
        (tmp_path / "corpus_documents.jsonl").write_text("{bad json\n", encoding="utf-8")
        (tmp_path / "corpus_chunks.jsonl").write_text("{bad json\n", encoding="utf-8")
        library = ClassicsLibrary(corpus_dir=tmp_path)
        assert library.available is False
        assert library.search("用神") == []


class TestLiunianBounds:
    def test_combined_year_range_is_bounded(self, client):
        payload = {
            "local_datetime": "1990-06-15T12:00:00",
            "timezone": "Asia/Shanghai",
            "gender": "男",
            "start_year": 2095,
            "count": 20,
        }
        assert client.post("/v1/bazi/liunian", json=payload).status_code == 422

    def test_evaluate_entry_supports_liunian(self, client):
        response = client.post("/v1/calculations/evaluate", json={
            "module": "bazi", "method": "liunian",
            "input": {
                "local_datetime": "1990-06-15T12:00:00",
                "timezone": "Asia/Shanghai",
                "gender": "男",
                "start_year": 2026,
                "count": 2,
            },
        })
        assert response.status_code == 200
        assert response.json()["data"]["status"] == "completed"


class TestAttributionLinks:
    def test_non_wikisource_documents_have_plain_source_urls(self):
        path = (Path(__file__).resolve().parents[2] / "data" / "generated" /
                "wikisource-corpus" / "corpus_documents.jsonl")
        if not path.exists():
            pytest.skip("本地典籍语料未生成（data/generated/ 不入库）")
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        non_mediawiki = [row for row in rows if row["source_id"] != "zh-wikisource-open"]
        assert non_mediawiki
        assert all("?action=history" not in row["attribution_url"] for row in non_mediawiki)


class TestSyntheticCorpus:
    """不依赖 data/generated/：用两行合成 jsonl 验证加载、检索与简繁变体。"""

    def test_library_loads_and_searches_without_generated_corpus(self, tmp_path):
        document = {
            "document_id": "test-doc-1", "source_id": "daozhige-github",
            "title": "六壬大全", "category_id": "liuren",
            "character_count": 12, "source_url": "https://example.invalid/book",
            "license_name": "测试许可", "license_url": "https://example.invalid/license",
        }
        chunk = {
            "chunk_id": "test-doc-1:00000", "document_id": "test-doc-1",
            "title": "六壬大全", "category_id": "liuren", "chunk_index": 0,
            "content": "月将起例与四课三传", "char_start": 0, "char_end": 10,
        }
        (tmp_path / "corpus_documents.jsonl").write_text(json.dumps(document) + "\n", encoding="utf-8")
        (tmp_path / "corpus_chunks.jsonl").write_text(json.dumps(chunk) + "\n", encoding="utf-8")
        library = ClassicsLibrary(corpus_dir=tmp_path, sources_dir=tmp_path)
        assert library.available is True
        rows = library.search("月將", category="liuren", limit=1)
        assert len(rows) == 1
        assert rows[0]["title"] == "六壬大全"
        assert "月将起例" in rows[0]["excerpt"]
        assert rows[0]["source_url"] == "https://example.invalid/book"
        assert library.status()["manifest_not_stored"] == []


class TestFetchScriptContracts:
    ROOT = Path(__file__).resolve().parents[2]

    def test_web_classics_manifest_urls_are_whitelisted(self):
        script = _load_script("cache_web_classics", self.ROOT / "scripts" / "cache_web_classics.py")
        manifest = json.loads((self.ROOT / "data" / "sources" /
                               "web-classics-books.json").read_text(encoding="utf-8"))
        import urllib.parse
        for book in manifest["books"]:
            for page in book["pages"]:
                host = urllib.parse.urlparse(page["url"]).hostname
                assert host in script.ALLOWED_HOSTS, page["url"]

    def test_web_classics_rejects_file_and_internal_urls(self):
        script = _load_script("cache_web_classics_reject", self.ROOT / "scripts" / "cache_web_classics.py")
        with pytest.raises(ValueError):
            script.fetch("file:///etc/passwd", timeout=1, retries=0)
        with pytest.raises(ValueError):
            script.fetch("http://127.0.0.1:8088/admin", timeout=1, retries=0)

    def test_open_sources_rejects_path_traversal(self):
        import urllib.parse
        # 清单内路径不应含 '..'，且 quote(safe='') 后斜杠也被编码
        manifest = json.loads((self.ROOT / "data" / "sources" /
                               "open-source-books.json").read_text(encoding="utf-8"))
        for book in manifest["books"]:
            assert ".." not in book["repo_path"].split("/")
            assert "/" not in urllib.parse.quote(book["repo_path"], safe="")
