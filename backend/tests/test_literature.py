import os
import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.iching import manual_cast
from app.core.literature import collect_literature_opinions
from app.core.meihua import number_cast


class FakeSearchClient:
    def search(self, term, limit=30):
        return [{
            "chunk_id": "book-1:00001",
            "document_id": "book-1",
            "title": "周易履卦义解",
            "source_url": "https://example.test/book-1",
            "content_sha256": "a" * 64,
            "chunk_index": 1,
            "snippet": "《易》履卦曰：辨上下，定民志。后文继续说明。",
        }]


class DiverseSearchClient:
    def search(self, term, limit=30):
        return [{
            "chunk_id": term + ":1",
            "document_id": term,
            "title": "易学书籍" + term,
            "source_url": "https://example.test/" + term,
            "content_sha256": "b" * 64,
            "chunk_index": 1,
            "snippet": "《易》提到{}，应当积渐而行。".format(term),
        }]


class LiteratureTests(unittest.TestCase):
    def setUp(self):
        self.results = [{
            "module": "zhouyi",
            "method": "manual",
            "result": manual_cast([7, 8, 7, 8, 7, 8]),
        }, {
            "module": "meihua",
            "method": "numbers",
            "result": number_cast(1, 2),
        }]

    def test_returns_exact_source_and_explicit_book_opinion(self):
        output = collect_literature_opinions(self.results, FakeSearchClient(), max_books=1)
        self.assertEqual(output["status"], "available")
        book = output["books"][0]
        self.assertEqual(book["title"], "周易履卦义解")
        self.assertIn("辨上下", book["excerpt"])
        self.assertIn("位置、责任", book["book_opinion"])
        self.assertTrue(book["source_url"])
        self.assertEqual(book["review_status"], "automatic_candidate_unreviewed")

    def test_excerpt_keeps_previous_sentence_for_context(self):
        output = collect_literature_opinions(self.results, FakeSearchClient(), max_books=1)
        self.assertIn("辨上下", output["books"][0]["excerpt"])

    def test_disabled_mode_does_not_require_corpus_service(self):
        previous = os.environ.pop("ENABLE_LITERATURE", None)
        try:
            output = collect_literature_opinions(self.results)
        finally:
            if previous is not None:
                os.environ["ENABLE_LITERATURE"] = previous
        self.assertEqual(output["status"], "disabled")
        self.assertEqual(output["books"], [])

    def test_preserves_one_candidate_per_hexagram(self):
        output = collect_literature_opinions(self.results, DiverseSearchClient(), max_books=4)
        matched_terms = {book["matched_term"] for book in output["books"]}
        expected_terms = {item["term"] for item in output["query_terms"]}
        self.assertEqual(matched_terms, expected_terms)

    def test_qimen_and_ziwei_literature_candidates(self):
        """验证奇门与紫微模块可正确生成典籍检索候选词。"""
        qimen_result = {
            "module": "qimen",
            "method": "time",
            "result": {
                "zhi_fu_star": "天心",
                "zhi_shi_gate": "开门",
                "facts": {"zhi_fu_star": "天心", "zhi_shi_gate": "开门"},
            },
        }
        ziwei_result = {
            "module": "ziwei",
            "method": "time",
            "result": {
                "facts": {
                    "palaces_by_order": [
                        {"name": "命宫", "main_stars": [{"name": "紫微"}]},
                    ]
                }
            },
        }
        output = collect_literature_opinions([qimen_result, ziwei_result], DiverseSearchClient(), max_books=5)
        terms = [item["term"] for item in output["query_terms"]]
        self.assertIn("天心", terms)
        self.assertIn("开门", terms)
        self.assertIn("紫微", terms)
        self.assertTrue(any("奇门" in b["matched_term"] or b["matched_term"] in ("天心", "开门") for b in output["books"]))


if __name__ == "__main__":
    unittest.main()
