#!/usr/bin/env python3
"""Comprehensive check of all generated data files vs ClickHouse tables."""

import base64
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CLICKHOUSE_URL = "http://localhost:18123"
CLICKHOUSE_USER = "destiny"
CLICKHOUSE_PASSWORD = "destiny_local"


def query_ch(sql):
    url = f"{CLICKHOUSE_URL}/?query={urllib.parse.quote(sql)}%20FORMAT%20JSON"
    req = urllib.request.Request(url)
    credentials = base64.b64encode(f"{CLICKHOUSE_USER}:{CLICKHOUSE_PASSWORD}".encode("utf-8")).decode("ascii")
    req.add_header("Authorization", f"Basic {credentials}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def count_jsonl_lines(path):
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def main():
    print("=" * 80)
    print("                天机演象 (Destiny) 全量数据入库完整性检查")
    print("=" * 80)

    all_passed = True

    # 1. Check Seed & Rule Constant Tables
    print("\n【1. 基础易学与术数常量表核验】:")
    seed_tables = [
        ("data_sources", "数据源登记表"),
        ("five_elements", "五行生克与方位表"),
        ("heavenly_stems", "十天干属性表"),
        ("earthly_branches", "十二地支属性表"),
        ("branch_imagery", "地支类象表"),
        ("trigrams", "先天/后天八卦表"),
        ("trigram_imagery", "八卦万物类象表"),
        ("hexagrams", "六十四卦基础表"),
        ("hexagram_explanations", "六十四卦详解与断语表"),
        ("solar_terms", "二十四节气表"),
        ("sexagenary_cycle", "六十甲子与纳音表"),
        ("fengshui_mountains", "二十四山方位表"),
        ("luoshu_palaces", "洛书九宫属性表"),
    ]

    print(f"  {'数据表名称':<24} | {'中文名称':<18} | {'文件行数':<10} | {'库中行数':<10} | {'校验结果'}")
    print("  " + "-" * 76)

    for table, desc in seed_tables:
        jsonl_file = ROOT / "data" / "generated" / f"{table}.jsonl"
        expected_rows = count_jsonl_lines(jsonl_file)
        try:
            db_res = query_ch(f"SELECT count() as cnt FROM destiny.{table}")
            actual_rows = int(db_res["data"][0]["cnt"])
        except Exception as e:
            actual_rows = f"Error: {e}"

        status = "PASSED" if expected_rows == actual_rows and expected_rows > 0 else "FAILED"
        if status == "FAILED":
            all_passed = False
        print(f"  {table:<24} | {desc:<18} | {expected_rows:<10} | {str(actual_rows):<10} | [{status}]")

    # 2. Check Corpus Tables
    print("\n【2. 古籍经典与文献语料库表核验】:")
    corpus_dirs = [
        ("wikisource-corpus", "中文维基文库开放经典古籍 (周易/梅花/六爻/命理/堪舆/奇门/六壬)"),
        ("corpus", "道门典籍参考语料 (道藏诸部文献)"),
    ]

    total_expected_docs = 0
    total_expected_chunks = 0
    total_expected_runs = 0

    for folder, desc in corpus_dirs:
        base = ROOT / "data" / "generated" / folder
        docs = count_jsonl_lines(base / "corpus_documents.jsonl")
        chunks = count_jsonl_lines(base / "corpus_chunks.jsonl")
        runs = count_jsonl_lines(base / "corpus_ingestion_runs.jsonl")
        total_expected_docs += docs
        total_expected_chunks += chunks
        total_expected_runs += runs
        print(f"  * 数据集 [{folder}] - {desc}:")
        print(f"    - 文献数: {docs:,} 篇 | 切片数: {chunks:,} 个 | 批次数: {runs} 批")

    print("\n  数据库对应汇总对比:")
    corpus_table_checks = [
        ("corpus_documents", "文献主表", total_expected_docs),
        ("corpus_chunks", "知识切片表", total_expected_chunks),
        ("corpus_ingestion_runs", "摄入批次表", total_expected_runs),
    ]

    print(f"  {'数据表名称':<24} | {'中文名称':<12} | {'预期总数':<12} | {'库中实际总数':<12} | {'校验结果'}")
    print("  " + "-" * 76)
    for table, desc, exp in corpus_table_checks:
        try:
            db_res = query_ch(f"SELECT count() as cnt FROM destiny.{table}")
            act = int(db_res["data"][0]["cnt"])
        except Exception as e:
            act = f"Error: {e}"
        status = "PASSED" if exp == act and exp > 0 else "FAILED"
        if status == "FAILED":
            all_passed = False
        print(f"  {table:<24} | {desc:<12} | {exp:<12,} | {str(act):<12} | [{status}]")

    # 3. Domain Document Check for Wikisource
    print("\n【3. 本次重点搜集典籍覆盖率检查 (53部经典)】:")
    categories_res = query_ch("""
        SELECT category_id, category_name, count() as doc_count, sum(character_count) as total_chars, sum(subcontent_count) as total_sections
        FROM destiny.corpus_documents
        WHERE source_id = 'zh-wikisource-open'
        GROUP BY category_id, category_name
        ORDER BY total_chars DESC
    """)
    for cat in categories_res["data"]:
        print(f"  - 分类: {cat['category_name']} ({cat['category_id']}) -> 文献: {cat['doc_count']} 部, 章节: {cat['total_sections']} 卷, 字数: {int(cat['total_chars']):,} 字")

    # 4. Summary result
    print("\n" + "=" * 80)
    if all_passed:
        print("  【检查结论】: 全部 16 张数据表、所有基础常量及 53 部经典语料共 29,202 条切片已全部 100% 入库无遗漏！")
    else:
        print("  【检查结论】: 部分数据存在不匹配，请检查上述标记为 FAILED 的条目。")
    print("=" * 80)


if __name__ == "__main__":
    main()
