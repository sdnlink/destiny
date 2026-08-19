#!/usr/bin/env python3
"""Verify ingested corpus and domain statistics in ClickHouse."""

import base64
import json
import urllib.parse
import urllib.request


def query_ch(sql):
    url = f"http://localhost:18123/?query={urllib.parse.quote(sql)}%20FORMAT%20JSON"
    req = urllib.request.Request(url)
    credentials = base64.b64encode(b"destiny:destiny_local").decode("ascii")
    req.add_header("Authorization", f"Basic {credentials}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))["data"]


def main():
    print("==================================================================")
    print("              ClickHouse 易学/术数/周易语料库入库统计             ")
    print("==================================================================")

    # 1. Total statistics
    runs = query_ch("SELECT run_id, source_id, document_count, chunk_count, character_count, byte_count FROM destiny.corpus_ingestion_runs")
    print("\n【语料库摄入批次 (Ingestion Runs)】:")
    for r in runs:
        print(f"  - 来源: {r['source_id']:<20} | 批次ID: {r['run_id']}")
        print(f"    文献数: {int(r['document_count']):<6} | 切片数: {int(r['chunk_count']):<6} | 总字数: {int(r['character_count']):,}")

    # 2. Wikisource domain breakdown
    cats = query_ch("""
        SELECT category_id, category_name, count() AS doc_count, sum(character_count) AS total_chars, sum(subcontent_count) AS total_sections
        FROM destiny.corpus_documents
        WHERE source_id = 'zh-wikisource-open'
        GROUP BY category_id, category_name
        ORDER BY total_chars DESC
    """)
    print("\n【中文维基文库开放经典古籍分类分布】:")
    print(f"  {'分类ID':<15} | {'分类名':<10} | {'书目数':<8} | {'总章节数':<10} | {'总字数':<12}")
    print("  " + "-" * 64)
    total_docs = 0
    total_chars = 0
    for c in cats:
        d_cnt = int(c['doc_count'])
        c_cnt = int(c['total_chars'])
        s_cnt = int(c['total_sections'])
        total_docs += d_cnt
        total_chars += c_cnt
        print(f"  {c['category_id']:<15} | {c['category_name']:<10} | {d_cnt:<8} | {s_cnt:<10} | {c_cnt:,}")
    print("  " + "-" * 64)
    print(f"  {'合计':<15} | {'全部经典':<10} | {total_docs:<8} | {'-':<10} | {total_chars:,}")

    # 3. Sample search in new collections
    print("\n【典籍检索验证】:")
    test_terms = ["梅花易數", "納甲", "體卦", "用卦", "六爻", "世爻", "青囊", "撼龍", "子平", "遁甲", "六壬"]
    for term in test_terms:
        res = query_ch(f"""
            SELECT count() AS chunk_hits, count(DISTINCT title) AS doc_hits
            FROM destiny.corpus_chunks
            WHERE source_id = 'zh-wikisource-open' AND content LIKE '%{term}%'
        """)[0]
        print(f"  - 关键词「{term}」: 命中 {res['doc_hits']} 部典籍中的 {res['chunk_hits']} 个知识切片")


if __name__ == "__main__":
    main()
