#!/usr/bin/env python3
"""从公开古籍网页（诗词汇、中华典藏等）抓取维基文库缺失的典籍原文。

- 内容为古籍原文（公有领域），逐书记录来源链接与转录许可；
- 输出 cache/web-classics/（texts/ + metadata/ + catalog.json），
  catalog 与 wikisource/daozhige 同 schema，供 build_classics_corpus.py 合并；
- HTML 只提取正文可见文本，剔除导航/脚本/广告。
"""

import argparse
import hashlib
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) DestinyCorpusBuilder/1.0 Chrome/120 Safari/537.36")
LICENSE_NAME = "公有领域（古籍原文网页转录）"
USAGE_SCOPE = "research-attribution-preferred"


class VisibleTextExtractor(HTMLParser):
    """提取 body 内可见文本，跳过脚本样式与导航噪音。"""

    SKIP_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "aside", "form", "iframe"}
    NOISE_MARKERS = ("版权所有", "免责声明", "登录", "注册", "相关推荐", "上一篇", "下一篇",
                     "返回顶部", "扫描二维码", "手机版", "RSS")

    def __init__(self):
        super().__init__()
        self._skip_depth = 0
        self._parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        elif tag in ("p", "br", "div", "h1", "h2", "h3", "h4", "li", "tr"):
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth:
            return
        text = data.strip()
        if not text:
            return
        if any(marker in text for marker in self.NOISE_MARKERS) and len(text) < 60:
            return
        self._parts.append(text + "\n")

    def text(self):
        lines = []
        for line in "".join(self._parts).splitlines():
            stripped = line.strip()
            if stripped:
                lines.append(stripped)
        return "\n".join(lines) + "\n"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def fetch(url, timeout, retries):
    last_error = None
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "zh-CN,zh;q=0.9",
            })
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001 - 下载器需要宽容重试
            last_error = exc
            wait = min(45, 4 * (2 ** attempt))
            print("[retry {}/{}] {} sleep {}s: {}".format(attempt + 1, retries, url[-70:], wait, exc), flush=True)
            time.sleep(wait)
    raise RuntimeError("fetch failed: {} ({})".format(url, last_error))


def extract_text(html):
    parser = VisibleTextExtractor()
    parser.feed(html)
    return parser.text()


def title_slug(title):
    return "web-" + hashlib.sha256(title.encode("utf-8")).hexdigest()[:10]


def main():
    parser = argparse.ArgumentParser(description="抓取公开古籍网页原文")
    parser.add_argument("--manifest", type=Path, default=Path("data/sources/web-classics-books.json"))
    parser.add_argument("--output", type=Path, default=Path("cache/web-classics"))
    parser.add_argument("--only", default=None)
    parser.add_argument("--timeout", type=int, default=45)
    parser.add_argument("--retries", type=int, default=4)
    args = parser.parse_args()

    manifest = json.loads(args.manifest.resolve().read_text(encoding="utf-8"))
    output = args.output.resolve()
    texts_dir = output / "texts"
    metadata_dir = output / "metadata"
    for directory in (texts_dir, metadata_dir):
        directory.mkdir(parents=True, exist_ok=True)

    rows = []
    for index, book in enumerate(manifest["books"], 1):
        if args.only and args.only not in book["title"]:
            continue
        slug = title_slug(book["title"])
        text_path = texts_dir / (slug + ".txt")
        metadata_path = metadata_dir / (slug + ".json")
        sections = []
        try:
            for page in book["pages"]:
                html = fetch(page["url"], args.timeout, args.retries)
                text = extract_text(html)
                if len(text.strip()) < 50:
                    raise ValueError("page too short: {}".format(page["url"]))
                sections.append("# {}\n{}".format(page.get("title", page["url"]), text))
                time.sleep(2.0)
            full_text = "\n\n".join(sections)
            digest = hashlib.sha256(full_text.encode("utf-8")).hexdigest()
            text_path.write_bytes(full_text.encode("utf-8"))
            metadata = {
                "document_id": "webclassic-" + slug,
                "slug": slug,
                "title": book["title"],
                "domain": book["domain"],
                "source_id": manifest["source_id"],
                "source_url": book["pages"][0]["url"],
                "license_name": LICENSE_NAME,
                "usage_scope": USAGE_SCOPE,
                "status": "ok",
                "characters": len(full_text),
                "bytes": text_path.stat().st_size,
                "sha256": digest,
                "page_count": len(sections),
                "pages": [{"title": p.get("title", ""), "url": p["url"]} for p in book["pages"]],
                "fetched_at": utc_now(),
            }
            metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            status = "ok"
        except Exception as exc:  # noqa: BLE001 - 单本失败不阻塞其余
            metadata = {
                "document_id": "webclassic-" + slug, "slug": slug, "title": book["title"],
                "domain": book.get("domain", ""), "source_id": manifest["source_id"],
                "status": "failed", "error": str(exc), "checked_at": utc_now(),
            }
            metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
            status = "failed"
        rows.append(metadata)
        print("{} {}/{}: {}".format(status, index, len(manifest["books"]), book["title"]), flush=True)

    ok_rows = [row for row in rows if row["status"] == "ok"]
    catalog = {
        "source": {"source_id": manifest["source_id"], "display_name": manifest.get("display_name", "")},
        "books": ok_rows,
    }
    (output / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {"books": len(rows), "ok": len(ok_rows),
               "failed": sum(row["status"] == "failed" for row in rows),
               "characters": sum(row.get("characters", 0) for row in ok_rows)}
    (output / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    if summary["failed"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
