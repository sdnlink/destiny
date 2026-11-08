"""ClickHouse HTTP 传输层。

常量库（`app.core.db`）与独立语料服务（`app.corpus_api`）原先各自拼
URL、Basic Auth 和 JSON 解析；两套代码对 64 位整数、参数前缀、错误体
的处理曾经不一致。这里只保留唯一一份传输实现，调用方各自决定失败后
是降级返回 None，还是映射成 502。
"""

import base64
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ClickHouseRequestError(Exception):
    """一次 ClickHouse HTTP 请求失败；kind 区分可重试网络错误与协议错误。"""

    def __init__(self, kind, message, status=None, detail=""):
        super().__init__(message)
        self.kind = kind
        self.status = status
        self.detail = detail


class ClickHouseHttpClient:
    def __init__(self, url, user, password, timeout=5):
        self.url = url.rstrip("/") + "/"
        self.user = user
        self.password = password
        self.timeout = timeout

    def query(self, statement, parameters=None):
        """执行只读 SQL，返回 FORMAT JSON 的 data 数组。"""
        request_parameters = {"output_format_json_quote_64bit_integers": "0"}
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
            raise ClickHouseRequestError(
                "http", detail or str(exc), status=exc.code, detail=detail
            ) from exc
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise ClickHouseRequestError("unavailable", str(exc)) from exc
        try:
            return json.loads(payload)["data"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise ClickHouseRequestError("protocol", f"响应不是预期的 FORMAT JSON: {exc}") from exc
