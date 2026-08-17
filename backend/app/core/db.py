import base64
import json
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class ClickHouseRepository:
    def __init__(self, url=None, user=None, password=None, timeout=5):
        self.url = (url or os.environ.get("CLICKHOUSE_URL", "http://localhost:18123")).rstrip("/") + "/"
        self.user = user or os.environ.get("CLICKHOUSE_USER", "destiny")
        self.password = password or os.environ.get("CLICKHOUSE_PASSWORD", "destiny_local")
        self.timeout = timeout

    def is_available(self):
        try:
            url = self.url + "ping"
            req = Request(url, method="GET")
            credentials = base64.b64encode(f"{self.user}:{self.password}".encode("utf-8")).decode("ascii")
            req.add_header("Authorization", f"Basic {credentials}")
            with urlopen(req, timeout=1.5) as resp:
                return resp.status == 200 and resp.read().strip() == b"Ok."
        except Exception:
            return False

    def query(self, statement, parameters=None):
        request_parameters = {
            "output_format_json_quote_64bit_integers": "0",
        }
        for key, value in (parameters or {}).items():
            request_parameters[f"param_{key}"] = str(value)
        url = self.url + "?" + urlencode(request_parameters)
        req = Request(url, data=statement.encode("utf-8"), method="POST")
        credentials = base64.b64encode(f"{self.user}:{self.password}".encode("utf-8")).decode("ascii")
        req.add_header("Authorization", f"Basic {credentials}")
        req.add_header("Content-Type", "text/plain; charset=utf-8")
        try:
            with urlopen(req, timeout=self.timeout) as response:
                payload = response.read().decode("utf-8")
            return json.loads(payload)["data"]
        except Exception:
            return None

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

    def get_database_stats(self):
        return self.query("""
            SELECT table, sum(rows) AS rows
            FROM system.parts
            WHERE active AND database = 'destiny'
            GROUP BY table
            ORDER BY table
            FORMAT JSON
        """)


# Global repository instance
db_repository = ClickHouseRepository()
