import importlib.util
from pathlib import Path
import unittest


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "build_corpus.py"
SPEC = importlib.util.spec_from_file_location("build_corpus", MODULE_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ChunkTests(unittest.TestCase):
    def test_chunks_reconstruct_original_text(self):
        text = ("乾坤阴阳。" * 500) + "末尾\n"
        chunks = MODULE.chunk_text(text, target_size=120, max_size=180)
        self.assertEqual("".join(item[2] for item in chunks), text)
        self.assertTrue(all(len(item[2]) <= 180 for item in chunks))

    def test_long_unbroken_text_uses_max_size(self):
        text = "道" * 401
        chunks = MODULE.chunk_text(text, target_size=100, max_size=150)
        self.assertEqual([len(item[2]) for item in chunks], [150, 150, 101])
        self.assertEqual("".join(item[2] for item in chunks), text)

    def test_invalid_chunk_sizes_are_rejected(self):
        with self.assertRaises(ValueError):
            MODULE.chunk_text("文本", target_size=100, max_size=50)

    def test_clickhouse_datetime_normalizes_iso8601(self):
        self.assertEqual(
            MODULE.clickhouse_datetime("2026-08-15T06:21:46+00:00"),
            "2026-08-15 06:21:46",
        )
        self.assertIsNone(MODULE.clickhouse_datetime(None))


if __name__ == "__main__":
    unittest.main()
