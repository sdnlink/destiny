"""本地多来源典籍语料库，为引擎结论提供原文依据。

数据来源：维基文库（cache_wikisource_texts.py）、殆知阁 GitHub 存档
（cache_open_sources.py）、公开古籍网站转录（cache_web_classics.py），
经 scripts/build_classics_corpus.py 合并切块后落盘
data/generated/wikisource-corpus/（corpus_documents.jsonl + corpus_chunks.jsonl）。
本模块只读加载，不重复抓取；引擎通过 search/evidence 把典籍原文
挂到结果 evidence 字段上，替代未经签署的主观断语。

检索简繁兼容：殆知阁语料为简体、维基文库/网站转录为繁体，查询词先展开
简繁变体再匹配；摘录始终显示语料原文。zhconv 缺失时记录一次告警并退化。
"""

import json
import logging
import os
from pathlib import Path

try:
    from zhconv import convert as _zh_convert
except ImportError:  # 简繁转换是增强能力，缺库时降级
    _zh_convert = None
    logging.getLogger(__name__).warning("zhconv 未安装：典籍检索将退化为原样匹配（跨简繁查询会漏配）")

MAX_QUERY_LENGTH = 100
MAX_SEARCH_LIMIT = 100
SOURCE_MANIFESTS = (
    "wikisource-books.json",
    "open-source-books.json",
    "web-classics-books.json",
)

DEFAULT_CORPUS_DIR = (
    Path(__file__).resolve().parents[3] / "data" / "generated" / "wikisource-corpus"
)
DEFAULT_CALENDAR_CORPUS_DIR = (
    Path(__file__).resolve().parents[3] / "data" / "generated" / "calendar-corpus"
)
DEFAULT_SOURCES_DIR = Path(__file__).resolve().parents[3] / "data" / "sources"
EXCERPT_RADIUS = 60

# 维基文库缺失或不完整的书目：逐项记录补齐来源与残余缺口（清单已清账）。
SOURCING_BACKLOG = (
    {"title": "八宅明鏡", "domain": "yangzhai", "note": "维基文库缺失；已由 web-classics（诗词汇原文转录）补齐全文入库"},
    {"title": "陽宅十書", "domain": "yangzhai", "note": "维基文库缺失；已由 web-classics（王元吉易学网）补齐全文入库"},
    {"title": "沈氏玄空學", "domain": "kanyu", "note": "维基文库缺失；已由 web-classics（中华典藏）补齐卷首至卷六，替卦起星盘仍未实现"},
    {"title": "卜筮正宗", "domain": "liuyao", "note": "维基文库版仅467字符；已由 daozhige-github 全文（约10万字）补充"},
    {"title": "紫微斗數全書", "domain": "ziwei", "note": "维基文库抓取遭限流；已由 web-classics（中华典藏）补齐序文与卷一至卷三，卷四图说暂缺"},
    {"title": "太極圖說", "domain": "xiangshu", "note": "经逐句核对正文完整（自「自無極而為太極」至「大哉易也，斯其至矣」，原文仅约250字），此前『不完整』为长度启发式误报"},
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


def _query_variants(query):
    """展开查询词的简繁变体：原样优先，其余方向兜底。

    殆知阁语料为简体、维基文库/网站转录多为繁体；用户与引擎两侧的关键词
    简繁不定，两侧都要展开。zhconv 缺失时只返回原样。
    """
    variants = [query]
    if _zh_convert is not None and query:
        for direction in ("zh-hant", "zh-hans"):
            converted = _zh_convert(query, direction)
            if converted and converted not in variants:
                variants.append(converted)
    return variants


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
        target_dirs = [self.corpus_dir]
        if self.corpus_dir == DEFAULT_CORPUS_DIR and DEFAULT_CALENDAR_CORPUS_DIR.exists():
            target_dirs.append(DEFAULT_CALENDAR_CORPUS_DIR)

        try:
            for c_dir in target_dirs:
                documents_path = c_dir / "corpus_documents.jsonl"
                chunks_path = c_dir / "corpus_chunks.jsonl"
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
        except (OSError, ValueError, KeyError, TypeError) as exc:
            logging.getLogger(__name__).warning(
                "典籍语料加载失败，本次以空库降级：%s (%s)", self.corpus_dir, exc)
            chunks, documents = [], {}
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
        for name in SOURCE_MANIFESTS:
            manifest_path = self.sources_dir / name
            if manifest_path.exists():
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest_titles.extend(book["title"] for book in manifest.get("books", []))
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
        """按关键词检索原文段落，命中次数多的排前。

        查询词与 title_query 自动展开简繁变体；摘录展示语料原文
        （不显示转换后的文本），保证"原文依据"可逐条回溯。
        """
        self._ensure_loaded()
        if not query:
            return []
        if len(query) > MAX_QUERY_LENGTH:
            raise ValueError("query exceeds {} characters".format(MAX_QUERY_LENGTH))
        if not isinstance(limit, int) or not 1 <= limit <= MAX_SEARCH_LIMIT:
            raise ValueError("limit must be between 1 and {}".format(MAX_SEARCH_LIMIT))
        variants = _query_variants(query)
        title_variants = _query_variants(title_query) if title_query else None
        scored = []
        for chunk in self._chunks:
            if category and chunk["category_id"] != category:
                continue
            if title_variants and not any(variant in chunk["title"] for variant in title_variants):
                continue
            content = chunk["content"]
            for variant in variants:
                count = content.count(variant)
                if count:
                    scored.append((count, chunk, variant))
                    break
        scored.sort(key=lambda item: (-item[0], item[1]["document_id"], item[1]["chunk_index"]))
        return [self._passage(chunk, count, variant) for count, chunk, variant in scored[:limit]]

    def _passage(self, chunk, count, matched_variant):
        return {
            "classic_id": chunk["chunk_id"],
            "document_id": chunk["document_id"],
            "title": chunk["title"],
            "category": chunk["category_id"],
            "chunk_index": chunk["chunk_index"],
            "excerpt": _excerpt(chunk["content"], matched_variant),
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
