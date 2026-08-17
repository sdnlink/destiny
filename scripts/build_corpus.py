#!/usr/bin/env python3
"""Build a deterministic, traceable corpus from the verified text cache."""

import argparse
import hashlib
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from verify_daorenjia_cache import verify


SOURCE_ID = "daorenjia-reference"
USAGE_SCOPE = "internal_research"
BUILDER_VERSION = "1.0.0"
DEFAULT_TARGET_SIZE = 1200
DEFAULT_MAX_SIZE = 1800
BREAK_CHARACTERS = set("\n。！？；.!?;")
CATEGORY_NAMES = {
    "c8": "洞真上清经", "c9": "洞玄灵宝经", "c10": "洞神三皇经", "c11": "三洞经教",
    "c12": "太平部诸经", "c13": "太玄部经诀", "c14": "正一部经籙", "c15": "道德真经",
    "c16": "四子真经", "c17": "黄帝阴符经", "c18": "道教易学", "c19": "太清金丹经",
    "c20": "太清摄养经", "c21": "诸子文集", "c22": "道学论著", "c23": "全真文集",
    "c24": "道教类书", "c25": "道法诸经", "c26": "道法总集", "c27": "科戒威仪",
    "c28": "灵宝诸斋仪", "c29": "灯仪法忏章表", "c30": "神仙高道传", "c31": "仙境名山志",
}
DOMAIN_TERMS = [
    "阴阳", "五行", "八卦", "周易", "易经", "乾坤", "太极", "河图", "洛书", "九宫",
    "天干", "地支", "甲子", "六壬", "梅花易数", "风水", "堪舆", "阳宅", "方位", "卦",
    "道", "德", "气", "神", "仙", "丹", "符", "法", "经", "真",
]


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def clickhouse_datetime(value):
    if not value:
        return None
    return value[:19].replace("T", " ")


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary.replace(path)


