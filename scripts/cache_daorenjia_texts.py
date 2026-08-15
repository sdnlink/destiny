#!/usr/bin/env python3
"""Cache book text from daorenjia.com with rate limiting and resume support."""

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser


BASE_URL = "https://www.daorenjia.com/"
USER_AGENT = "TianjiYanxiang-TextCache/0.1"
BOOK_PATH = re.compile(r"^/?daozang\d+-\d+/?$")
CATEGORY_PATH = re.compile(r"^/?c\d+/?$")


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href.strip())


class BookParser(HTMLParser):
    BLOCK_TAGS = {"p", "br", "div", "table", "tr", "li", "h1", "h2", "h3", "h4"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts = []
        self.text_parts = []
        self.in_title = False
        self.content_depth = 0
        self.found_content = False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        attr_map = dict(attrs)
        if tag == "title":
            self.in_title = True
        if tag == "div" and attr_map.get("id") == "content4":
            self.content_depth = 1
            self.found_content = True
            return
        if self.content_depth:
            if tag == "div":
                self.content_depth += 1
            if tag in self.BLOCK_TAGS:
                self.text_parts.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == "title":
            self.in_title = False
        if self.content_depth:
            if tag in self.BLOCK_TAGS:
                self.text_parts.append("\n")
            if tag == "div":
                self.content_depth -= 1

    def handle_data(self, data):
        if self.in_title:
            self.title_parts.append(data)
        if self.content_depth:
            self.text_parts.append(data)

    def result(self):
        raw_title = "".join(self.title_parts).strip()
        title = re.sub(r"\s*在线阅读\s*$", "", raw_title)
        lines = []
        for line in "".join(self.text_parts).splitlines():
            cleaned = re.sub(r"[ \t\r\f\v]+", " ", line).strip()
            if cleaned:
                lines.append(cleaned)
        return title, "\n".join(lines) + "\n"


class Fetcher:
    def __init__(self, delay, timeout, retries):
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self.last_request_at = 0.0

    def get(self, url):
        wait = self.delay - (time.monotonic() - self.last_request_at)
        if wait > 0:
            time.sleep(wait)
        last_error = None
        for attempt in range(self.retries + 1):
            try:
                request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,text/plain"})
                self.last_request_at = time.monotonic()
                with urlopen(request, timeout=self.timeout) as response:
                    content_type = response.headers.get("Content-Type", "")
                    body = response.read()
                return body.decode("utf-8", errors="replace"), content_type
            except HTTPError as exc:
                last_error = exc
                if exc.code in (404, 410):
                    raise
                retry_after = exc.headers.get("Retry-After")
                time.sleep(float(retry_after) if retry_after and retry_after.isdigit() else 2 ** attempt)
            except (URLError, TimeoutError) as exc:
                last_error = exc
                time.sleep(2 ** attempt)
        raise last_error


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_links(html):
    parser = LinkParser()
    parser.feed(html)
    return parser.links


def same_site_path(href):
    absolute = urljoin(BASE_URL, href)
    parsed = urlparse(absolute)
    if parsed.netloc not in ("www.daorenjia.com", "daorenjia.com"):
        return None
    return parsed.path.strip("/")


def discover(fetcher, robots):
    home, _ = fetcher.get(BASE_URL)
    categories = set()
    for href in parse_links(home):
        path = same_site_path(href)
        if path and CATEGORY_PATH.match(path):
            categories.add(path)

    books = {}
    for index, category in enumerate(sorted(categories, key=lambda value: int(value[1:])), 1):
        url = urljoin(BASE_URL, category)
        if not robots.can_fetch(USER_AGENT, url):
            continue
        html, _ = fetcher.get(url)
        count_before = len(books)
        for href in parse_links(html):
            path = same_site_path(href)
            if path and BOOK_PATH.match(path):
                books[path] = {"slug": path, "url": urljoin(BASE_URL, path), "category": category}
        print(f"discovered {category}: +{len(books) - count_before} books ({index}/{len(categories)})", flush=True)
    return [books[key] for key in sorted(books)]


def load_metadata(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def cache_book(book, fetcher, robots, text_dir, metadata_dir, force=False):
    text_path = text_dir / f"{book['slug']}.txt"
    metadata_path = metadata_dir / f"{book['slug']}.json"
    existing = load_metadata(metadata_path)
    if not force and existing and existing.get("status") == "ok" and text_path.exists():
        digest = hashlib.sha256(text_path.read_bytes()).hexdigest()
        if existing.get("sha256") == digest:
            return existing, "cached"

    if not robots.can_fetch(USER_AGENT, book["url"]):
        return {**book, "status": "robots_denied", "checked_at": utc_now()}, "failed"

    try:
        html, content_type = fetcher.get(book["url"])
        if "html" not in content_type.lower():
            raise ValueError(f"unexpected content type: {content_type}")
        parser = BookParser()
        parser.feed(html)
        title, text = parser.result()
        if not parser.found_content or len(text.strip()) < 20:
            raise ValueError("book text container missing or empty")
        text_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = text_path.with_suffix(".txt.tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(text_path)
        metadata = {
            **book,
            "title": title,
            "status": "ok",
            "characters": len(text),
            "bytes": text_path.stat().st_size,
            "sha256": hashlib.sha256(text_path.read_bytes()).hexdigest(),
            "fetched_at": utc_now(),
            "parser_version": "1.0.0",
        }
        write_json(metadata_path, metadata)
        return metadata, "downloaded"
    except Exception as exc:
        metadata = {**book, "status": "failed", "error": str(exc), "checked_at": utc_now()}
        write_json(metadata_path, metadata)
        return metadata, "failed"


def build_manifest(catalog, metadata_dir, output_path):
    records = []
    for book in catalog:
        metadata = load_metadata(metadata_dir / f"{book['slug']}.json")
        records.append(metadata or {**book, "status": "pending"})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = output_path.with_suffix(".jsonl.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    temporary.replace(output_path)
    return records


def load_catalog(path):
    value = load_metadata(path)
    if not value or value.get("source") != BASE_URL or not isinstance(value.get("books"), list):
        raise ValueError(f"invalid catalog: {path}")
    return value["books"]


def load_robots(fetcher, cache_path):
    try:
        text, _ = fetcher.get(urljoin(BASE_URL, "robots.txt"))
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(text, encoding="utf-8")
    except Exception:
        if not cache_path.exists():
            raise
        text = cache_path.read_text(encoding="utf-8")
        print("using cached robots.txt because the source is unavailable", flush=True)
    robots = RobotFileParser(urljoin(BASE_URL, "robots.txt"))
    robots.parse(text.splitlines())
    return robots


def write_summary(records, output, run_totals, interrupted=False):
    ok_records = [record for record in records if record.get("status") == "ok"]
    failed_records = [record for record in records if record.get("status") in ("failed", "robots_denied")]
    pending_records = [record for record in records if record.get("status") == "pending"]
    summary = {
        "source": BASE_URL,
        "updated_at": utc_now(),
        "book_count": len(records),
        "cached_books": len(ok_records),
        "failed_books": len(failed_records),
        "pending_books": len(pending_records),
        "characters": sum(record.get("characters", 0) for record in ok_records),
        "bytes": sum(record.get("bytes", 0) for record in ok_records),
        "interrupted": interrupted,
        **run_totals,
    }
    write_json(output / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description="缓存道人家书籍正文纯文本")
    parser.add_argument("--output", type=Path, default=Path("cache/daorenjia"))
    parser.add_argument("--delay", type=float, default=1.0, help="每次请求的最小间隔秒数")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--discover-only", action="store_true")
    parser.add_argument("--reuse-catalog", action="store_true", help="复用现有catalog.json，续传时避免重新扫描分类")
    parser.add_argument("--manifest-only", action="store_true", help="离线重建部分清单和统计，不发送网络请求")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--max-consecutive-failures", type=int, default=5,
                        help="连续失败达到该数量时自动暂停")
    args = parser.parse_args()
    if args.delay < 0.5:
        parser.error("--delay must be at least 0.5 seconds")
    if args.max_consecutive_failures < 1:
        parser.error("--max-consecutive-failures must be at least 1")

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.manifest_only:
        catalog = load_catalog(output / "catalog.json")
        records = build_manifest(catalog, output / "metadata", output / "manifest.jsonl")
        write_summary(records, output, {"downloaded": 0, "cached": 0, "failed": 0}, interrupted=True)
        return

    fetcher = Fetcher(args.delay, args.timeout, args.retries)
    robots = load_robots(fetcher, output / "robots.txt")

    catalog_path = output / "catalog.json"
    if args.reuse_catalog:
        catalog = load_catalog(catalog_path)
    else:
        catalog = discover(fetcher, robots)
        write_json(catalog_path, {
            "source": BASE_URL,
            "discovered_at": utc_now(),
            "book_count": len(catalog),
            "books": catalog,
        })
    print(f"catalog contains {len(catalog)} books", flush=True)
    if args.discover_only:
        return

    text_dir = output / "texts"
    metadata_dir = output / "metadata"
    totals = {"downloaded": 0, "cached": 0, "failed": 0}
    interrupted = False
    consecutive_failures = 0
    try:
        for index, book in enumerate(catalog, 1):
            _, state = cache_book(book, fetcher, robots, text_dir, metadata_dir, args.force)
            totals[state] += 1
            print(f"{state} {book['slug']} ({index}/{len(catalog)})", flush=True)
            if state == "failed":
                consecutive_failures += 1
                if consecutive_failures >= args.max_consecutive_failures:
                    interrupted = True
                    print(f"paused after {consecutive_failures} consecutive failures", flush=True)
                    break
            elif state == "downloaded":
                consecutive_failures = 0
    except KeyboardInterrupt:
        interrupted = True
        print("cache interrupted; writing partial manifest", flush=True)

    records = build_manifest(catalog, metadata_dir, output / "manifest.jsonl")
    summary = write_summary(records, output, totals, interrupted)
    if interrupted:
        raise SystemExit(130)
    if summary["failed_books"] or summary["pending_books"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
