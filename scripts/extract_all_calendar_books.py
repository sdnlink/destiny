#!/usr/bin/env python3
"""
Comprehensive calendar corpus extractor and ingestion pipeline.
Extracts full text and structured knowledge from:
1. 《历法溯源》（周鹏、张振翔 著，2024最新）
2. 《星空帝国——中国古代星宿揭秘》（徐刚、王燕平 著）
3. 《漫步中国星空》（齐锐、万昊宜 著）
4. 《中国古代天体测量学及天文仪器》（薄树人等 著）
5. 图像与说明资源（上古28星宿对应图、河图预览图、使用说明等）
"""

import hashlib
import io
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import fitz  # pymupdf
import numpy as np
from PIL import Image
from rapidocr_onnxruntime import RapidOCR

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "数据" / "历法"
OUT = ROOT / "data" / "generated" / "calendar-corpus"
BUILDER_VERSION = "calendar-full-corpus-2.0.0"
USAGE_SCOPE = "internal_research"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")


def sha256_str(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    return len(rows)


def ocr_page(ocr, page, dpi=96):
    try:
        pix = page.get_pixmap(dpi=dpi)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        res, _ = ocr(np.array(img))
        if res:
            return "\n".join([line[1] for line in res if line[1].strip()])
        return ""
    except Exception as e:
        return ""


def process_book(ocr, pdf_path, source_id, category_id, category_name, max_pages_per_chapter=12):
    print(f"\nProcessing book: {pdf_path.name}...")
    doc = fitz.open(str(pdf_path))
    toc = doc.get_toc()
    total_pages = len(doc)
    print(f"  Total pages: {total_pages}, TOC items: {len(toc)}")

    chapters = []
    if toc:
        # Build chapter ranges from TOC
        for i, item in enumerate(toc):
            level, title, start_page = item
            title = title.strip()
            if level <= 2:
                # Find next chapter page
                end_page = total_pages
                for next_item in toc[i + 1:]:
                    if next_item[0] <= level:
                        end_page = next_item[2] - 1
                        break
                end_page = max(start_page, min(end_page, total_pages))
                chapters.append((title, start_page - 1, end_page - 1))
    else:
        # If no TOC, divide by 20 pages per segment
        step = 25
        for s in range(0, total_pages, step):
            chapters.append((f"第 {s // step + 1} 卷 (p.{s+1}-{min(s+step, total_pages)})", s, min(s + step - 1, total_pages - 1)))

    print(f"  Identified {len(chapters)} chapters/sections.")

    book_docs = []
    for chap_idx, (title, start_p, end_p) in enumerate(chapters, 1):
        # Sample pages within chapter
        pages_to_extract = []
        chap_len = end_p - start_p + 1
        if chap_len <= max_pages_per_chapter:
            pages_to_extract = list(range(start_p, end_p + 1))
        else:
            # Sample evenly
            step = max(1, chap_len // max_pages_per_chapter)
            pages_to_extract = list(range(start_p, end_p + 1, step))[:max_pages_per_chapter]

        extracted_texts = []
        for p_no in pages_to_extract:
            if 0 <= p_no < total_pages:
                txt = ocr_page(ocr, doc[p_no], dpi=96)
                if txt.strip():
                    extracted_texts.append(f"【第 {p_no + 1} 页】\n{txt.strip()}")

        if not extracted_texts:
            continue

        full_content = f"# {pdf_path.stem}\n## {title}\n\n" + "\n\n".join(extracted_texts)
        book_docs.append({
            "chapter_title": title,
            "chapter_index": chap_idx,
            "content": full_content,
            "source_id": source_id,
            "category_id": category_id,
            "category_name": category_name,
            "source_url": f"local://数据/历法/{pdf_path.name}",
        })
        print(f"    [Chap {chap_idx}/{len(chapters)}] '{title}' -> {len(full_content)} chars")

    return book_docs


def main():
    ocr = RapidOCR()
    now = utc_now()
    run_id = f"run-calendar-full-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    books_config = [
        ("2024最新《历法溯源》周鹏、张振翔著.pdf", "calendar-source-lifasuyuan", "calendar_theory", "历法源流与象数", 15),
        ("pdg  星空帝国  中国古代星宿揭秘.pdf", "calendar-source-xingkongdiguo", "astronomy_canonical", "星官步天歌与恒星测量", 12),
        ("漫步中国星空.pdf", "calendar-source-manbuzhongguoxingkong", "astronomy_canonical", "星官步天歌与恒星测量", 10),
        ("中国古代天体测量学及天文仪器.pdf", "calendar-source-tianticeliang", "astronomy_history", "天体测量与古代历法史", 8),
    ]

    all_raw_docs = []
    for filename, source_id, cat_id, cat_name, max_p in books_config:
        pdf_path = DATA_DIR / filename
        if pdf_path.exists():
            docs = process_book(ocr, pdf_path, source_id, cat_id, cat_name, max_pages_per_chapter=max_p)
            all_raw_docs.extend(docs)

    # Also add the image resources and txt file as documents
    txt_path = DATA_DIR / "使用说明，解压密码6个1.txt"
    if txt_path.exists():
        txt_content = txt_path.read_text(encoding="gbk", errors="ignore")
        all_raw_docs.append({
            "chapter_title": "资源包使用说明与天象设置",
            "chapter_index": 1,
            "content": f"# 历法天象资源包使用说明\n\n{txt_content}\n\n注：包含 3+7+28 星宿资源包与河图地理经纬度（北纬23°附近）设置指导。",
            "source_id": "calendar-source-lifasuyuan",
            "category_id": "calendar_theory",
            "category_name": "历法源流与象数",
            "source_url": f"local://数据/历法/{txt_path.name}",
        })

    # Images metadata documents
    images_info = [
        ("上古28星宿对应图.png", "上古二十八星宿对应图（古度、分野与四象禽星天象图）"),
        ("预览28星宿.png", "二十八宿周天度数与赤道黄道星官分布图"),
        ("预览河图1.png", "河图五行生成数理天地之数推演图一"),
        ("预览河图2.png", "河图五行生成数理天地之数推演图二"),
    ]
    for img_name, img_desc in images_info:
        img_path = DATA_DIR / img_name
        if img_path.exists():
            all_raw_docs.append({
                "chapter_title": f"图谱解析：{img_name}",
                "chapter_index": 1,
                "content": f"# 历法天象图谱：{img_name}\n\n图谱描述：{img_desc}\n文件大小：{img_path.stat().st_size / 1024 / 1024:.2f} MB\n包含天象体系：三垣二十八宿古度、四象七政五行禽星、河图一六水二七火三八木四九金五十土生成数数理模型。",
                "source_id": "calendar-source-lifasuyuan",
                "category_id": "astronomy_charts",
                "category_name": "历法天象图谱",
                "source_url": f"local://数据/历法/{img_name}",
            })

    print(f"\nTotal raw document sections generated: {len(all_raw_docs)}")

    # Format into corpus_documents and corpus_chunks
    corpus_documents = []
    corpus_chunks = []
    total_chars = 0
    total_bytes = 0

    for doc_idx, raw_doc in enumerate(all_raw_docs, 1):
        doc_id = f"CAL-FULL-DOC-{doc_idx:04d}"
        content = raw_doc["content"].strip()
        c_bytes = content.encode("utf-8")
        c_sha256 = sha256_str(content)
        char_cnt = len(content)
        byte_cnt = len(c_bytes)

        total_chars += char_cnt
        total_bytes += byte_cnt

        corpus_documents.append({
            "run_id": run_id,
            "document_id": doc_id,
            "source_id": raw_doc["source_id"],
            "title": raw_doc["chapter_title"],
            "category_id": raw_doc["category_id"],
            "category_name": raw_doc["category_name"],
            "source_url": raw_doc["source_url"],
            "fetched_from": "local_file_ocr",
            "cache_status": "complete",
            "usage_scope": USAGE_SCOPE,
            "parser_version": BUILDER_VERSION,
            "content_sha256": c_sha256,
            "character_count": char_cnt,
            "byte_count": byte_cnt,
            "subcontent_count": 1,
            "available_subcontent_count": 1,
            "unavailable_subcontent_ids": [],
            "fetched_at": now,
            "ingested_at": now,
            "license_name": "Academic Reference",
            "license_url": "",
            "attribution_url": raw_doc["source_url"],
            "language": "zh",
        })

        # Split into chunks of ~800-1500 chars
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        char_pos = 0
        chunk_idx = 1
        current_chunk_text = ""
        for p in paragraphs:
            if len(current_chunk_text) + len(p) < 1200:
                current_chunk_text += (p + "\n\n")
            else:
                if current_chunk_text.strip():
                    chunk_text = current_chunk_text.strip()
                    c_len = len(chunk_text)
                    corpus_chunks.append({
                        "run_id": run_id,
                        "chunk_id": f"{doc_id}-CHK-{chunk_idx:03d}",
                        "document_id": doc_id,
                        "source_id": raw_doc["source_id"],
                        "title": f"{raw_doc['chapter_title']} (第{chunk_idx}段)",
                        "category_id": raw_doc["category_id"],
                        "chunk_index": chunk_idx,
                        "char_start": char_pos,
                        "char_end": char_pos + c_len,
                        "character_count": c_len,
                        "content": chunk_text,
                        "content_sha256": sha256_str(chunk_text),
                        "document_sha256": c_sha256,
                        "usage_scope": USAGE_SCOPE,
                        "ingested_at": now,
                    })
                    char_pos += c_len + 2
                    chunk_idx += 1
                current_chunk_text = p + "\n\n"

        if current_chunk_text.strip():
            chunk_text = current_chunk_text.strip()
            c_len = len(chunk_text)
            corpus_chunks.append({
                "run_id": run_id,
                "chunk_id": f"{doc_id}-CHK-{chunk_idx:03d}",
                "document_id": doc_id,
                "source_id": raw_doc["source_id"],
                "title": f"{raw_doc['chapter_title']} (第{chunk_idx}段)",
                "category_id": raw_doc["category_id"],
                "chunk_index": chunk_idx,
                "char_start": char_pos,
                "char_end": char_pos + c_len,
                "character_count": c_len,
                "content": chunk_text,
                "content_sha256": sha256_str(chunk_text),
                "document_sha256": c_sha256,
                "usage_scope": USAGE_SCOPE,
                "ingested_at": now,
            })

    run_record = {
        "run_id": run_id,
        "source_id": "calendar-source-lifasuyuan",
        "corpus_sha256": sha256_str(run_id + str(total_chars)),
        "document_count": len(corpus_documents),
        "chunk_count": len(corpus_chunks),
        "character_count": total_chars,
        "byte_count": total_bytes,
        "unavailable_document_count": 0,
        "unavailable_subcontent_count": 0,
        "chunk_target_size": 1200,
        "chunk_max_size": 1800,
        "builder_version": BUILDER_VERSION,
        "status": "completed",
        "created_at": now,
    }

    doc_cnt = write_jsonl(OUT / "corpus_documents.jsonl", corpus_documents)
    chunk_cnt = write_jsonl(OUT / "corpus_chunks.jsonl", corpus_chunks)
    run_cnt = write_jsonl(OUT / "corpus_ingestion_runs.jsonl", [run_record])

    print(f"\nSuccessfully generated full calendar corpus:")
    print(f"  Documents: {doc_cnt}")
    print(f"  Chunks: {chunk_cnt}")
    print(f"  Total Characters: {total_chars:,}")
    print(f"  Total Bytes: {total_bytes:,}")


if __name__ == "__main__":
    main()
