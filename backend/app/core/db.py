import base64
import logging
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.clickhouse_http import ClickHouseHttpClient, ClickHouseRequestError


logger = logging.getLogger("destiny.db")

AVAILABILITY_TTL_SECONDS = 30.0
# 一次失败连接在本机实测要 2–4 秒（探活与查询各自超时、localhost 还要先试 IPv6），
# 而一次 /v1/calculations/compare 会连打三条常量查询：没有失败冷却时，
# 数据库不可达的机器上单个请求要空耗 12 秒，前端 15 秒超时就是这么撞上的。
QUERY_FAILURE_COOLDOWN_SECONDS = 20.0
# 常量表是只读字典数据，一次页面加载会连续打十几个常量端点。
# 没有缓存时每个请求都要新建连接、重新鉴权、重新查表。
CONSTANT_TTL_SECONDS = 120.0


class ClickHouseRepository:
    def __init__(self, url=None, user=None, password=None, timeout=5):
        self.url = (url or os.environ.get("CLICKHOUSE_URL", "http://localhost:18123")).rstrip("/") + "/"
        self.user = user or os.environ.get("CLICKHOUSE_USER", "destiny")
        # 口令只从环境读取：仓库里不再出现第二份默认口令，避免和部署配置漂移
        self.password = password or os.environ.get("CLICKHOUSE_PASSWORD", "")
        if not self.password:
            logger.warning("CLICKHOUSE_PASSWORD 未设置，数据库查询将被拒绝")
        self.timeout = timeout
        self._http = ClickHouseHttpClient(self.url, self.user, self.password, timeout=timeout)
        self._availability = None
        self._availability_checked_at = 0.0
        # 查询失败后的冷却截止时间：期内不再尝试建连，直接走降级路径
        self._failure_until = 0.0
        # 查询结果缓存：常量表是按字典表，重复查同一句 SQL 没必要重复建连接
        self._query_cache = {}

    def is_available(self):
        """带缓存的可用性探测。

        常量端点每个请求都会探测一次，未缓存时数据库不可达要等超时；
        这里缓存 30 秒，避免一次页面加载打出十几个超时。
        localhost 会先试 IPv6 再试 IPv4，实测 1 秒超时约耗 2 秒，所以取 1 秒。
        """
        now = time.monotonic()
        if self._availability is not None and now - self._availability_checked_at < AVAILABILITY_TTL_SECONDS:
            return self._availability
        try:
            url = self.url + "ping"
            req = Request(url, method="GET")
            credentials = base64.b64encode(f"{self.user}:{self.password}".encode("utf-8")).decode("ascii")
            req.add_header("Authorization", f"Basic {credentials}")
            with urlopen(req, timeout=1.0) as resp:
                available = resp.status == 200 and resp.read().strip() == b"Ok."
        except (HTTPError, URLError, OSError, ValueError) as exc:
            logger.info("clickhouse ping failed: %s", exc)
            available = False
        self._availability = available
        self._availability_checked_at = now
        if available:
            # 数据库恢复了：解除查询冷却，下一个请求立刻回到真实数据
            self._failure_until = 0.0
        else:
            self._enter_cooldown()
        return available

    def _enter_cooldown(self):
        self._failure_until = time.monotonic() + QUERY_FAILURE_COOLDOWN_SECONDS

    def query(self, statement, parameters=None, cache_seconds=CONSTANT_TTL_SECONDS):
        """执行只读查询。

        成功结果按 (SQL, 参数) 缓存 `cache_seconds` 秒；失败结果不进结果缓存，
        只进 20 秒的失败冷却 —— 冷却期内重复查询直接返回 None（降级），
        避免每次失败都要重新等一次连接超时。
        需要绝对新鲜度的调用（如库表统计）传 cache_seconds=0。
        """
        if time.monotonic() < self._failure_until:
            return None
        cache_key = (statement, tuple(sorted((parameters or {}).items())))
        if cache_seconds > 0:
            cached = self._query_cache.get(cache_key)
            if cached is not None and time.monotonic() < cached[1]:
                return cached[0]

        try:
            rows = self._http.query(statement, parameters)
        except ClickHouseRequestError as exc:
            if exc.kind == "protocol":
                # 响应不是预期的 FORMAT JSON 结构：这属于代码/查询错误，必须留下痕迹
                logger.error("clickhouse response is not FORMAT JSON: %s", exc)
                return None
            # 网络/鉴权失败：记录原因再返回 None，调用方据此走降级路径；
            # 同时进入冷却期，冷却内不再重复等超时（见 QUERY_FAILURE_COOLDOWN_SECONDS）。
            logger.warning("clickhouse query failed: %s", exc)
            self._enter_cooldown()
            return None
        if cache_seconds > 0 and rows:
            self._query_cache[cache_key] = (rows, time.monotonic() + cache_seconds)
        return rows

    def clear_cache(self):
        """清空查询缓存（测试与人工刷新用）。"""
        self._query_cache.clear()

    def get_trigrams(self):
        return self.query("SELECT * FROM destiny.trigrams ORDER BY earlier_heaven_ordinal FORMAT JSON")

    def get_trigram_imagery(self, trigram_name=None, dimension=None):
        filters = ["1"]
        params = {}
        if trigram_name:
            filters.append("trigram_name = {trigram_name:String}")
            params["trigram_name"] = trigram_name
        if dimension:
            filters.append("dimension = {dimension:String}")
            params["dimension"] = dimension
        where = " AND ".join(filters)
        return self.query(f"""
            SELECT earlier_heaven_ordinal, trigram_name, trigram_symbol, element, dimension, imagery_items, source_id, rule_version
            FROM destiny.trigram_imagery
            WHERE {where}
            ORDER BY earlier_heaven_ordinal, dimension
            FORMAT JSON
        """, params)

    def get_branch_imagery(self, branch_name=None, dimension=None):
        filters = ["1"]
        params = {}
        if branch_name:
            filters.append("branch_name = {branch_name:String}")
            params["branch_name"] = branch_name
        if dimension:
            filters.append("dimension = {dimension:String}")
            params["dimension"] = dimension
        where = " AND ".join(filters)
        return self.query(f"""
            SELECT ordinal, branch_name, dimension, imagery_items, source_id, rule_version
            FROM destiny.branch_imagery
            WHERE {where}
            ORDER BY ordinal, dimension
            FORMAT JSON
        """, params)

    def get_hexagrams(self):
        return self.query("SELECT * FROM destiny.hexagrams ORDER BY king_wen_ordinal FORMAT JSON")

    def get_hexagram_explanations(self, name_or_ordinal=None):
        if name_or_ordinal is not None:
            if isinstance(name_or_ordinal, int):
                return self.query("SELECT * FROM destiny.hexagram_explanations WHERE ordinal = {ordinal:UInt8} FORMAT JSON", {"ordinal": name_or_ordinal})
            return self.query("SELECT * FROM destiny.hexagram_explanations WHERE name = {name:String} OR full_name = {name:String} FORMAT JSON", {"name": str(name_or_ordinal)})
        return self.query("SELECT * FROM destiny.hexagram_explanations ORDER BY ordinal FORMAT JSON")

    def get_five_elements(self):
        return self.query("SELECT * FROM destiny.five_elements FORMAT JSON")

    def get_heavenly_stems(self):
        return self.query("SELECT * FROM destiny.heavenly_stems ORDER BY ordinal FORMAT JSON")

    def get_earthly_branches(self):
        return self.query("SELECT * FROM destiny.earthly_branches ORDER BY ordinal FORMAT JSON")

    def get_solar_terms(self):
        return self.query("SELECT * FROM destiny.solar_terms ORDER BY ordinal FORMAT JSON")

    def get_sexagenary_cycle(self):
        return self.query("SELECT * FROM destiny.sexagenary_cycle ORDER BY ordinal FORMAT JSON")

    def get_fengshui_mountains(self):
        return self.query("SELECT * FROM destiny.fengshui_mountains ORDER BY ordinal FORMAT JSON")

    def get_luoshu_palaces(self):
        return self.query("SELECT * FROM destiny.luoshu_palaces ORDER BY palace_number FORMAT JSON")

    def get_twenty_eight_mansions(self, quadrant=None):
        if quadrant:
            return self.query("SELECT * FROM destiny.twenty_eight_mansions WHERE quadrant = {quadrant:String} ORDER BY ordinal FORMAT JSON", {"quadrant": quadrant})
        return self.query("SELECT * FROM destiny.twenty_eight_mansions ORDER BY ordinal FORMAT JSON")

    def get_three_enclosures(self):
        return self.query("SELECT * FROM destiny.three_enclosures ORDER BY ordinal FORMAT JSON")

    def get_historical_calendars(self, dynasty=None):
        if dynasty:
            return self.query("SELECT * FROM destiny.historical_calendars WHERE dynasty = {dynasty:String} ORDER BY ordinal FORMAT JSON", {"dynasty": dynasty})
        return self.query("SELECT * FROM destiny.historical_calendars ORDER BY ordinal FORMAT JSON")

    def get_hetu_numerology(self, element=None):
        if element:
            return self.query("SELECT * FROM destiny.hetu_numerology WHERE element = {element:String} ORDER BY pair_id FORMAT JSON", {"element": element})
        return self.query("SELECT * FROM destiny.hetu_numerology ORDER BY pair_id FORMAT JSON")

    def get_lunar_phase_regimes(self):
        return self.query("SELECT * FROM destiny.lunar_phase_regimes ORDER BY ordinal FORMAT JSON")

    def get_database_stats(self):
        # 库表统计需要新鲜值，不走缓存
        return self.query("""
            SELECT table, sum(rows) AS rows
            FROM system.parts
            WHERE active AND database = 'destiny'
            GROUP BY table
            ORDER BY table
            FORMAT JSON
        """, cache_seconds=0)


# Global repository instance
db_repository = ClickHouseRepository()

