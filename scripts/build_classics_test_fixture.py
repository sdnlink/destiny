"""生成典籍检索的压缩测试夹具。

完整典籍语料约 20MB，按仓库约定不入库；CI 上没有 ``data/generated/``。
本脚本把测试真正依赖的检索语义抽成 10 条小型文档/段落，写入
``data/validation-cases/classics-fixture/``，供本地与 CI 共用。

夹具只保留可复核的原文片段，不替代真实语料，也不改变生产检索逻辑。
真实语料的规模/清单断言仍由 ``test_classic_grounded_modules.py`` 在完整语料
存在时执行。
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "data" / "validation-cases" / "classics-fixture"

DOCUMENTS = [
    {
        "document_id": "fixture-zengshanbuyi",
        "source_id": "fixture",
        "title": "增刪卜易",
        "category_id": "liuyao",
        "category_name": "六爻",
        "source_url": "https://zh.wikisource.org/wiki/增刪卜易",
        "license_name": "Public Domain",
        "license_url": "https://creativecommons.org/publicdomain/mark/1.0/",
        "character_count": 120,
    },
    {
        "document_id": "fixture-huangjinze",
        "source_id": "fixture",
        "title": "黄金策",
        "category_id": "liuyao",
        "category_name": "六爻",
        "source_url": "https://zh.wikisource.org/wiki/黄金策",
        "license_name": "Public Domain",
        "license_url": "https://creativecommons.org/publicdomain/mark/1.0/",
        "character_count": 80,
    },
    {
        "document_id": "fixture-qimen",
        "source_id": "fixture",
        "title": "奇門遁甲統宗",
        "category_id": "qimen",
        "category_name": "奇门",
        "source_url": "https://zh.wikisource.org/wiki/奇門遁甲統宗",
        "license_name": "Public Domain",
        "license_url": "https://creativecommons.org/publicdomain/mark/1.0/",
        "character_count": 70,
    },
    {
        "document_id": "fixture-bazhai",
        "source_id": "fixture",
        "title": "八宅明鏡",
        "category_id": "yangzhai",
        "category_name": "阳宅",
        "source_url": "https://zh.wikisource.org/wiki/八宅明鏡",
        "license_name": "Public Domain",
        "license_url": "https://creativecommons.org/publicdomain/mark/1.0/",
        "character_count": 100,
    },
    {
        "document_id": "fixture-xuankong",
        "source_id": "fixture",
        "title": "沈氏玄空學",
        "category_id": "kanyu",
        "category_name": "堪舆",
        "source_url": "https://zh.wikisource.org/wiki/沈氏玄空學",
        "license_name": "Public Domain",
        "license_url": "https://creativecommons.org/publicdomain/mark/1.0/",
        "character_count": 110,
    },
    {
        "document_id": "fixture-ziwei",
        "source_id": "fixture",
        "title": "紫微斗數全書",
        "category_id": "ziwei",
        "category_name": "紫微",
        "source_url": "https://zh.wikisource.org/wiki/紫微斗數全書",
        "license_name": "Public Domain",
        "license_url": "https://creativecommons.org/publicdomain/mark/1.0/",
        "character_count": 90,
    },
    {
        "document_id": "fixture-liuren",
        "source_id": "fixture",
        "title": "六壬大全",
        "category_id": "liuren",
        "category_name": "六壬",
        "source_url": "https://zh.wikisource.org/wiki/六壬大全",
        "license_name": "Public Domain",
        "license_url": "https://creativecommons.org/publicdomain/mark/1.0/",
        "character_count": 80,
    },
    {
        "document_id": "fixture-butian",
        "source_id": "fixture",
        "title": "步天歌",
        "category_id": "calendar",
        "category_name": "历法",
        "source_url": "https://zh.wikisource.org/wiki/步天歌",
        "license_name": "Public Domain",
        "license_url": "https://creativecommons.org/publicdomain/mark/1.0/",
        "character_count": 80,
    },
    {
        "document_id": "fixture-sanming",
        "source_id": "fixture",
        "title": "三命通會",
        "category_id": "mingli",
        "category_name": "命理",
        "source_url": "https://zh.wikisource.org/wiki/三命通會",
        "license_name": "Public Domain",
        "license_url": "https://creativecommons.org/publicdomain/mark/1.0/",
        "character_count": 100,
    },
    {
        "document_id": "fixture-huangji",
        "source_id": "fixture",
        "title": "皇極經世",
        "category_id": "xiangshu",
        "category_name": "象数",
        "source_url": "https://zh.wikisource.org/wiki/皇極經世",
        "license_name": "Public Domain",
        "license_url": "https://creativecommons.org/publicdomain/mark/1.0/",
        "character_count": 80,
    },
]

CONTENTS = {
    "fixture-zengshanbuyi": (
        "增刪卜易\n"
        "用神者，所問之事也；元神者，生用神之爻也。\n"
        "三合局者，申子辰合水局，亥卯未合木局，寅午戌合火局，巳酉丑合金局。\n"
        "伏神者，用神不上卦而伏於本宮也；月破者，月建沖爻也。"
    ),
    "fixture-huangjinze": (
        "黄金策\n"
        "用神有真假，動靜有先後；旺相休囚，各以其時。"
    ),
    "fixture-qimen": (
        "奇門遁甲統宗\n"
        "八門：休門、生門、傷門、杜門、景門、死門、驚門、開門。\n"
        "八神：值符、螣蛇、太陰、六合、白虎、玄武、九地、九天。"
    ),
    "fixture-bazhai": (
        "八宅明鏡\n"
        "大遊年歌：乾六天五禍絕延生，坎五天生延絕禍六。\n"
        "遊年歌以伏位為主，按順逆飛布九星。"
    ),
    "fixture-xuankong": (
        "沈氏玄空學\n"
        "挨星、起星、替卦皆以運星入中，按二十四山陰陽順逆飛布。\n"
        "寅午庚丁上，右弼四星臨；中宮五到向，無替可尋。"
    ),
    "fixture-ziwei": (
        "紫微斗數全書\n"
        "太微賦：紫微為帝座，天府為令星；諸星布列十二宮，各有所主。"
    ),
    "fixture-liuren": (
        "六壬大全\n"
        "月将者，正月登明，二月天魁，三月從魁，四月傳送，五月小吉，六月勝光。"
    ),
    "fixture-butian": (
        "步天歌\n"
        "步天歌者，所以紀三垣二十八宿之次舍，便於仰觀也。"
    ),
    "fixture-sanming": (
        "三命通會\n"
        "流年、太歲、大運、行運、月令、提綱、元會運世，皆以干支推之。"
    ),
    "fixture-huangji": (
        "皇極經世\n"
        "元會運世：一元十二會，一會三十運，一運十二世，一世三十年。"
    ),
}


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for document in DOCUMENTS:
        document["character_count"] = len(CONTENTS[document["document_id"]])
    with (OUTPUT_DIR / "corpus_documents.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for document in DOCUMENTS:
            handle.write(json.dumps(document, ensure_ascii=False) + "\n")
    with (OUTPUT_DIR / "corpus_chunks.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for index, document in enumerate(DOCUMENTS):
            content = CONTENTS[document["document_id"]]
            chunk = {
                "chunk_id": "{}:00000".format(document["document_id"]),
                "document_id": document["document_id"],
                "source_id": document["source_id"],
                "title": document["title"],
                "category_id": document["category_id"],
                "chunk_index": 0,
                "char_start": 0,
                "char_end": len(content),
                "character_count": len(content),
                "content": content,
            }
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    print(f"documents={len(DOCUMENTS)} chunks={len(DOCUMENTS)}")


if __name__ == "__main__":
    main()
