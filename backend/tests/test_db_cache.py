"""ClickHouse 只读查询的缓存行为测试。

常量端点一次页面加载会连打十几个，每个请求都重新建连接、重新鉴权、重新查表
是不可接受的；但缓存又不能让一次瞬时故障把整个 TTL 都锁在降级路径上。
这里同时钉住这两条性质。
"""

import json
import unittest
from unittest import mock
from urllib.error import URLError

from app.core import db as db_module


class _FakeResponse:
    status = 200

    def __init__(self, payload):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False


class QueryCacheTests(unittest.TestCase):
    def setUp(self):
        self.repo = db_module.ClickHouseRepository(password="test-password")

    def test_identical_queries_hit_network_once(self):
        rows = [{"number": 1, "name": "乾"}]
        payload = json.dumps({"data": rows}).encode("utf-8")
        with mock.patch.object(db_module, "urlopen", return_value=_FakeResponse(payload)) as opener:
            first = self.repo.get_trigrams()
            second = self.repo.get_trigrams()
        self.assertEqual(opener.call_count, 1, "同一条只读查询不应重复建连接")
        self.assertEqual(first, rows)
        self.assertEqual(second, rows)

    def test_different_parameters_do_not_share_cache(self):
        payload = json.dumps({"data": [{"trigram_name": "乾"}]}).encode("utf-8")
        with mock.patch.object(db_module, "urlopen", return_value=_FakeResponse(payload)) as opener:
            self.repo.get_trigram_imagery(trigram_name="乾")
            self.repo.get_trigram_imagery(trigram_name="坎")
        self.assertEqual(opener.call_count, 2)

    def test_failures_are_not_cached(self):
        with mock.patch.object(db_module, "urlopen", side_effect=URLError("boom")) as opener:
            self.assertIsNone(self.repo.get_trigrams())
            # 失败会进入 20 秒冷却，冷却期内重复查询不再建连（降级不重试）
            self.assertIsNone(self.repo.get_trigrams())
        self.assertEqual(opener.call_count, 1, "冷却期内不应重复尝试建连")

    def test_failed_query_does_not_cache_rows(self):
        self.repo._failure_until = 0.0
        payload = json.dumps({"data": [{"number": 1}]}).encode("utf-8")
        with mock.patch.object(db_module, "urlopen", side_effect=URLError("boom")):
            self.assertIsNone(self.repo.get_trigrams())
        self.assertEqual(self.repo._query_cache, {}, "失败的查询不能写进结果缓存")
        # 数据库恢复（探活成功）后必须立刻回到真实数据，而不是继续吃旧的失败结论
        self.repo._failure_until = 0.0
        with mock.patch.object(db_module, "urlopen", return_value=_FakeResponse(payload)):
            self.assertEqual(self.repo.get_trigrams(), [{"number": 1}])

    def test_successful_ping_clears_cooldown(self):
        self.repo._enter_cooldown()
        ping_payload = b"Ok.\n"
        with mock.patch.object(db_module, "urlopen", return_value=_FakeResponse(ping_payload)):
            self.assertTrue(self.repo.is_available())
        self.assertEqual(self.repo._failure_until, 0.0, "数据库恢复后冷却必须解除")

    def test_failed_ping_enters_cooldown(self):
        with mock.patch.object(db_module, "urlopen", side_effect=URLError("boom")):
            self.assertFalse(self.repo.is_available())
        self.assertGreater(self.repo._failure_until, 0.0, "探活失败也应进入冷却，避免后续查询继续空等超时")

    def test_stats_query_bypasses_cache(self):
        payload = json.dumps({"data": [{"table": "trigrams", "rows": 8}]}).encode("utf-8")
        with mock.patch.object(db_module, "urlopen", return_value=_FakeResponse(payload)) as opener:
            self.repo.get_database_stats()
            self.repo.get_database_stats()
        self.assertEqual(opener.call_count, 2, "库表统计需要新鲜值，不应被缓存")

    def test_clear_cache_forces_refetch(self):
        payload = json.dumps({"data": [{"number": 1}]}).encode("utf-8")
        with mock.patch.object(db_module, "urlopen", return_value=_FakeResponse(payload)) as opener:
            self.repo.get_five_elements()
            self.repo.clear_cache()
            self.repo.get_five_elements()
        self.assertEqual(opener.call_count, 2)

    def test_empty_result_is_not_cached(self):
        payload = json.dumps({"data": []}).encode("utf-8")
        with mock.patch.object(db_module, "urlopen", return_value=_FakeResponse(payload)) as opener:
            self.repo.get_five_elements()
            self.repo.get_five_elements()
        self.assertEqual(opener.call_count, 2, "空表结果不缓存，避免把一次异常空响应当成稳态")


if __name__ == "__main__":
    unittest.main()
