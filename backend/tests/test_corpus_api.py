import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "app" / "corpus_api.py"
SPEC = importlib.util.spec_from_file_location("corpus_api", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class FakeClient:
    def __init__(self, rows=None):
        self.rows = rows or []
        self.calls = []

    def query(self, statement, parameters=None):
        self.calls.append((statement, parameters or {}))
        return self.rows


class ApiHelperTests(unittest.TestCase):
    def test_integer_parameter_applies_bounds(self):
        self.assertEqual(MODULE.integer_parameter({}, "limit", 20, 1, 100), 20)
        self.assertEqual(MODULE.integer_parameter({"limit": ["50"]}, "limit", 20, 1, 100), 50)
        with self.assertRaises(MODULE.ApiError):
            MODULE.integer_parameter({"limit": ["101"]}, "limit", 20, 1, 100)

    def test_snippet_preserves_match(self):
        content = "前" * 200 + "阴阳五行" + "后" * 200
        snippet, position = MODULE.make_snippet(content, "阴阳五行", radius=20)
        self.assertEqual(position, 200)
        self.assertIn("阴阳五行", snippet)
        self.assertTrue(snippet.startswith("…"))
        self.assertTrue(snippet.endswith("…"))

    def test_document_id_pattern_is_restrictive(self):
        self.assertTrue(MODULE.DOCUMENT_ID_PATTERN.match("daozang18-761"))
        self.assertFalse(MODULE.DOCUMENT_ID_PATTERN.match("../secret"))


class ScriptVariantTests(unittest.TestCase):
    def test_term_variants_cover_both_scripts(self):
        traditional = MODULE.term_variants("月將")
        simplified = MODULE.term_variants("月将")
        self.assertEqual(traditional[0], "月將")
        self.assertIn("月将", traditional)
        self.assertIn("月將", simplified)
        self.assertEqual(len(traditional), len(set(traditional)), "变体不应重复")

    def test_term_variants_degrade_without_zhconv(self):
        original = MODULE._zh_convert
        MODULE._zh_convert = None
        try:
            self.assertEqual(MODULE.term_variants("月將"), ["月將"])
            self.assertEqual(MODULE.term_variants(""), [])
        finally:
            MODULE._zh_convert = original

    def test_search_expands_variants_in_sql_and_keeps_original_snippet(self):
        content = "前" * 20 + "月将起例" + "后" * 20
        client = FakeClient([{
            "chunk_id": "c-1", "document_id": "d-1", "title": "六壬大全",
            "category_id": "liuren", "chunk_index": 0, "char_start": 0,
            "char_end": len(content), "content": content, "content_sha256": "x",
        }])
        repository = MODULE.CorpusRepository(client)
        results = repository.search("月將", "liuren", 5)
        statement, params = client.calls[0]
        self.assertIn(" OR ", statement)
        self.assertEqual(params["term_0"], "月將")
        self.assertIn("月将", params.values())
        self.assertEqual(params["category"], "liuren")
        self.assertEqual(results[0]["match_offset_in_chunk"], 20)
        self.assertIn("月将起例", results[0]["snippet"])

    def test_title_query_expands_variants(self):
        client = FakeClient([])
        repository = MODULE.CorpusRepository(client)
        repository.list_documents(None, None, "奇门遁甲统宗", 10, 0)
        statement, params = client.calls[0]
        self.assertIn(" OR ", statement)
        self.assertIn("奇門遁甲統宗", params.values())


if __name__ == "__main__":
    unittest.main()
