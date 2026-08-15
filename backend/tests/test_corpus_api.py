import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[1] / "app" / "corpus_api.py"
SPEC = importlib.util.spec_from_file_location("corpus_api", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


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


if __name__ == "__main__":
    unittest.main()
