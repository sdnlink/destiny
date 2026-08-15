#!/usr/bin/env python3
"""Internal read-only HTTP API for the verified learning corpus."""

import argparse
import base64
import json
import os
import re
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


DOCUMENT_ID_PATTERN = re.compile(r"^[a-z0-9-]+$")
USAGE_SCOPE = "internal_research"


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def integer_parameter(query, name, default, minimum=0, maximum=100):
    raw = query.get(name, [str(default)])[0]
    try:
        value = int(raw)
    except ValueError:
        raise ApiError(HTTPStatus.BAD_REQUEST, "INVALID_PARAMETER", f"{name} must be an integer")
    if value < minimum or value > maximum:
        raise ApiError(
            HTTPStatus.BAD_REQUEST,
            "INVALID_PARAMETER",
            f"{name} must be between {minimum} and {maximum}",
        )
    return value


def make_snippet(content, term, radius=100):
    position = content.find(term)
    if position < 0:
        return content[: radius * 2], None
    start = max(0, position - radius)
    end = min(len(content), position + len(term) + radius)
    prefix = "…" if start else ""
    suffix = "…" if end < len(content) else ""
    return prefix + content[start:end] + suffix, position


class ClickHouseClient:
    def __init__(self, url, user, password, timeout=30):
        self.url = url.rstrip("/") + "/"
        self.user = user
        self.password = password
        self.timeout = timeout

    def query(self, statement, parameters=None):
        request_parameters = {
            "output_format_json_quote_64bit_integers": "0",
        }
        for key, value in (parameters or {}).items():
            request_parameters[f"param_{key}"] = str(value)
        url = self.url + "?" + urlencode(request_parameters)
        request = Request(url, data=statement.encode("utf-8"), method="POST")
        credentials = base64.b64encode(f"{self.user}:{self.password}".encode("utf-8")).decode("ascii")
        request.add_header("Authorization", f"Basic {credentials}")
        request.add_header("Content-Type", "text/plain; charset=utf-8")
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = response.read().decode("utf-8")
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace").strip()
            raise ApiError(HTTPStatus.BAD_GATEWAY, "CLICKHOUSE_ERROR", detail or str(exc))
        except (URLError, TimeoutError) as exc:
            raise ApiError(HTTPStatus.BAD_GATEWAY, "CLICKHOUSE_UNAVAILABLE", str(exc))
        return json.loads(payload)["data"]


class CorpusRepository:
    def __init__(self, client):
        self.client = client

    def health(self):
        rows = self.client.query(
            "SELECT count() AS documents FROM destiny.corpus_documents FORMAT JSON"
        )
        return {"status": "ok", "documents": rows[0]["documents"], "usage_scope": USAGE_SCOPE}

    def stats(self):
        summary = self.client.query("""
            SELECT
              count() AS documents,
              sum(character_count) AS characters,
              sum(byte_count) AS bytes,
              sum(subcontent_count) AS subcontents,
              sum(length(unavailable_subcontent_ids)) AS unavailable_subcontents,
              countIf(cache_status = 'text_unavailable') AS unavailable_documents
            FROM destiny.corpus_documents
            FORMAT JSON
        """)[0]
        categories = self.client.query("""
            SELECT
              category_id,
              any(category_name) AS category_name,
              count() AS documents,
              sum(character_count) AS characters,
              sum(byte_count) AS bytes
            FROM destiny.corpus_documents
            GROUP BY category_id
            ORDER BY category_id
            FORMAT JSON
        """)
        runs = self.client.query("""
            SELECT * FROM destiny.corpus_ingestion_runs
            ORDER BY created_at DESC LIMIT 1 FORMAT JSON
        """)
        return {**summary, "categories": categories, "latest_run": runs[0] if runs else None}

    def list_documents(self, category, status, title_query, limit, offset):
        filters = ["1"]
        params = {"limit": limit, "offset": offset}
        if category:
            filters.append("category_id = {category:String}")
            params["category"] = category
        if status:
            filters.append("cache_status = {status:String}")
            params["status"] = status
        if title_query:
            filters.append("positionCaseInsensitiveUTF8(title, {title_query:String}) > 0")
            params["title_query"] = title_query
        where = " AND ".join(filters)
        return self.client.query(f"""
            SELECT
              document_id, title, category_id, category_name, cache_status,
              character_count, byte_count, subcontent_count,
              available_subcontent_count, unavailable_subcontent_ids, source_url
            FROM destiny.corpus_documents
            WHERE {where}
            ORDER BY category_id, document_id
            LIMIT {{limit:UInt32}} OFFSET {{offset:UInt32}}
            FORMAT JSON
        """, params)

    def get_document(self, document_id):
        rows = self.client.query("""
            SELECT
              document_id, source_id, title, category_id, category_name, source_url,
              fetched_from, cache_status, usage_scope, parser_version, content_sha256,
              character_count, byte_count, subcontent_count, available_subcontent_count,
              unavailable_subcontent_ids, fetched_at, ingested_at
            FROM destiny.corpus_documents
            WHERE document_id = {document_id:String}
            LIMIT 1 FORMAT JSON
        """, {"document_id": document_id})
        if not rows:
            raise ApiError(HTTPStatus.NOT_FOUND, "DOCUMENT_NOT_FOUND", "document does not exist")
        return rows[0]

    def get_chunks(self, document_id, limit, offset):
        self.get_document(document_id)
        return self.client.query("""
            SELECT
              chunk_id, document_id, title, category_id, chunk_index,
              char_start, char_end, character_count, content, content_sha256,
              document_sha256, usage_scope
            FROM destiny.corpus_chunks
            WHERE document_id = {document_id:String}
            ORDER BY chunk_index
            LIMIT {limit:UInt32} OFFSET {offset:UInt32}
            FORMAT JSON
        """, {"document_id": document_id, "limit": limit, "offset": offset})

    def search(self, term, category, limit):
        filters = ["positionCaseInsensitiveUTF8(c.content, {term:String}) > 0"]
        params = {"term": term, "limit": limit}
        if category:
            filters.append("c.category_id = {category:String}")
            params["category"] = category
        where = " AND ".join(filters)
        rows = self.client.query(f"""
            SELECT
              c.chunk_id, c.document_id, c.title, c.category_id, c.chunk_index,
              c.char_start, c.char_end, c.content, c.content_sha256,
              d.source_url, d.cache_status
            FROM destiny.corpus_chunks AS c
            INNER JOIN destiny.corpus_documents AS d
              ON c.run_id = d.run_id AND c.document_id = d.document_id
            WHERE {where}
            ORDER BY c.document_id, c.chunk_index
            LIMIT {{limit:UInt32}}
            FORMAT JSON
        """, params)
        results = []
        for row in rows:
            snippet, position = make_snippet(row.pop("content"), term)
            row["snippet"] = snippet
            row["match_offset_in_chunk"] = position
            results.append(row)
        return results


