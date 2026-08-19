#!/usr/bin/env python3
"""Generate expanded manifest for all discovered classical books."""

import json
from pathlib import Path

MANIFEST_BOOKS = [
    # 周易经传与注疏 (Zhouyi)
    {"title": "周易", "domain": "zhouyi"},
    {"title": "易傳", "domain": "zhouyi"},
    {"title": "周易正義", "domain": "zhouyi"},
    {"title": "周易正義 (四庫全書本)", "domain": "zhouyi"},
    {"title": "子夏易傳", "domain": "zhouyi"},
    {"title": "周易集解", "domain": "zhouyi"},
    {"title": "周易集解 (四庫全書本)", "domain": "zhouyi"},
    {"title": "周易本義 (四庫全書本)", "domain": "zhouyi"},
    {"title": "周易鄭康成註", "domain": "zhouyi"},
    {"title": "周易參同契", "domain": "zhouyi"},
    {"title": "周易參同契分章通真義", "domain": "zhouyi"},

    # 象数与易纬 (Xiangshu)
    {"title": "易學象數論", "domain": "xiangshu"},
    {"title": "皇極經世", "domain": "xiangshu"},
    {"title": "皇極經世書 (四庫全書本)", "domain": "xiangshu"},
    {"title": "乾坤鑿度", "domain": "xiangshu"},
    {"title": "易緯稽覽圖 (四庫全書本)", "domain": "xiangshu"},
    {"title": "易緯通卦驗 (四庫全書本)", "domain": "xiangshu"},
    {"title": "太玄經", "domain": "xiangshu"},
    {"title": "潛虛", "domain": "xiangshu"},
    {"title": "太極圖說", "domain": "xiangshu"},
    {"title": "通書", "domain": "xiangshu"},
    {"title": "正蒙", "domain": "xiangshu"},

    # 梅花易数 (Meihua)
    {"title": "梅花易數", "domain": "meihua"},

    # 六爻与卜筮 (Liuyao)
    {"title": "增刪卜易", "domain": "liuyao"},
    {"title": "卜筮正宗（河潞武子龄校本）", "domain": "liuyao"},
    {"title": "火珠林", "domain": "liuyao"},
    {"title": "京氏易傳", "domain": "liuyao"},
    {"title": "焦氏易林", "domain": "liuyao"},
    {"title": "靈棋經", "domain": "liuyao"},
    {"title": "靈棋經 (四庫全書本)", "domain": "liuyao"},
    {"title": "欽定古今圖書集成/博物彙編/藝術典/卜筮部", "domain": "liuyao"},

    # 命理与相术 (Mingli / Xiangshu_ming)
    {"title": "淵海子平", "domain": "mingli"},
    {"title": "三命通會", "domain": "mingli"},
    {"title": "滴天髓", "domain": "mingli"},
    {"title": "滴天髓闡微", "domain": "mingli"},
    {"title": "神機妙算達摩一掌經", "domain": "mingli"},
    {"title": "人倫大統賦", "domain": "xiangshu_ming"},
    {"title": "月波洞中記", "domain": "xiangshu_ming"},
    {"title": "欽定古今圖書集成/博物彙編/藝術典/星命部", "domain": "mingli"},
    {"title": "欽定古今圖書集成/博物彙編/藝術典/相術部", "domain": "xiangshu_ming"},

    # 奇门与六壬 (Qimen / Liuren)
    {"title": "六壬大全", "domain": "liuren"},
    {"title": "六壬指南", "domain": "liuren"},
    {"title": "遁甲演義", "domain": "qimen"},
    {"title": "鬼谷子", "domain": "qimen"},

    # 堪舆与阳宅 (Kanyu / Yangzhai)
    {"title": "宅經", "domain": "yangzhai"},
    {"title": "葬書", "domain": "kanyu"},
    {"title": "撼龍經", "domain": "kanyu"},
    {"title": "青囊經", "domain": "kanyu"},
    {"title": "青囊奧語", "domain": "kanyu"},
    {"title": "青囊序", "domain": "kanyu"},
    {"title": "地理辨正", "domain": "kanyu"},
    {"title": "催官篇 (四庫全書本)", "domain": "kanyu"},
    {"title": "欽定古今圖書集成/博物彙編/藝術典/堪輿部", "domain": "kanyu"},
]


def main():
    root = Path(__file__).resolve().parents[1]
    manifest = {
        "schema_version": "1.0",
        "source_id": "zh-wikisource-open",
        "source_name": "中文维基文库",
        "api_url": "https://zh.wikisource.org/w/api.php",
        "expected_license_url": "https://creativecommons.org/licenses/by-sa/4.0/deed.zh",
        "usage_scope": "open_licensed_research",
        "books": MANIFEST_BOOKS,
    }
    target_path = root / "data" / "sources" / "wikisource-books.json"
    target_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {target_path} with {len(MANIFEST_BOOKS)} books.")


if __name__ == "__main__":
    main()
