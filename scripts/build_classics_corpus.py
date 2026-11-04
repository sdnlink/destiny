#!/usr/bin/env python3
"""合并构建多来源典籍语料：维基文库 + 殆知阁存档 + 公开古籍网站转录。

替代单一来源的 build_wikisource_corpus.py：
- 每个来源保留独立 source_id / license / 来源链接，逐书可溯源；
- 输出 schema 与旧构建器完全一致（corpus_documents/chunks/ingestion_runs/analysis），
  app.common.classics.ClassicsLibrary 无需改动。
"""

import argparse
import hashlib
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from build_corpus import DEFAULT_MAX_SIZE, DEFAULT_TARGET_SIZE, chunk_text, sha256_bytes, write_jsonl

BUILDER_VERSION = "classics-builder-2.0.0"
DOMAIN_NAMES = {
    "zhouyi": "周易经传", "xiangshu": "象数", "meihua": "梅花易数", "liuyao": "六爻",
    "liuren": "大六壬", "qimen": "奇门遁甲", "mingli": "命理", "xiangshu_ming": "相术",
    "yangzhai": "阳宅", "kanyu": "堪舆", "ziwei": "紫微斗数",
}
DOMAIN_TERMS = [
    "周易", "易傳", "八卦", "六十四卦", "陰陽", "五行", "河圖", "洛書", "元會運世",
    "梅花易數", "體卦", "用卦", "六爻", "納甲", "六親", "世爻", "應爻", "卜筮",
    "六壬", "月將", "四課", "三傳", "天將", "奇門", "遁甲", "九星", "八門", "三奇",
    "子平", "命理", "用神", "格局", "十神", "相術", "相法", "宅經", "陽宅", "風水", "堪輿",
    "葬書", "青囊", "撼龍", "龍脈", "二十四山", "九宮", "類象",
    "紫微", "太微賦", "安命", "玄空", "挨星", "八宅", "遊年",
]

DEFAULT_SOURCES = (
    ("wikisource", "cache/wikisource"),
    ("daozhige-github", "cache/open-sources"),
    ("web-classics", "cache/web-classics"),
)


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")


def percentile(values, ratio):
    if not values:
        return 0
    return values[round((len(values) - 1) * ratio)]


def _load_books(cache_dir):
    catalog = json.loads((cache_dir / "catalog.json").read_text(encoding="utf-8"))
    source = catalog["source"]
    books = [book for book in catalog["books"] if book.get("status") == "ok"]
    return source, books


