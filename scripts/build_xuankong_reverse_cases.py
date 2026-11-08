"""从本地典籍语料重建玄空起星图派生样例。

用法（仓库根目录）：
    python scripts/build_xuankong_reverse_cases.py

原始语料 ``data/generated/`` 不入库；本脚本把可解析的 430 条实例写进
``data/validation-cases/xuankong-reverse-cases.json``，供 CI 回归读取。
语料不存在时直接失败，避免静默生成空样例。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.fengshui.classic_reverse import fixture_document, parse_classic_reverse_cases

OUTPUT = ROOT / "data" / "validation-cases" / "xuankong-reverse-cases.json"


def main() -> int:
    parsed = parse_classic_reverse_cases()
    document = fixture_document(parsed)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "wrote {}: blocks={} cases={} missing={} invalid={} ocr={}".format(
            OUTPUT,
            document["block_count"],
            document["case_count"],
            document["missing_block_count"],
            document["invalid_line_count"],
            document["ocr_corrected_count"],
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
