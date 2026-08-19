#!/usr/bin/env python3
"""
Load schema and seed data into ClickHouse for Tianji Yanxiang.
Works across Windows, Linux, and macOS.
"""
import base64
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CLICKHOUSE_URL = os.environ.get("CLICKHOUSE_URL", "http://localhost:18123").rstrip("/")
CLICKHOUSE_USER = os.environ.get("CLICKHOUSE_USER", "destiny")
CLICKHOUSE_PASSWORD = os.environ.get("CLICKHOUSE_PASSWORD", "destiny_local")

TABLES = [
    "data_sources",
    "five_elements",
    "heavenly_stems",
    "earthly_branches",
    "branch_imagery",
    "trigrams",
    "trigram_imagery",
    "hexagrams",
    "hexagram_explanations",
    "solar_terms",
    "sexagenary_cycle",
    "fengshui_mountains",
    "luoshu_palaces",
]


def make_request(url, data=None, method="GET", content_type="text/plain; charset=utf-8"):
    req = Request(url, data=data, method=method)
    credentials = base64.b64encode(f"{CLICKHOUSE_USER}:{CLICKHOUSE_PASSWORD}".encode("utf-8")).decode("ascii")
    req.add_header("Authorization", f"Basic {credentials}")
    if content_type:
        req.add_header("Content-Type", content_type)
    return req


def wait_for_clickhouse(max_attempts=30):
    print(f"Waiting for ClickHouse at {CLICKHOUSE_URL}...")
    for i in range(1, max_attempts + 1):
        try:
            req = make_request(f"{CLICKHOUSE_URL}/ping")
            with urlopen(req, timeout=2) as resp:
                if resp.status == 200 and resp.read().strip() == b"Ok.":
                    print("ClickHouse is ready!")
                    return True
        except Exception:
            pass
        time.sleep(1)
    print(f"Error: ClickHouse did not become ready after {max_attempts}s", file=sys.stderr)
    return False


def execute_sql_file(sql_file_path):
    print(f"Applying schema from {sql_file_path.name}...")
    content = sql_file_path.read_text(encoding="utf-8")
    statements = [stmt.strip() for stmt in content.split(";") if stmt.strip()]
    for stmt in statements:
        req = make_request(f"{CLICKHOUSE_URL}/", data=stmt.encode("utf-8"), method="POST")
        try:
            with urlopen(req, timeout=10) as resp:
                resp.read()
        except HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            print(f"Warning during SQL execute: {err_body.strip()}", file=sys.stderr)


def load_tables():
    data_dir = ROOT / "data" / "generated"
    for table in TABLES:
        jsonl_path = data_dir / f"{table}.jsonl"
        if not jsonl_path.exists():
            print(f"Skipping {table}: {jsonl_path} does not exist")
            continue

        # Truncate
        truncate_sql = f"TRUNCATE TABLE destiny.{table}"
        req = make_request(f"{CLICKHOUSE_URL}/", data=truncate_sql.encode("utf-8"), method="POST")
        try:
            with urlopen(req, timeout=10) as resp:
                resp.read()
        except Exception as e:
            print(f"Truncate error for {table}: {e}", file=sys.stderr)

        # Insert JSONEachRow
        query_param = quote(f"INSERT INTO destiny.{table} FORMAT JSONEachRow")
        insert_url = f"{CLICKHOUSE_URL}/?query={query_param}"
        data = jsonl_path.read_bytes()
        req = make_request(insert_url, data=data, method="POST", content_type="application/octet-stream")
        try:
            with urlopen(req, timeout=30) as resp:
                resp.read()
            print(f"Loaded {table} from {jsonl_path.name}")
        except Exception as e:
            print(f"Insert error for {table}: {e}", file=sys.stderr)


def load_corpus():
    corpus_dirs = [
        ROOT / "data" / "generated" / "corpus",
        ROOT / "data" / "generated" / "wikisource-corpus",
    ]
    for table in ["corpus_documents", "corpus_chunks", "corpus_ingestion_runs"]:
        truncate_sql = f"TRUNCATE TABLE destiny.{table}"
        req = make_request(f"{CLICKHOUSE_URL}/", data=truncate_sql.encode("utf-8"), method="POST")
        try:
            with urlopen(req, timeout=10) as resp:
                resp.read()
        except Exception as e:
            print(f"Truncate error for {table}: {e}", file=sys.stderr)

    for corpus_dir in corpus_dirs:
        if not corpus_dir.exists():
            continue
        for table in ["corpus_documents", "corpus_chunks", "corpus_ingestion_runs"]:
            jsonl_path = corpus_dir / f"{table}.jsonl"
            if not jsonl_path.exists():
                continue
            query_param = quote(f"INSERT INTO destiny.{table} FORMAT JSONEachRow")
            insert_url = f"{CLICKHOUSE_URL}/?query={query_param}"
            data = jsonl_path.read_bytes()
            req = make_request(insert_url, data=data, method="POST", content_type="application/octet-stream")
            try:
                with urlopen(req, timeout=60) as resp:
                    resp.read()
                print(f"Loaded {table} from {corpus_dir.name}/{jsonl_path.name}")
            except Exception as e:
                print(f"Insert error for {corpus_dir.name}/{table}: {e}", file=sys.stderr)


def print_stats():
    query_param = quote("SELECT table, sum(rows) AS rows FROM system.parts WHERE active AND database = 'destiny' GROUP BY table ORDER BY table FORMAT PrettyCompact")
    req = make_request(f"{CLICKHOUSE_URL}/?query={query_param}", method="GET")
    try:
        with urlopen(req, timeout=10) as resp:
            print("\nDatabase row counts:")
            print(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Failed to query stats: {e}", file=sys.stderr)


def main():
    if not wait_for_clickhouse():
        sys.exit(1)

    schema_file = ROOT / "clickhouse" / "init" / "001_schema.sql"
    if schema_file.exists():
        execute_sql_file(schema_file)

    load_tables()
    load_corpus()
    print_stats()


if __name__ == "__main__":
    main()
