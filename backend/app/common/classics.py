"""本地典籍语料库：加载维基文库存档，为引擎结论提供原文依据。

数据来源：scripts/cache_wikisource_texts.py 按公开许可清单抓取，
经 scripts/build_wikisource_corpus.py 切块后落盘
data/generated/wikisource-corpus/（corpus_documents.jsonl + corpus_chunks.jsonl）。
本模块只读加载，不重复抓取；引擎通过 search/evidence 把典籍原文
挂到结果 evidence 字段上，替代未经签署的主观断语。
"""

import json
import os
from pathlib import Path

DEFAULT_CORPUS_DIR = (
    Path(__file__).resolve().parents[3] / "data" / "generated" / "wikisource-corpus"
)
DEFAULT_SOURCES_DIR = Path(__file__).resolve().parents[3] / "data" / "sources"
EXCERPT_RADIUS = 60

# 维基文库缺失或不完整、已由其他公开来源补齐/待补的书目。
SOURCING_BACKLOG = (
    {"title": "八宅明鏡", "domain": "yangzhai", "note": "维基文库缺失；已由 web-classics（诗词汇原文转录）补齐全文入库"},
    {"title": "陽宅十書", "domain": "yangzhai", "note": "维基文库缺失；已由 web-classics（王元吉易学网）补齐全文入库"},
    {"title": "沈氏玄空學", "domain": "kanyu", "note": "维基文库缺失；已由 web-classics（中华典藏）补齐卷首至卷六，替卦起星盘仍未实现"},
    {"title": "卜筮正宗", "domain": "liuyao", "note": "维基文库版仅467字符；已由 daozhige-github 全文（约10万字）补充"},
    {"title": "紫微斗數全書", "domain": "ziwei", "note": "维基文库抓取遭限流；已由 web-classics（中华典藏）补齐序文与卷一至卷三，卷四图说暂缺"},
    {"title": "太極圖說", "domain": "xiangshu", "note": "维基文库现有抓取不完整，待重抓"},
)


def _excerpt(content, query):
    position = content.find(query)
    if position < 0:
        text = content[: EXCERPT_RADIUS * 2]
        return text + ("…" if len(content) > len(text) else "")
    start = max(0, position - EXCERPT_RADIUS)
    end = min(len(content), position + len(query) + EXCERPT_RADIUS)
    prefix = "…" if start else ""
    suffix = "…" if end < len(content) else ""
    return prefix + content[start:end].replace("\n", " ").strip() + suffix


class ClassicsLibrary:
    """只读典籍库。首次访问时把 jsonl 索引进内存（约 10MB 量级）。"""

    def __init__(self, corpus_dir=None, sources_dir=None):
        self.corpus_dir = Path(corpus_dir or os.environ.get("CLASSICS_CORPUS_DIR", DEFAULT_CORPUS_DIR))
        self.sources_dir = Path(sources_dir or DEFAULT_SOURCES_DIR)
        self._chunks = None
        self._documents = None

    def _ensure_loaded(self):
        if self._chunks is not None:
            return
        chunks = []
        documents = {}
        documents_path = self.corpus_dir / "corpus_documents.jsonl"
        chunks_path = self.corpus_dir / "corpus_chunks.jsonl"
        if documents_path.exists():
            with documents_path.open(encoding="utf-8") as handle:
                for line in handle:
                    row = json.loads(line)
                    documents[row["document_id"]] = row
        if chunks_path.exists():
            with chunks_path.open(encoding="utf-8") as handle:
                for line in handle:
                    row = json.loads(line)
                    row["chunk_index"] = int(row["chunk_index"])
                    chunks.append(row)
        for chunk in chunks:
            document = documents.get(chunk["document_id"], {})
            chunk["source_url"] = document.get("source_url", "")
            chunk["license_name"] = document.get("license_name", "")
            chunk["license_url"] = document.get("license_url", "")
        self._chunks = chunks
        self._documents = documents

    @property
    def available(self):
        self._ensure_loaded()
        return bool(self._chunks)

    def status(self):
        self._ensure_loaded()
        manifest_titles = []
        manifest_path = self.sources_dir / "wikisource-books.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest_titles = [book["title"] for book in manifest.get("books", [])]
        stored_titles = {document["title"] for document in self._documents.values()}
        return {
            "corpus_dir": str(self.corpus_dir),
            "documents": len(self._documents),
            "chunks": len(self._chunks),
            "characters": sum(document["character_count"] for document in self._documents.values()),
            "incomplete_documents": sorted(
                document["title"] for document in self._documents.values()
                if document["character_count"] < 2000
            ),
            "manifest_not_stored": sorted(set(manifest_titles) - stored_titles),
            "sourcing_backlog": SOURCING_BACKLOG,
        }

    def search(self, query, category=None, title_query=None, limit=5):
        """按关键词检索原文段落，命中次数多的排前。"""
        self._ensure_loaded()
        if not query:
            return []
        scored = []
        for chunk in self._chunks:
            if category and chunk["category_id"] != category:
                continue
            if title_query and title_query not in chunk["title"]:
                continue
            count = chunk["content"].count(query)
            if count:
                scored.append((count, chunk))
        scored.sort(key=lambda item: (-item[0], item[1]["document_id"], item[1]["chunk_index"]))
        return [self._passage(chunk, count, query) for _, chunk in scored[:limit]]

    def _passage(self, chunk, count, query):
        return {
            "classic_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "title": chunk["title"],
            "category": chunk["category_id"],
            "chunk_index": chunk["chunk_index"],
            "excerpt": _excerpt(chunk["content"], query),
            "match_count": count,
            "source_url": chunk["source_url"],
            "license_name": chunk["license_name"],
            "license_url": chunk["license_url"],
        }

    def evidence(self, queries, category=None, per_query=2, limit=6):
        """为一组结论关键词收集去重后的典籍依据。"""
        merged = {}
        for query in queries:
            for passage in self.search(query, category=category, limit=per_query):
                merged.setdefault(passage["classic_id"], passage)
        passages = sorted(
            merged.values(),
            key=lambda item: (-item["match_count"], item["title"], item["chunk_index"]),
        )
        return passages[:limit]


_library = None


def get_library():
    global _library
    if _library is None:
        _library = ClassicsLibrary()
    return _library
