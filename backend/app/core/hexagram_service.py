"""Hexagram explanation data loader and analyzer."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.db import db_repository

_FALLBACK_FILE = Path(__file__).resolve().parents[2] / "data" / "rules" / "hexagram-explanations.json"
_CACHE: Optional[Dict[str, Dict[str, Any]]] = None


def _load_all() -> Dict[str, Dict[str, Any]]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    data_map: Dict[str, Dict[str, Any]] = {}
    db_rows = db_repository.get_hexagram_explanations()
    if db_rows:
        for row in db_rows:
            data_map[row["name"]] = row
            data_map[row["full_name"]] = row
            data_map[str(row["ordinal"])] = row
    elif _FALLBACK_FILE.exists():
        raw = json.loads(_FALLBACK_FILE.read_text(encoding="utf-8"))
        for row in raw:
            data_map[row["name"]] = row
            data_map[row["full_name"]] = row
            data_map[str(row["ordinal"])] = row

    _CACHE = data_map
    return data_map


def get_hexagram_explanation(name_or_ordinal: Any) -> Optional[Dict[str, Any]]:
    """Retrieve full explanation record for a hexagram by name, full name, or ordinal."""
    all_data = _load_all()
    key = str(name_or_ordinal).strip()
    return all_data.get(key)
