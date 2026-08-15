#!/usr/bin/env python3
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "generated"
SOURCE = "canonical-traditional-constants-v1"
VERSION = "1.0.0"


def write_jsonl(name, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    return len(rows)


def main():
    source_rows = json.loads((ROOT / "data-sources.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    for row in source_rows:
        row["retrieved_at"] = now if row["access_status"] == "available" else None

    elements = [
        ("木", "火", "土", "东", "春"), ("火", "土", "金", "南", "夏"),
        ("土", "金", "水", "中", "长夏"), ("金", "水", "木", "西", "秋"),
        ("水", "木", "火", "北", "冬"),
    ]
    five_elements = [dict(element=a, generating=b, controlling=c, direction=d,
                          season=e, source_id=SOURCE, rule_version=VERSION)
                     for a, b, c, d, e in elements]

    stem_data = [
        ("甲", "阳", "木", "东"), ("乙", "阴", "木", "东"),
        ("丙", "阳", "火", "南"), ("丁", "阴", "火", "南"),
        ("戊", "阳", "土", "中"), ("己", "阴", "土", "中"),
        ("庚", "阳", "金", "西"), ("辛", "阴", "金", "西"),
        ("壬", "阳", "水", "北"), ("癸", "阴", "水", "北"),
    ]
    stems = [dict(ordinal=i, name=n, polarity=p, element=e, direction=d,
                  source_id=SOURCE, rule_version=VERSION)
             for i, (n, p, e, d) in enumerate(stem_data, 1)]

    branch_data = [
        ("子", "阳", "水", "鼠", 11, 23, "北", ["癸"]),
        ("丑", "阴", "土", "牛", 12, 1, "东北", ["己", "癸", "辛"]),
        ("寅", "阳", "木", "虎", 1, 3, "东北", ["甲", "丙", "戊"]),
        ("卯", "阴", "木", "兔", 2, 5, "东", ["乙"]),
        ("辰", "阳", "土", "龙", 3, 7, "东南", ["戊", "乙", "癸"]),
        ("巳", "阴", "火", "蛇", 4, 9, "东南", ["丙", "戊", "庚"]),
        ("午", "阳", "火", "马", 5, 11, "南", ["丁", "己"]),
        ("未", "阴", "土", "羊", 6, 13, "西南", ["己", "丁", "乙"]),
        ("申", "阳", "金", "猴", 7, 15, "西南", ["庚", "壬", "戊"]),
        ("酉", "阴", "金", "鸡", 8, 17, "西", ["辛"]),
        ("戌", "阳", "土", "狗", 9, 19, "西北", ["戊", "辛", "丁"]),
        ("亥", "阴", "水", "猪", 10, 21, "西北", ["壬", "甲"]),
    ]
    branches = [dict(ordinal=i, name=n, polarity=p, element=e, zodiac=z,
                     lunar_month=m, hour_start=h, direction=d, hidden_stems=hs,
                     source_id=SOURCE, rule_version=VERSION)
                for i, (n, p, e, z, m, h, d, hs) in enumerate(branch_data, 1)]

    trigram_data = [
        ("乾", "☰", "111", "金", "西北", "父"), ("兑", "☱", "110", "金", "西", "少女"),
        ("离", "☲", "101", "火", "南", "中女"), ("震", "☳", "100", "木", "东", "长男"),
        ("巽", "☴", "011", "木", "东南", "长女"), ("坎", "☵", "010", "水", "北", "中男"),
        ("艮", "☶", "001", "土", "东北", "少男"), ("坤", "☷", "000", "土", "西南", "母"),
    ]
    trigrams = [dict(earlier_heaven_ordinal=i, name=n, symbol=s, binary_code=b,
                     element=e, direction_later_heaven=d, family_role=f,
                     source_id=SOURCE, rule_version=VERSION)
                for i, (n, s, b, e, d, f) in enumerate(trigram_data, 1)]

    hexagram_names = (
        "乾 坤 屯 蒙 需 讼 师 比 小畜 履 泰 否 同人 大有 谦 豫 随 蛊 临 观 噬嗑 贲 剥 复 "
        "无妄 大畜 颐 大过 坎 离 咸 恒 遁 大壮 晋 明夷 家人 睽 蹇 解 损 益 夬 姤 萃 升 困 "
        "井 革 鼎 震 艮 渐 归妹 丰 旅 巽 兑 涣 节 中孚 小过 既济 未济"
    ).split()
    hexagrams = [dict(king_wen_ordinal=i, name=name, symbol=chr(0x4DBF + i),
                      unicode_codepoint=f"U+{0x4DBF + i:04X}", source_id=SOURCE,
                      rule_version=VERSION)
                 for i, name in enumerate(hexagram_names, 1)]

    term_names = "立春 雨水 惊蛰 春分 清明 谷雨 立夏 小满 芒种 夏至 小暑 大暑 立秋 处暑 白露 秋分 寒露 霜降 立冬 小雪 大雪 冬至 小寒 大寒".split()
    seasons = (["春"] * 6) + (["夏"] * 6) + (["秋"] * 6) + (["冬"] * 6)
    longitudes = [315, 330, 345, 0, 15, 30, 45, 60, 75, 90, 105, 120,
                  135, 150, 165, 180, 195, 210, 225, 240, 255, 270, 285, 300]
    terms = [dict(ordinal=i, name=n, solar_longitude=l, season=s,
                  source_id=SOURCE, rule_version=VERSION)
             for i, (n, l, s) in enumerate(zip(term_names, longitudes, seasons), 1)]

    nayin_pairs = "海中金 炉中火 大林木 路旁土 剑锋金 山头火 涧下水 城头土 白蜡金 杨柳木 泉中水 屋上土 霹雳火 松柏木 长流水 沙中金 山下火 平地木 壁上土 金箔金 覆灯火 天河水 大驿土 钗钏金 桑柘木 大溪水 沙中土 天上火 石榴木 大海水".split()
    stem_names = [row[0] for row in stem_data]
    branch_names = [row[0] for row in branch_data]
    cycles = []
    for idx in range(60):
        stem, branch = stem_names[idx % 10], branch_names[idx % 12]
        cycles.append(dict(ordinal=idx + 1, name=stem + branch, stem=stem,
                           branch=branch, nayin=nayin_pairs[idx // 2],
                           source_id=SOURCE, rule_version=VERSION))

    mountain_data = [
        ("子", "地支", "坎", "水", "北"), ("癸", "天干", "坎", "水", "北"),
        ("丑", "地支", "艮", "土", "东北"), ("艮", "八卦", "艮", "土", "东北"),
        ("寅", "地支", "艮", "木", "东北"), ("甲", "天干", "震", "木", "东"),
        ("卯", "地支", "震", "木", "东"), ("乙", "天干", "震", "木", "东"),
        ("辰", "地支", "巽", "土", "东南"), ("巽", "八卦", "巽", "木", "东南"),
        ("巳", "地支", "巽", "火", "东南"), ("丙", "天干", "离", "火", "南"),
        ("午", "地支", "离", "火", "南"), ("丁", "天干", "离", "火", "南"),
        ("未", "地支", "坤", "土", "西南"), ("坤", "八卦", "坤", "土", "西南"),
        ("申", "地支", "坤", "金", "西南"), ("庚", "天干", "兑", "金", "西"),
        ("酉", "地支", "兑", "金", "西"), ("辛", "天干", "兑", "金", "西"),
        ("戌", "地支", "乾", "土", "西北"), ("乾", "八卦", "乾", "金", "西北"),
        ("亥", "地支", "乾", "水", "西北"), ("壬", "天干", "坎", "水", "北"),
    ]
    mountains = []
    for idx, (name, category, trigram, element, direction) in enumerate(mountain_data):
        center = idx * 15.0
        mountains.append(dict(
            ordinal=idx + 1, name=name, center_degree=center,
            start_degree=(center - 7.5) % 360, end_degree=(center + 7.5) % 360,
            category=category, trigram=trigram, element=element, direction=direction,
            source_id=SOURCE, rule_version=VERSION,
        ))

    luoshu_data = [
        (1, "一白", "坎", "北", "水", "中男"),
        (2, "二黑", "坤", "西南", "土", "母"),
        (3, "三碧", "震", "东", "木", "长男"),
        (4, "四绿", "巽", "东南", "木", "长女"),
        (5, "五黄", "", "中", "土", "中宫"),
        (6, "六白", "乾", "西北", "金", "父"),
        (7, "七赤", "兑", "西", "金", "少女"),
        (8, "八白", "艮", "东北", "土", "少男"),
        (9, "九紫", "离", "南", "火", "中女"),
    ]
    luoshu = [dict(palace_number=n, name=name, trigram=t, direction=d,
                   element=e, family_role=f, source_id=SOURCE, rule_version=VERSION)
              for n, name, t, d, e, f in luoshu_data]

    counts = {
        "data_sources": write_jsonl("data_sources", source_rows),
        "five_elements": write_jsonl("five_elements", five_elements),
        "heavenly_stems": write_jsonl("heavenly_stems", stems),
        "earthly_branches": write_jsonl("earthly_branches", branches),
        "trigrams": write_jsonl("trigrams", trigrams),
        "hexagrams": write_jsonl("hexagrams", hexagrams),
        "solar_terms": write_jsonl("solar_terms", terms),
        "sexagenary_cycle": write_jsonl("sexagenary_cycle", cycles),
        "fengshui_mountains": write_jsonl("fengshui_mountains", mountains),
        "luoshu_palaces": write_jsonl("luoshu_palaces", luoshu),
    }
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
