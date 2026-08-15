#!/usr/bin/env python3
"""Verify that the daorenjia text cache is complete and internally consistent."""

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


EXPECTED_PARSER_VERSION = "1.2.0"
COMPLETE_STATUSES = {"ok", "text_unavailable"}


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify(cache_dir):
    errors = []
    warnings = []
    catalog_path = cache_dir / "catalog.json"
    metadata_dir = cache_dir / "metadata"
    text_dir = cache_dir / "texts"
    if not catalog_path.exists():
        return {"complete": False, "errors": ["catalog.json is missing"], "warnings": []}

    catalog = load_json(catalog_path)
    books = catalog.get("books") or []
    slugs = [book.get("slug") for book in books]
    slug_set = set(slugs)
    if len(slugs) != len(slug_set):
        errors.append("catalog contains duplicate slugs")
    if catalog.get("book_count") != len(books):
        errors.append("catalog book_count does not match books length")

    totals = {
        "book_count": len(books),
        "cached_books": 0,
        "text_unavailable_books": 0,
        "characters": 0,
        "bytes": 0,
        "subcontents": 0,
    }
    unavailable = []
    seen_subcontents = set()

    for book in books:
        slug = book.get("slug")
        metadata_path = metadata_dir / f"{slug}.json"
        text_path = text_dir / f"{slug}.txt"
        if not metadata_path.exists():
            errors.append(f"{slug}: metadata missing")
            continue
        try:
            metadata = load_json(metadata_path)
        except (OSError, ValueError) as exc:
            errors.append(f"{slug}: invalid metadata: {exc}")
            continue

        status = metadata.get("status")
        if status not in COMPLETE_STATUSES:
            errors.append(f"{slug}: incomplete status {status!r}")
            continue
        if metadata.get("parser_version") != EXPECTED_PARSER_VERSION:
            errors.append(f"{slug}: parser version is not {EXPECTED_PARSER_VERSION}")
        if metadata.get("slug") != slug or metadata.get("url") != book.get("url"):
            errors.append(f"{slug}: metadata identity does not match catalog")
        if not metadata.get("title"):
            errors.append(f"{slug}: title is empty")
        if not text_path.exists():
            errors.append(f"{slug}: text file missing")
            continue

        raw = text_path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            errors.append(f"{slug}: text is not valid UTF-8: {exc}")
            continue
        if metadata.get("bytes") != len(raw):
            errors.append(f"{slug}: byte count mismatch")
        if metadata.get("characters") != len(text):
            errors.append(f"{slug}: character count mismatch")
        if metadata.get("sha256") != sha256(text_path):
            errors.append(f"{slug}: SHA-256 mismatch")

        subcontent_ids = metadata.get("subcontent_ids") or []
        if len(subcontent_ids) != len(set(subcontent_ids)):
            errors.append(f"{slug}: duplicate subcontent ids")
        if metadata.get("subcontent_count") != len(subcontent_ids):
            errors.append(f"{slug}: subcontent count mismatch")
        for subcontent_id in subcontent_ids:
            key = (slug, str(subcontent_id))
            if key in seen_subcontents:
                errors.append(f"{slug}: repeated subcontent {subcontent_id}")
            seen_subcontents.add(key)

        if status == "ok":
            totals["cached_books"] += 1
            if len(text.strip()) < 20:
                errors.append(f"{slug}: successful text is unexpectedly short")
        else:
            totals["text_unavailable_books"] += 1
            unavailable.append({"slug": slug, "title": metadata.get("title"), "text": text.strip()})
            if "图片版" not in text:
                warnings.append(f"{slug}: unavailable marker does not mention 图片版")

        totals["characters"] += len(text)
        totals["bytes"] += len(raw)
        totals["subcontents"] += len(subcontent_ids)

    metadata_slugs = {path.stem for path in metadata_dir.glob("*.json")}
    text_slugs = {path.stem for path in text_dir.glob("*.txt")}
    for extra in sorted(metadata_slugs - slug_set):
        warnings.append(f"extra metadata file: {extra}")
    for extra in sorted(text_slugs - slug_set):
        warnings.append(f"extra text file: {extra}")
    for missing in sorted(slug_set - text_slugs):
        errors.append(f"missing text file: {missing}")

    complete_count = totals["cached_books"] + totals["text_unavailable_books"]
    if complete_count != totals["book_count"]:
        errors.append(
            f"complete book count {complete_count} does not equal catalog count {totals['book_count']}"
        )

    return {
        "complete": not errors,
        "verified_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        **totals,
        "unavailable": unavailable,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description="校验道人家书籍文本缓存")
    parser.add_argument("--cache", type=Path, default=Path("cache/daorenjia"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = verify(args.cache.resolve())
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    raise SystemExit(0 if report["complete"] else 1)


if __name__ == "__main__":
    main()
