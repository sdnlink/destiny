"""《沈氏玄空學》起星图「到星 → 入中星」实例的只读解析器。

用途：
- 从 ``data/generated/wikisource-corpus/corpus_chunks.jsonl`` 独立重算
  「216 局 × 山/向 = 432 条」中的可解析实例，生成
  ``data/validation-cases/xuankong-reverse-cases.json``；
- 回归测试读取派生样例，避免把期望表手写死在测试里。

语料是 OCR 转录，存在少量缺行/错字。这里只对**可定位的单字 OCR**
做最小订正（见 ``OCR_CORRECTIONS``），缺行不补、不虚构；解析器会报告
``missing_blocks`` 与 ``invalid_lines``，由测试断言数量。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

CORPUS_PATH = (
    Path(__file__).resolve().parents[3] / "data" / "generated" / "wikisource-corpus" / "corpus_chunks.jsonl"
)

CN_DIGITS = {char: index for index, char in enumerate("一二三四五六七八九", 1)}
MOUNTAIN_CHARS = set("子癸甲申坤壬乙卯未戌乾亥辰巽巳艮丙辛酉丑寅午庚丁")

HEADER_RE = re.compile(r"^\s*([一二三四五六七八九])运(.+?)山(.+?)向兼\s*起星图\s*$")
CASE_RE = re.compile(r"^\s*(?:[一二三四]、)?\s*([一二三四五六七八九])到([向山])")
TARGET_RE = re.compile(r"(?:仍|以|而)([一二三四五六七八九])入中")
SOURCE_RE = re.compile(r"之(?:天元|地元|人元)即([\u4e00-\u9fff]{1,2})")

# 原典 OCR 错字：只订正「到星/入中星」单字，且每条都能由同句源山字义校验。
# 这些行仍保留 original_line，便于逐条回溯，不把订正当成新底本。
OCR_CORRECTIONS = {
    "一、三到向，三之地元即甲，挨贪狼，故不用三而以九入中，庚阳顺行。": 1,
    "一、三到向，三之人元即乙，挨巨门，故不用三而以六入中，乙阴逆行。": 2,
    "二、四到山，四之人元即巳，挨武曲，故不用四而以七入中，巳阳顺行。": 6,
    "二、八到山，八之人元即寅，挨弼星，故不用八而以七入中，寅阳顺行。": 9,
}


def _mountain_from_fragment(fragment: str) -> str:
    for char in fragment:
        if char in MOUNTAIN_CHARS:
            return char
    return ""


def _blocks(content: str) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    current: Dict[str, Any] | None = None
    for line in content.splitlines():
        header = HEADER_RE.match(line)
        if header:
            if current:
                blocks.append(current)
            current = {"header": line.strip(), "body": []}
            continue
        if current is not None and line.strip() and not line.strip().startswith("以上"):
            current["body"].append(line)
    if current:
        blocks.append(current)
    return blocks


def parse_classic_reverse_cases(path: str | Path = CORPUS_PATH) -> Dict[str, Any]:
    """解析起星图实例。

    返回 ``blocks``、``missing_blocks``、``invalid_lines`` 与 ``cases``。
    缺行/无法解析的行不补造，只在元数据中计数，供测试显式断言。
    """
    corpus_path = Path(path)
    if not corpus_path.exists():
        raise FileNotFoundError("典藏语料不存在：{}".format(corpus_path))

    texts: List[str] = []
    with corpus_path.open(encoding="utf-8") as handle:
        for raw in handle:
            row = json.loads(raw)
            if row.get("title") == "沈氏玄空學" and "起星图" in row.get("content", ""):
                texts.append(row["content"])

    blocks = _blocks("\n".join(texts))
    cases: List[Dict[str, Any]] = []
    missing_blocks: List[Dict[str, Any]] = []
    invalid_lines: List[Dict[str, str]] = []

    for block in blocks:
        body = [line for line in block["body"] if CASE_RE.match(line)]
        if len(body) != 2:
            missing_blocks.append({"header": block["header"], "case_lines": len(body)})
        for line in block["body"]:
            match = CASE_RE.match(line)
            if not match:
                continue
            arriving = CN_DIGITS[match.group(1)]
            side = match.group(2)
            original = line.strip()

            if "无替可寻" in line:
                entering = 5
                source = ""
                corrected = False
            else:
                if original in OCR_CORRECTIONS:
                    entering = OCR_CORRECTIONS[original]
                    corrected = True
                else:
                    target_match = TARGET_RE.search(line)
                    if not target_match:
                        invalid_lines.append({"header": block["header"], "line": original})
                        continue
                    entering = CN_DIGITS[target_match.group(1)]
                    corrected = False
                source_match = SOURCE_RE.search(line)
                source = _mountain_from_fragment(source_match.group(1)) if source_match else ""

            cases.append({
                "block": block["header"],
                "side": side,
                "arriving_star": arriving,
                "entering_star": entering,
                "source_mountain": source,
                "ocr_corrected": corrected,
                "original_line": original,
            })

    return {
        "corpus": str(corpus_path),
        "source_title": "沈氏玄空學",
        "blocks": len(blocks),
        "missing_blocks": missing_blocks,
        "invalid_lines": invalid_lines,
        "cases": cases,
    }


def fixture_document(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """把解析结果压成可入库的派生样例（不含 20MB 原始语料）。"""
    cases = parsed["cases"]
    return {
        "schema_version": "1.0",
        "source_title": parsed["source_title"],
        "source_path": "data/generated/wikisource-corpus/corpus_chunks.jsonl",
        "block_count": parsed["blocks"],
        "case_count": len(cases),
        "missing_block_count": len(parsed["missing_blocks"]),
        "invalid_line_count": len(parsed["invalid_lines"]),
        "ocr_corrected_count": sum(1 for case in cases if case["ocr_corrected"]),
        "cases": cases,
    }


__all__ = (
    "CORPUS_PATH",
    "OCR_CORRECTIONS",
    "parse_classic_reverse_cases",
    "fixture_document",
)