def build(cache_root, output_dir, target_size, max_size):
    ingested_at = utc_now()
    documents = []
    chunks = []
    category_stats = defaultdict(lambda: {"documents": 0, "characters": 0, "bytes": 0, "chunks": 0})
    term_frequency = Counter()
    lengths = []
    corpus_digest = hashlib.sha256()
    source_ids = []

    for source_id, relative in DEFAULT_SOURCES:
        cache_dir = cache_root / relative
        catalog_path = cache_dir / "catalog.json"
        if not catalog_path.exists():
            print("skip missing catalog: {}".format(catalog_path))
            continue
        source, books = _load_books(cache_dir)
        source_ids.append(source["source_id"])
        for metadata in sorted(books, key=lambda item: item["document_id"]):
            raw = (cache_dir / "texts" / (metadata["slug"] + ".txt")).read_bytes()
            text = raw.decode("utf-8")
            digest = hashlib.sha256(raw).hexdigest()
            if digest != metadata.get("sha256") or len(text) != metadata.get("characters"):
                raise RuntimeError("cache metadata mismatch: {}".format(metadata["title"]))
            document_chunks = chunk_text(text, target_size, max_size)
            domain = metadata["domain"]
            corpus_digest.update(metadata["document_id"].encode("utf-8"))
            corpus_digest.update(b"\0")
            corpus_digest.update(bytes.fromhex(digest))
            attribution = metadata["source_url"]
            if "history_url" in metadata:
                attribution = metadata["history_url"]
            elif source.get("api_url", "").startswith("https://github.com"):
                attribution = metadata["source_url"]
            else:
                attribution = metadata["source_url"] + "?action=history"
            pages = metadata.get("page_count", 1)
            documents.append({
                "document_id": metadata["document_id"], "source_id": source["source_id"],
                "title": metadata["title"], "category_id": domain,
                "category_name": DOMAIN_NAMES.get(domain, domain), "source_url": metadata["source_url"],
                "fetched_from": source.get("api_url", metadata["source_url"]), "cache_status": "ok",
                "usage_scope": metadata.get("usage_scope", ""),
                "parser_version": metadata.get("parser_version", "web-transcript-1.0"),
                "content_sha256": digest, "character_count": len(text), "byte_count": len(raw),
                "subcontent_count": pages, "available_subcontent_count": pages,
                "unavailable_subcontent_ids": [],
                "fetched_at": metadata.get("fetched_at", ingested_at)[:19].replace("T", " "),
                "ingested_at": ingested_at, "license_name": metadata["license_name"],
                "license_url": metadata.get("license_url", metadata["source_url"]),
                "attribution_url": attribution,
                "language": "zh",
            })
            reconstructed = []
            for chunk_index, (char_start, char_end, content) in enumerate(document_chunks):
                reconstructed.append(content)
                chunks.append({
                    "chunk_id": "{}:{:05d}".format(metadata["document_id"], chunk_index),
                    "document_id": metadata["document_id"], "source_id": source["source_id"],
                    "title": metadata["title"], "category_id": domain, "chunk_index": chunk_index,
                    "char_start": char_start, "char_end": char_end, "character_count": len(content),
                    "content": content, "content_sha256": sha256_bytes(content.encode("utf-8")),
                    "document_sha256": digest, "usage_scope": metadata.get("usage_scope", ""),
                    "ingested_at": ingested_at,
                })
            if "".join(reconstructed) != text:
                raise RuntimeError("chunk reconstruction failed: {}".format(metadata["title"]))
            stats = category_stats[domain]
            stats["name"] = DOMAIN_NAMES.get(domain, domain)
            stats["documents"] += 1
            stats["characters"] += len(text)
            stats["bytes"] += len(raw)
            stats["chunks"] += len(document_chunks)
            lengths.append(len(text))
            for term in DOMAIN_TERMS:
                term_frequency[term] += text.count(term)

    if not documents:
        raise RuntimeError("no documents collected from any source")
    corpus_sha256 = corpus_digest.hexdigest()
    run_id = "{}:{}".format("+".join(source_ids), corpus_sha256[:16])
    for row in documents:
        row["run_id"] = run_id
    for row in chunks:
        row["run_id"] = run_id
    lengths.sort()
    analysis = {
        "source_ids": source_ids, "run_id": run_id, "builder_version": BUILDER_VERSION,
        "corpus_sha256": corpus_sha256, "created_at": ingested_at,
        "documents": len(documents), "chunks": len(chunks),
        "characters": sum(item["character_count"] for item in documents),
        "bytes": sum(item["byte_count"] for item in documents),
        "chunking": {"target_size": target_size, "max_size": max_size, "overlap": 0},
        "document_length": {
            "min": min(lengths), "median": statistics.median(lengths),
            "p95": percentile(lengths, 0.95), "max": max(lengths),
        },
        "categories": [{"category_id": key, **value} for key, value in sorted(category_stats.items())],
        "domain_terms": [{"term": term, "count": term_frequency[term]} for term in DOMAIN_TERMS],
    }
    run = {
        "run_id": run_id, "source_ids": source_ids, "corpus_sha256": corpus_sha256,
        "document_count": len(documents), "chunk_count": len(chunks),
        "character_count": analysis["characters"], "byte_count": analysis["bytes"],
        "unavailable_document_count": 0, "unavailable_subcontent_count": 0,
        "chunk_target_size": target_size, "chunk_max_size": max_size,
        "builder_version": BUILDER_VERSION, "status": "prepared", "created_at": ingested_at,
    }
    write_jsonl(output_dir / "corpus_documents.jsonl", documents)
    write_jsonl(output_dir / "corpus_chunks.jsonl", chunks)
    write_jsonl(output_dir / "corpus_ingestion_runs.jsonl", [run])
    (output_dir / "corpus_analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: analysis[key] for key in ("run_id", "source_ids", "documents", "chunks", "characters", "corpus_sha256")},
                     ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="合并构建多来源典籍语料")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=Path("data/generated/wikisource-corpus"))
    parser.add_argument("--target-size", type=int, default=DEFAULT_TARGET_SIZE)
    parser.add_argument("--max-size", type=int, default=DEFAULT_MAX_SIZE)
    args = parser.parse_args()
    try:
        build(args.repo_root.resolve(), args.output.resolve(), args.target_size, args.max_size)
    except (OSError, ValueError, RuntimeError) as exc:
        print("classics corpus build failed: {}".format(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
