import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "cache_daorenjia_texts.py"
SPEC = importlib.util.spec_from_file_location("cache_daorenjia_texts", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ParserTests(unittest.TestCase):
    def test_extracts_only_content4(self):
        parser = MODULE.BookParser()
        parser.feed("""
            <title>测试经 在线阅读</title>
            <div>导航</div>
            <div id="content4"><p>第一段</p><div><p>第二段&nbsp;内容</p></div></div>
            <div>页脚</div>
        """)
        title, text = parser.result()
        self.assertEqual(title, "测试经")
        self.assertIn("第一段", text)
        self.assertIn("第二段 内容", text)
        self.assertNotIn("导航", text)
        self.assertNotIn("页脚", text)

    def test_discovers_book_paths_only(self):
        links = MODULE.parse_links('<a href="daozang18-761">书</a><a href="dztu-761">图</a>')
        paths = [MODULE.same_site_path(link) for link in links]
        self.assertTrue(MODULE.BOOK_PATH.match(paths[0]))
        self.assertFalse(MODULE.BOOK_PATH.match(paths[1]))

    def test_rejects_external_links(self):
        self.assertIsNone(MODULE.same_site_path("https://example.com/daozang18-761"))

    def test_mobile_api_html_uses_same_text_parser(self):
        parser = MODULE.BookParser()
        parser.feed('<div id="content4"><p>第一段</p><p>第二段</p></div>')
        _, text = parser.result()
        self.assertEqual(text, "第一段\n第二段\n")


if __name__ == "__main__":
    unittest.main()
