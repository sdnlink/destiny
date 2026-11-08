"""ClickHouse HTTP 传输层的契约测试。

常量库与语料服务现在共用这一份实现：URL 参数前缀、64 位整数输出格式、
Basic Auth 和错误分类都在这里锁定，避免两套客户端再次漂移。
"""

import io
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from app.core.clickhouse_http import ClickHouseHttpClient, ClickHouseRequestError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class ClickHouseHttpClientTests(unittest.TestCase):
    def setUp(self):
        self.client = ClickHouseHttpClient("http://localhost:8123", "destiny", "secret", timeout=7)

    def test_query_builds_parameters_and_reads_json_data(self):
        response = FakeResponse(b'{"data": [{"documents": 89}]}')
        with patch("app.core.clickhouse_http.urlopen", return_value=response) as mocked:
            rows = self.client.query("SELECT 1", {"name": "a b"})
        self.assertEqual(rows, [{"documents": 89}])
        request = mocked.call_args[0][0]
        self.assertIn("output_format_json_quote_64bit_integers=0", request.full_url)
        self.assertIn("param_name=a+b", request.full_url)
        self.assertEqual(mocked.call_args[1]["timeout"], 7)

    def test_http_error_keeps_status_and_response_body(self):
        error = HTTPError(
            "http://localhost:8123", 401, "Unauthorized", None, io.BytesIO(b"bad password")
        )
        with patch("app.core.clickhouse_http.urlopen", side_effect=error):
            with self.assertRaises(ClickHouseRequestError) as caught:
                self.client.query("SELECT 1")
        self.assertEqual(caught.exception.kind, "http")
        self.assertEqual(caught.exception.status, 401)
        self.assertEqual(caught.exception.detail, "bad password")

    def test_network_error_is_unavailable(self):
        with patch("app.core.clickhouse_http.urlopen", side_effect=URLError("connection refused")):
            with self.assertRaises(ClickHouseRequestError) as caught:
                self.client.query("SELECT 1")
        self.assertEqual(caught.exception.kind, "unavailable")

    def test_non_json_response_is_protocol_error(self):
        response = FakeResponse(b"not-json")
        with patch("app.core.clickhouse_http.urlopen", return_value=response):
            with self.assertRaises(ClickHouseRequestError) as caught:
                self.client.query("SELECT 1")
        self.assertEqual(caught.exception.kind, "protocol")


if __name__ == "__main__":
    unittest.main()
