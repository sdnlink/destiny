"""卦象释义数据源：数据库不可用时必须能回退到仓库内的 JSON。

`_FALLBACK_FILE` 曾按 parents[2] 拼成 backend/data/rules/...（实际文件在仓库根 data/rules），
于是本地无 ClickHouse 时 get_hexagram_explanation 恒为 None，step5 的卦象释义整段消失。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core import hexagram_service


def test_fallback_file_points_at_repository_data():
    path = hexagram_service._FALLBACK_FILE
    assert path.exists(), f"卦象释义回退文件不存在：{path}"
    assert path.parent.name == "rules"


def test_explanation_is_available_without_database(monkeypatch):
    monkeypatch.setattr(hexagram_service.db_repository, "get_hexagram_explanations", lambda *a, **k: [])
    hexagram_service._CACHE = None
    hexagram_service._CACHE_LOADED_AT = 0.0

    record = hexagram_service.get_hexagram_explanation("大有")
    assert record is not None
    assert record["name"] == "大有"
    assert record["summary"]


def test_unknown_hexagram_returns_none(monkeypatch):
    monkeypatch.setattr(hexagram_service.db_repository, "get_hexagram_explanations", lambda *a, **k: [])
    hexagram_service._CACHE = None
    hexagram_service._CACHE_LOADED_AT = 0.0

    assert hexagram_service.get_hexagram_explanation("不存在的卦") is None
