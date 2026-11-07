"""常量端点的来源声明。

数据库不可达时曾经返回「数据库来源 + 空数组」，前端据此认为"表拉到了但没数据"。
现在每种来源都必须写清楚，且不可达时必须带 warning。

`/v1/constants/hexagram-explanations` 有两级回退：数据库 → 本地 rule 文件缓存
（`source: file_cache`），所以来源取值多一个合法项。
"""

import unittest

from fastapi.testclient import TestClient

from app.main import app

CONSTANT_PATHS = (
    "/v1/constants/trigrams",
    "/v1/constants/trigram-imagery",
    "/v1/constants/hexagrams",
    "/v1/constants/hexagram-explanations",
    "/v1/constants/five-elements",
    "/v1/constants/stems",
    "/v1/constants/branches",
    "/v1/constants/solar-terms",
    "/v1/constants/sexagenary-cycle",
    "/v1/constants/fengshui-mountains",
    "/v1/constants/luoshu-palaces",
    "/v1/constants/twenty-eight-mansions",
    "/v1/constants/three-enclosures",
    "/v1/constants/historical-calendars",
    "/v1/constants/hetu-numerology",
    "/v1/constants/lunar-phases",
)

SOURCES = {"clickhouse_database", "in_memory_fallback", "unavailable", "file_cache"}


class ConstantEndpointSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_every_constant_endpoint_declares_its_source(self):
        for path in CONSTANT_PATHS:
            body = self.client.get(path).json()
            self.assertIn("source", body, f"{path} 未声明数据来源")
            self.assertIn(body["source"], SOURCES, f"{path} 的来源取值非法：{body['source']}")

    def test_unavailable_source_is_explicit(self):
        for path in CONSTANT_PATHS:
            body = self.client.get(path).json()
            if body["source"] != "unavailable":
                continue
            self.assertEqual(body["data"], [], f"{path} 声明不可达却返回了数据")
            self.assertTrue(body.get("warning"), f"{path} 声明不可达却没有 warning")


if __name__ == "__main__":
    unittest.main()
