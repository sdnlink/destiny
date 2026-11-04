"""规范化 JSON 与摘要的唯一实现。

此前 main.py、session/models.py、core/registry.py 各写了一份
「sort_keys + separators + sha256」，三份口径只要有一处改动（例如换了分隔符），
任务 ID、快照指纹、规则校验和就会互相对不上。统一到这里。
"""

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def canonical_digest(value: Any) -> str:
    return "sha256:" + canonical_hash(value)
