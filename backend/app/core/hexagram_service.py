"""Hexagram explanation data loader and analyzer."""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, Optional
from app.core.db import db_repository

logger = logging.getLogger("destiny.hexagram_service")

_FALLBACK_FILE = Path(__file__).resolve().parents[2] / "data" / "rules" / "hexagram-explanations.json"

# 缓存带过期时间，且空结果不缓存：
# 之前首载失败会把空字典永久写进缓存，之后即使数据源恢复也永远查不到解释。
_CACHE: Optional[Dict[str, Dict[str, Any]]] = None
_CACHE_LOADED_AT = 0.0
_CACHE_TTL_SECONDS = 300.0


def _load_all() -> Dict[str, Dict[str, Any]]:
    global _CACHE, _CACHE_LOADED_AT
    now = time.monotonic()
    if _CACHE and now - _CACHE_LOADED_AT < _CACHE_TTL_SECONDS:
        return _CACHE

    data_map: Dict[str, Dict[str, Any]] = {}
    db_rows = db_repository.get_hexagram_explanations()
    if db_rows:
        for row in db_rows:
            data_map[row["name"]] = row
            data_map[row["full_name"]] = row
            data_map[str(row["ordinal"])] = row
    elif _FALLBACK_FILE.exists():
        try:
            raw = json.loads(_FALLBACK_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("hexagram explanation fallback unreadable: %s", exc)
            raw = []
        for row in raw:
            data_map[row["name"]] = row
            data_map[row["full_name"]] = row
            data_map[str(row["ordinal"])] = row
    else:
        logger.warning("hexagram explanation fallback file missing: %s", _FALLBACK_FILE)

    if not data_map:
        # 数据源全部失败：不写缓存，下次调用继续重试
        logger.warning("hexagram explanation data is empty, cache not written")
        return data_map

    _CACHE = data_map
    _CACHE_LOADED_AT = now
    return data_map


def get_hexagram_explanation(name_or_ordinal: Any) -> Optional[Dict[str, Any]]:
    """Retrieve full explanation record for a hexagram by name, full name, or ordinal."""
    all_data = _load_all()
    key = str(name_or_ordinal).strip()
    return all_data.get(key)
