import sys
from pathlib import Path
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from cache_wikisource_texts import VisibleTextParser, _resolved_page, combine_pages, normalize_text, title_slug


class WikisourceCacheTests(unittest.TestCase):
    def test_slug_is_stable_and_distinguishes_titles(self):
        self.assertEqual(title_slug("梅花易數"), title_slug("梅花易數"))
        self.assertNotEqual(title_slug("梅花易數"), title_slug("梅花易数"))

    def test_visible_text_excludes_non_export_controls(self):
        parser = VisibleTextParser()
        parser.feed('<div><p>正文甲</p><span class="mw-editsection">编辑</span><p>正文乙</p></div>')
        self.assertEqual(parser.text(), "正文甲\n\n正文乙\n")

    def test_normalize_text_is_deterministic(self):
        self.assertEqual(normalize_text("甲  \r\n\r\n\r\n 乙\t"), "甲\n\n乙\n")

    def test_combines_pages_and_deduplicates_exact_text(self):
        pages = [
            {"title": "书/一", "text": "正文一足够长的内容用于测试并验证重复页面过滤。\n", "page_id": 1},
            {"title": "书/重复", "text": "正文一足够长的内容用于测试并验证重复页面过滤。\n", "page_id": 2},
            {"title": "书/二", "text": "正文二足够长的内容用于测试并保留不同页面文本。\n", "page_id": 3},
        ]
        text, accepted = combine_pages(pages)
        self.assertNotIn("书/重复", text)
        self.assertEqual([item["page_id"] for item in accepted], [1, 3])

    def test_resolves_api_redirect_titles(self):
        query = {
            "redirects": [{"from": "周易/序卦", "to": "易傳/序卦"}],
            "pages": [{"title": "易傳/序卦", "pageid": 8}],
        }
        self.assertEqual(_resolved_page(query, "周易/序卦")["pageid"], 8)


if __name__ == "__main__":
    unittest.main()
