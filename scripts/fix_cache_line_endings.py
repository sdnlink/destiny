"""修复缓存目录中 Windows 文本模式写入产生的 CRLF，并同步元数据哈希。"""
import hashlib
import json
from pathlib import Path

for root in (Path("cache/open-sources"), Path("cache/web-classics")):
    texts = root / "texts"
    metadata = root / "metadata"
    if not texts.exists():
        continue
    fixed = 0
    for path in sorted(texts.glob("*.txt")):
        raw = path.read_bytes()
        if b"\r\n" not in raw:
            continue
        text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        text = text.strip() + "\n"
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        path.write_bytes(text.encode("utf-8"))
        meta_path = metadata / (path.stem + ".json")
        if meta_path.exists():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["sha256"] = digest
            meta["characters"] = len(text)
            meta["bytes"] = path.stat().st_size
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        # 同步 catalog.json 中的行
        fixed += 1
    catalog = root / "catalog.json"
    if catalog.exists():
        data = json.loads(catalog.read_text(encoding="utf-8"))
        for book in data["books"]:
            p = texts / (book["slug"] + ".txt")
            raw = p.read_bytes()
            book["sha256"] = hashlib.sha256(raw).hexdigest()
            book["characters"] = len(raw.decode("utf-8"))
            book["bytes"] = p.stat().st_size
        catalog.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(root, "fixed", fixed)