def choose_end(text, start, target_size, max_size):
    remaining = len(text) - start
    if remaining <= max_size:
        return len(text)
    target_end = min(start + target_size, len(text))
    max_end = min(start + max_size, len(text))
    minimum_end = min(start + max(1, target_size // 2), max_end)
    for position in range(target_end, max_end):
        if text[position] in BREAK_CHARACTERS:
            return position + 1
    for position in range(target_end - 1, minimum_end - 1, -1):
        if text[position] in BREAK_CHARACTERS:
            return position + 1
    return max_end


def chunk_text(text, target_size=DEFAULT_TARGET_SIZE, max_size=DEFAULT_MAX_SIZE):
    if target_size < 1 or max_size < target_size:
        raise ValueError("chunk sizes must satisfy 1 <= target_size <= max_size")
    chunks = []
    start = 0
    while start < len(text):
        end = choose_end(text, start, target_size, max_size)
        chunks.append((start, end, text[start:end]))
        start = end
    return chunks


def percentile(sorted_values, ratio):
    if not sorted_values:
        return 0
    index = round((len(sorted_values) - 1) * ratio)
    return sorted_values[index]


def is_cjk(character):
    code = ord(character)
    return 0x3400 <= code <= 0x9FFF or 0xF900 <= code <= 0xFAFF


def build(cache_dir, output_dir, target_size, max_size):
    verification = verify(cache_dir)
    if not verification.get("complete"):
        raise RuntimeError("cache verification failed: " + "; ".join(verification.get("errors") or []))

    catalog = json.loads((cache_dir / "catalog.json").read_text(encoding="utf-8"))
    books = catalog["books"]
    ingested_at = utc_now()
    documents = []
    chunks = []
    category_stats = defaultdict(lambda: {"documents": 0, "characters": 0, "bytes": 0, "chunks": 0})
    character_frequency = Counter()
    term_frequency = Counter()
    document_lengths = []
    corpus_digest = hashlib.sha256()

    for book in books:
        slug = book["slug"]
        metadata = json.loads((cache_dir / "metadata" / f"{slug}.json").read_text(encoding="utf-8"))
        raw = (cache_dir / "texts" / f"{slug}.txt").read_bytes()
        text = raw.decode("utf-8")
        category_id = metadata["category"]
        category_name = CATEGORY_NAMES.get(category_id, category_id)
        document_chunks = chunk_text(text, target_size, max_size)
        corpus_digest.update(slug.encode("utf-8"))
        corpus_digest.update(b"\0")
        corpus_digest.update(bytes.fromhex(metadata["sha256"]))

        documents.append({
            "document_id": slug,
            "source_id": SOURCE_ID,
            "title": metadata["title"],
            "category_id": category_id,
            "category_name": category_name,
            "source_url": metadata["url"],
            "fetched_from": metadata.get("fetched_from", ""),
            "cache_status": metadata["status"],
            "usage_scope": USAGE_SCOPE,
            "parser_version": metadata["parser_version"],
            "content_sha256": metadata["sha256"],
            "character_count": metadata["characters"],
            "byte_count": metadata["bytes"],
            "subcontent_count": metadata.get("subcontent_count", 0),
            "available_subcontent_count": metadata.get(
                "available_subcontent_count", metadata.get("subcontent_count", 0)
            ),
            "unavailable_subcontent_ids": metadata.get("unavailable_subcontent_ids", []),
            "fetched_at": clickhouse_datetime(metadata.get("fetched_at")),
            "ingested_at": ingested_at,
        })

        reconstructed = []
        for chunk_index, (char_start, char_end, content) in enumerate(document_chunks):
            reconstructed.append(content)
            chunks.append({
                "chunk_id": f"{slug}:{chunk_index:05d}",
                "document_id": slug,
                "source_id": SOURCE_ID,
                "title": metadata["title"],
                "category_id": category_id,
                "chunk_index": chunk_index,
                "char_start": char_start,
                "char_end": char_end,
                "character_count": len(content),
                "content": content,
                "content_sha256": sha256_bytes(content.encode("utf-8")),
                "document_sha256": metadata["sha256"],
                "usage_scope": USAGE_SCOPE,
                "ingested_at": ingested_at,
            })
        if "".join(reconstructed) != text:
            raise RuntimeError(f"chunk reconstruction failed: {slug}")

        stats = category_stats[category_id]
        stats["name"] = category_name
        stats["documents"] += 1
        stats["characters"] += len(text)
        stats["bytes"] += len(raw)
        stats["chunks"] += len(document_chunks)
        document_lengths.append((len(text), slug, metadata["title"]))
        character_frequency.update(character for character in text if is_cjk(character))
        for term in DOMAIN_TERMS:
            term_frequency[term] += text.count(term)

    lengths = sorted(item[0] for item in document_lengths)
    analysis = {
        "source_id": SOURCE_ID,
        "usage_scope": USAGE_SCOPE,
        "builder_version": BUILDER_VERSION,
        "corpus_sha256": corpus_digest.hexdigest(),
        "created_at": ingested_at,
        "documents": len(documents),
        "chunks": len(chunks),
        "characters": sum(item["character_count"] for item in documents),
        "bytes": sum(item["byte_count"] for item in documents),
        "unavailable_documents": sum(item["cache_status"] == "text_unavailable" for item in documents),
        "unavailable_subcontents": sum(len(item["unavailable_subcontent_ids"]) for item in documents),
        "chunking": {"target_size": target_size, "max_size": max_size, "overlap": 0},
        "document_length": {
            "min": min(lengths), "p25": percentile(lengths, 0.25), "median": statistics.median(lengths),
            "p75": percentile(lengths, 0.75), "p95": percentile(lengths, 0.95), "max": max(lengths),
        },
        "categories": [
            {"category_id": key, **value} for key, value in sorted(category_stats.items())
        ],
        "largest_documents": [
            {"characters": size, "document_id": slug, "title": title}
            for size, slug, title in sorted(document_lengths, reverse=True)[:20]
        ],
        "smallest_documents": [
            {"characters": size, "document_id": slug, "title": title}
            for size, slug, title in sorted(document_lengths)[:20]
        ],
        "top_cjk_characters": [
            {"character": character, "count": count}
            for character, count in character_frequency.most_common(100)
        ],
        "domain_terms": [
            {"term": term, "count": term_frequency[term]}
            for term in DOMAIN_TERMS
        ],
    }

    run_id = f"{SOURCE_ID}:{analysis['corpus_sha256'][:16]}"
    for row in documents:
        row["run_id"] = run_id
    for row in chunks:
        row["run_id"] = run_id
    run = {
        "run_id": run_id,
        "source_id": SOURCE_ID,
        "corpus_sha256": analysis["corpus_sha256"],
        "document_count": analysis["documents"],
        "chunk_count": analysis["chunks"],
        "character_count": analysis["characters"],
        "byte_count": analysis["bytes"],
        "unavailable_document_count": analysis["unavailable_documents"],
        "unavailable_subcontent_count": analysis["unavailable_subcontents"],
        "chunk_target_size": target_size,
        "chunk_max_size": max_size,
        "builder_version": BUILDER_VERSION,
        "status": "prepared",
        "created_at": ingested_at,
    }

    write_jsonl(output_dir / "corpus_documents.jsonl", documents)
    write_jsonl(output_dir / "corpus_chunks.jsonl", chunks)
    write_jsonl(output_dir / "corpus_ingestion_runs.jsonl", [run])
    (output_dir / "corpus_analysis.json").write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"run_id": run_id, **{key: analysis[key] for key in (
        "documents", "chunks", "characters", "bytes", "unavailable_documents",
        "unavailable_subcontents", "corpus_sha256"
    )}}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="构建道人家内部学习语料")
    parser.add_argument("--cache", type=Path, default=Path("cache/daorenjia"))
    parser.add_argument("--output", type=Path, default=Path("data/generated/corpus"))
    parser.add_argument("--target-size", type=int, default=DEFAULT_TARGET_SIZE)
    parser.add_argument("--max-size", type=int, default=DEFAULT_MAX_SIZE)
    args = parser.parse_args()
    try:
        build(args.cache.resolve(), args.output.resolve(), args.target_size, args.max_size)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"corpus build failed: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