def create_handler(repository, token=None):
    class CorpusHandler(BaseHTTPRequestHandler):
        server_version = "TianjiCorpus/0.1"

        def log_message(self, message_format, *args):
            sys.stderr.write("%s - %s\n" % (self.address_string(), message_format % args))

        def send_json(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def require_authorization(self):
            if not token:
                return
            if self.headers.get("Authorization") != f"Bearer {token}":
                raise ApiError(HTTPStatus.UNAUTHORIZED, "UNAUTHORIZED", "valid bearer token required")

        def do_GET(self):
            try:
                self.require_authorization()
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)
                path = parsed.path.rstrip("/") or "/"
                if path == "/health":
                    result = repository.health()
                elif path == "/v1/corpus/stats":
                    result = repository.stats()
                elif path == "/v1/corpus/documents":
                    limit = integer_parameter(query, "limit", 20, 1, 100)
                    offset = integer_parameter(query, "offset", 0, 0, 1000000)
                    result = repository.list_documents(
                        query.get("category", [None])[0],
                        query.get("status", [None])[0],
                        query.get("q", [None])[0],
                        limit,
                        offset,
                    )
                elif path == "/v1/corpus/search":
                    term = query.get("q", [""])[0].strip()
                    if len(term) < 2 or len(term) > 100:
                        raise ApiError(
                            HTTPStatus.BAD_REQUEST,
                            "INVALID_QUERY",
                            "q must contain between 2 and 100 characters",
                        )
                    limit = integer_parameter(query, "limit", 20, 1, 100)
                    result = repository.search(term, query.get("category", [None])[0], limit)
                else:
                    match = re.match(r"^/v1/corpus/documents/([^/]+)(/chunks)?$", path)
                    if not match:
                        raise ApiError(HTTPStatus.NOT_FOUND, "NOT_FOUND", "endpoint does not exist")
                    document_id, chunks_suffix = match.groups()
                    if not DOCUMENT_ID_PATTERN.match(document_id):
                        raise ApiError(HTTPStatus.BAD_REQUEST, "INVALID_DOCUMENT_ID", "invalid document id")
                    if chunks_suffix:
                        limit = integer_parameter(query, "limit", 20, 1, 100)
                        offset = integer_parameter(query, "offset", 0, 0, 1000000)
                        result = repository.get_chunks(document_id, limit, offset)
                    else:
                        result = repository.get_document(document_id)
                self.send_json(HTTPStatus.OK, {"data": result, "usage_scope": USAGE_SCOPE})
            except ApiError as exc:
                self.send_json(exc.status, {"error": {"code": exc.code, "message": exc.message}})
            except Exception:
                self.send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": {"code": "INTERNAL_ERROR", "message": "internal server error"}},
                )

    return CorpusHandler


def main():
    parser = argparse.ArgumentParser(description="启动内部学习语料只读API")
    parser.add_argument("--bind", default=os.environ.get("CORPUS_API_BIND", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("CORPUS_API_PORT", "8088")))
    args = parser.parse_args()
    token = os.environ.get("CORPUS_API_TOKEN")
    if args.bind not in ("127.0.0.1", "localhost", "::1") and not token:
        parser.error("CORPUS_API_TOKEN is required when binding beyond loopback")
    client = ClickHouseClient(
        os.environ.get("CLICKHOUSE_URL", "http://localhost:18123"),
        os.environ.get("CLICKHOUSE_USER", "destiny"),
        os.environ.get("CLICKHOUSE_PASSWORD", "destiny_local"),
    )
    server = ThreadingHTTPServer((args.bind, args.port), create_handler(CorpusRepository(client), token))
    print(f"corpus API listening on http://{args.bind}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
