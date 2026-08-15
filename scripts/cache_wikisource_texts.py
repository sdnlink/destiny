#!/usr/bin/env python3
"""Cache an explicit open-license Wikisource book list as traceable plain text."""

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


USER_AGENT = "TianjiYanxiangResearch/1.0 (internal cultural research)"
PARSER_VERSION = "wikisource-api-1.0.0"
BLOCK_TAGS = {"article", "blockquote", "br", "dd", "div", "dl", "dt", "h1", "h2", "h3", "h4", "h5", "h6", "li", "p", "section", "table", "td", "th", "tr"}
SKIP_CLASSES = {"mw-editsection", "ws-noexport", "noprint", "catlinks"}


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def title_slug(title):
    digest = hashlib.sha256(title.encode("utf-8")).hexdigest()[:12]
    readable = re.sub(r"[^0-9A-Za-z\u3400-\u9fff]+", "-", title).strip("-")[:48]
    return "{}-{}".format(readable or "document", digest)


def normalize_text(value):
    lines = []
    blank = False
    for raw_line in value.replace("\r", "").split("\n"):
        line = re.sub(r"[ \t\f\v]+", " ", raw_line).strip()
        if line:
            lines.append(line)
            blank = False
        elif lines and not blank:
            lines.append("")
            blank = True
    return "\n".join(lines).strip() + "\n" if lines else ""


class VisibleTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        classes = set(dict(attrs).get("class", "").split())
        if self.skip_depth or tag in ("script", "style") or classes.intersection(SKIP_CLASSES):
            self.skip_depth += 1
            return
        if tag in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if tag.lower() in BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)

    def text(self):
        return normalize_text("".join(self.parts))


