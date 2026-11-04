#!/usr/bin/env python3
"""从公开来源（GitHub 殆知阁古代文献存档等）下载维基文库缺失的古籍纯文本。

设计要点：
- 只抓取古籍原文（内容本身为公有领域），来源与许可逐书记录，便于溯源；
- 输出 cache/open-sources/（texts/ + metadata/ + catalog.json），
  catalog.json 与 wikisource 缓存同 schema，供 build_classics_corpus.py 合并构建语料；
- 支持幂等重跑：文件未变化（size+sha256 一致）时跳过写入。
"""

import argparse
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER_AGENT = "DestinyCorpusBuilder/1.0 (open-source classics; contact: dev@local)"
REPO = "garychowcmu/daizhigev20"
RAW_BASE = "https://raw.githubusercontent.com/{}/master/".format(REPO)
API_URL = "https://api.github.com/repos/{}/git/trees/master".format(REPO)
LICENSE_NAME = "公有领域（古籍原文，殆知阁古代文献 GitHub 存档）"
LICENSE_URL = "https://github.com/{}/".format(REPO)
USAGE_SCOPE = "research-attribution-preferred"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_text(raw_bytes):
    text = raw_bytes.decode("utf-8", errors="replace")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.split("\n")]
    collapsed = []
    for line in lines:
        if line.strip() == "" and (not collapsed or collapsed[-1] == ""):
            continue
        collapsed.append(line)
    return "\n".join(collapsed).strip() + "\n"


def download(url, timeout, retries):
    last_error = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception as exc:  # noqa: BLE001 - 下载器需要宽容重试
            last_error = exc
            wait = min(60, 5 * (2 ** attempt))
            print("[retry {}/{}] {} sleeping {}s: {}".format(
                attempt + 1, retries, url[-60:], wait, exc), flush=True)
            time.sleep(wait)
    raise RuntimeError("download failed: {} ({})".format(url, last_error))


def title_slug(title):
    return "daozhige-" + hashlib.sha256(title.encode("utf-8")).hexdigest()[:10]


def main():
    parser = argparse.ArgumentParser(description="下载开放来源古籍纯文本")
    parser.add_argument("--manifest", type=Path, default=Path("data/sources/open-source-books.json"))
    parser.add_argument("--output", type=Path, default=Path("cache/open-sources"))
    parser.add_argument("--only", default=None, help="只处理标题包含该子串的书")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--retries", type=int, default=5)
    args = parser.parse_args()

    manifest_path = args.manifest.resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output = args.output.resolve()
    texts_dir = output / "texts"
    metadata_dir = output / "metadata"
    for directory in (texts_dir, metadata_dir):
        directory.mkdir(parents=True, exist_ok=True)

    rows = []
    books = manifest["books"]
    for index, book in enumerate(books, 1):
        if args.only and args.only not in book["title"]:
            continue
        slug = title_slug(book["title"])
        text_path = texts_dir / (slug + ".txt")
        metadata_path = metadata_dir / (slug + ".json")
        existing = None
        if metadata_path.exists() and text_path.exists():
            existing = json.loads(metadata_path.read_text(encoding="utf-8"))
        url = RAW_BASE + urllib.parse.quote(book["repo_path"])
        try:
            raw = download(url, args.timeout, args.retries)
            text = normalize_text(raw)
            if len(text.strip()) < 100:
                raise ValueError("text too short: {} chars".format(len(text.strip())))
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if existing and existing.get("sha256") == digest:
                metadata = existing
                status = "cached"
            else:
                text_path.write_bytes(text.encode("utf-8"))
                metadata = {
                    "document_id": "opensource-" + slug,
                    "slug": slug,
                    "title": book["title"],
                    "domain": book["domain"],
                    "source_id": manifest["source_id"],
                    "source_url": "https://github.com/{}/blob/master/{}".format(REPO, book["repo_path"]),
                    "license_name": LICENSE_NAME,
                    "license_url": LICENSE_URL,
                    "usage_scope": USAGE_SCOPE,
                    "status": "ok",
                    "characters": len(text),
                    "bytes": text_path.stat().st_size,
                    "sha256": digest,
                    "fetched_at": utc_now(),
                }
                metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
                status = "ok"
        except Exception as exc:  # noqa: BLE001 - 单本失败不阻塞其余
            metadata = {
                "document_id": "opensource-" + slug, "slug": slug, "title": book["title"],
                "domain": book.get("domain", ""), "source_id": manifest["source_id"],
                "status": "failed", "error": str(exc), "checked_at": utc_now(),
            }
            metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            status = "failed"
        rows.append(metadata)
        print("{} {}/{}: {}".format(status, index, len(books), book["title"]), flush=True)

    ok_rows = [row for row in rows if row["status"] == "ok"]
    catalog = {
        "source": {
            "source_id": manifest["source_id"],
            "display_name": manifest.get("display_name", manifest["source_id"]),
            "api_url": API_URL,
            "manifest": str(manifest_path),
        },
        "books": ok_rows,
    }
    (output / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {
        "books": len(rows), "ok": len(ok_rows),
        "failed": sum(row["status"] == "failed" for row in rows),
        "characters": sum(row.get("characters", 0) for row in ok_rows),
    }
    (output / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    if summary["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
