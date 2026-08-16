import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from build_wikisource_corpus import build


class WikisourceCorpusBuildTests(unittest.TestCase):
    def test_build_preserves_license_and_reconstructs_chunks(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            cache = root / "cache"
            output = root / "output"
            (cache / "texts").mkdir(parents=True)
            text = "梅花易數正文。" * 20 + "\n"
            raw = text.encode("utf-8")
            import hashlib
            digest = hashlib.sha256(raw).hexdigest()
            (cache / "texts" / "book.txt").write_bytes(raw)
            catalog = {
                "source": {"source_id": "zh-wikisource-open", "api_url": "https://example.test/api"},
                "books": [{
                    "document_id": "wikisource-book", "slug": "book", "title": "梅花易數", "domain": "meihua",
                    "source_url": "https://example.test/book", "usage_scope": "open_licensed_research",
                    "parser_version": "test", "sha256": digest, "characters": len(text), "bytes": len(raw),
                    "page_count": 1, "fetched_at": "2026-08-16T00:00:00+00:00", "status": "ok",
                    "license_name": "CC BY-SA 4.0", "license_url": "https://example.test/license",
                }],
            }
            (cache / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
            build(cache, output, 40, 60)
            document = json.loads((output / "corpus_documents.jsonl").read_text(encoding="utf-8"))
            chunks = [json.loads(line) for line in (output / "corpus_chunks.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(document["license_name"], "CC BY-SA 4.0")
            self.assertEqual("".join(chunk["content"] for chunk in chunks), text)


if __name__ == "__main__":
    unittest.main()