class ApiClient:
    def __init__(self, api_url, delay=1.0, timeout=60, retries=4):
        self.api_url = api_url
        self.delay = delay
        self.timeout = timeout
        self.retries = retries
        self.last_request_at = 0.0

    def request(self, parameters):
        parameters = {**parameters, "format": "json", "formatversion": 2}
        url = self.api_url + "?" + urlencode(parameters)
        last_error = None
        for attempt in range(self.retries + 1):
            wait = self.delay - (time.monotonic() - self.last_request_at)
            if wait > 0:
                time.sleep(wait)
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
            try:
                self.last_request_at = time.monotonic()
                with urlopen(request, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                last_error = exc
                if exc.code not in (429, 500, 502, 503, 504):
                    raise
                retry_after = exc.headers.get("Retry-After")
                pause = int(retry_after) if retry_after and retry_after.isdigit() else min(60, 2 ** attempt)
                time.sleep(pause)
            except (URLError, TimeoutError, ValueError) as exc:
                last_error = exc
                time.sleep(min(60, 2 ** attempt))
        raise last_error


def site_rights(client):
    payload = client.request({"action": "query", "meta": "siteinfo", "siprop": "rightsinfo|general"})
    query = payload["query"]
    return {
        "site_name": query["general"]["sitename"],
        "site_url": query["general"]["base"],
        "license_name": query["rightsinfo"]["text"],
        "license_url": query["rightsinfo"]["url"],
        "captured_at": utc_now(),
    }


def discover_pages(client, root_title):
    pages = []
    continuation = {}
    while True:
        payload = client.request({
            "action": "query", "list": "allpages", "apnamespace": 0,
            "apprefix": root_title + "/", "aplimit": "max", **continuation,
        })
        pages.extend(item["title"] for item in payload["query"]["allpages"])
        if "continue" not in payload:
            break
        continuation = {key: value for key, value in payload["continue"].items() if key != "continue"}
    return [title for title in pages if not title.endswith("/全覽")]


def fetch_page(client, title):
    payload = client.request({
        "action": "query", "prop": "extracts|info|revisions", "titles": title,
        "explaintext": 1, "inprop": "url", "rvprop": "ids|timestamp", "redirects": 1,
    })
    page = payload["query"]["pages"][0]
    if page.get("missing"):
        raise ValueError("page is missing: {}".format(title))
    text = normalize_text(page.get("extract", ""))
    extraction_method = "text-extracts"
    if len(text.strip()) < 20:
        parsed = client.request({"action": "parse", "page": page["title"], "prop": "text"})
        parser = VisibleTextParser()
        parser.feed(parsed["parse"]["text"])
        text = parser.text()
        extraction_method = "rendered-html-visible-text"
    revision = (page.get("revisions") or [{}])[0]
    return {
        "page_id": page["pageid"],
        "title": page["title"],
        "url": page["fullurl"],
        "history_url": page["fullurl"] + "?action=history",
        "revision_id": page.get("lastrevid") or revision.get("revid"),
        "revision_timestamp": revision.get("timestamp"),
        "extraction_method": extraction_method,
        "text": text,
    }


def combine_pages(pages):
    sections = []
    seen = set()
    accepted = []
    for page in pages:
        text = page["text"]
        if len(text.strip()) < 20:
            continue
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        sections.append("# {}\n\n{}".format(page["title"], text.rstrip()))
        accepted.append({key: value for key, value in page.items() if key != "text"})
    text = "\n\n".join(sections).strip() + "\n" if sections else ""
    return text, accepted


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def cache(manifest_path, output_dir, delay, timeout, retries):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    client = ApiClient(manifest["api_url"], delay, timeout, retries)
    rights = site_rights(client)
    if rights["license_url"] != manifest["expected_license_url"]:
        raise RuntimeError("source license changed; review required: {}".format(rights["license_url"]))
    write_json(output_dir / "source.json", {**manifest, "books": None, "rights_snapshot": rights})
    text_dir = output_dir / "texts"
    metadata_dir = output_dir / "metadata"
    rows = []
    for index, book in enumerate(manifest["books"], 1):
        slug = title_slug(book["title"])
        text_path = text_dir / (slug + ".txt")
        metadata_path = metadata_dir / (slug + ".json")
        existing = None
        if metadata_path.exists():
            existing = json.loads(metadata_path.read_text(encoding="utf-8"))
        if existing and existing.get("status") == "ok" and existing.get("parser_version") == PARSER_VERSION and text_path.exists():
            if hashlib.sha256(text_path.read_bytes()).hexdigest() == existing.get("sha256"):
                rows.append(existing)
                print("cached {}/{}: {}".format(index, len(manifest["books"]), book["title"]), flush=True)
                continue
        try:
            subpages = discover_pages(client, book["title"])
            titles = subpages or [book["title"]]
            pages = [fetch_page(client, title) for title in titles]
            text, accepted_pages = combine_pages(pages)
            if len(text.strip()) < 20:
                raise ValueError("no usable plain text returned")
            text_dir.mkdir(parents=True, exist_ok=True)
            temporary = text_path.with_suffix(".txt.tmp")
            temporary.write_text(text, encoding="utf-8")
            temporary.replace(text_path)
            metadata = {
                "document_id": "wikisource-" + slug,
                "slug": slug,
                "title": book["title"],
                "domain": book["domain"],
                "source_id": manifest["source_id"],
                "source_url": "https://zh.wikisource.org/wiki/" + book["title"].replace(" ", "_"),
                "license_name": rights["license_name"],
                "license_url": rights["license_url"],
                "usage_scope": manifest["usage_scope"],
                "status": "ok",
                "parser_version": PARSER_VERSION,
                "characters": len(text),
                "bytes": text_path.stat().st_size,
                "sha256": hashlib.sha256(text_path.read_bytes()).hexdigest(),
                "page_count": len(accepted_pages),
                "pages": accepted_pages,
                "fetched_at": utc_now(),
            }
        except Exception as exc:
            metadata = {
                "document_id": "wikisource-" + slug, "slug": slug, **book,
                "source_id": manifest["source_id"], "status": "failed", "error": str(exc),
                "parser_version": PARSER_VERSION, "checked_at": utc_now(),
            }
        write_json(metadata_path, metadata)
        rows.append(metadata)
        print("{} {}/{}: {}".format(metadata["status"], index, len(manifest["books"]), book["title"]), flush=True)

    summary = {
        "source_id": manifest["source_id"], "updated_at": utc_now(),
        "book_count": len(rows), "cached_books": sum(row["status"] == "ok" for row in rows),
        "failed_books": sum(row["status"] != "ok" for row in rows),
        "characters": sum(row.get("characters", 0) for row in rows),
        "bytes": sum(row.get("bytes", 0) for row in rows),
        "license_name": rights["license_name"], "license_url": rights["license_url"],
    }
    write_json(output_dir / "catalog.json", {"source": {**manifest, "books": None}, "books": rows})
    write_json(output_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if summary["failed_books"]:
        raise RuntimeError("{} books failed".format(summary["failed_books"]))


def main():
    parser = argparse.ArgumentParser(description="缓存中文维基文库开放许可书籍纯文本")
    parser.add_argument("--manifest", type=Path, default=Path("data/sources/wikisource-books.json"))
    parser.add_argument("--output", type=Path, default=Path("cache/wikisource"))
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--retries", type=int, default=4)
    args = parser.parse_args()
    try:
        cache(args.manifest.resolve(), args.output.resolve(), args.delay, args.timeout, args.retries)
    except (OSError, ValueError, RuntimeError, HTTPError, URLError) as exc:
        print("Wikisource cache failed: {}".format(exc))
        raise SystemExit(1)


if __name__ == "__main__":
    main()

