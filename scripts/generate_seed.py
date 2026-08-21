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

    trigram_imagery_config = json.loads((ROOT / "data" / "rules" / "trigram-imagery.json").read_text(encoding="utf-8"))["imagery"]
    branch_imagery_config = json.loads((ROOT / "data" / "rules" / "branch-imagery.json").read_text(encoding="utf-8"))["imagery"]

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
    branches = []
    branch_imagery_rows = []
    for i, (n, p, e, z, m, h, d, hs) in enumerate(branch_data, 1):
        bimg = branch_imagery_config.get(n, {})
        branches.append(dict(
            ordinal=i, name=n, polarity=p, element=e, zodiac=z,
            lunar_month=m, hour_start=h, direction=d, hidden_stems=hs,
            directions=bimg.get("方位", []),
            nature=bimg.get("自然", []),
            seasons=bimg.get("时令", []),
            objects=bimg.get("事物", []),
            source_id=SOURCE, rule_version=VERSION,
        ))
        for dimension, items in bimg.items():
            branch_imagery_rows.append(dict(
                ordinal=i,
                branch_name=n,
                dimension=dimension,
                imagery_items=items,
                source_id=SOURCE,
                rule_version=VERSION,
            ))

    trigram_data = [
        ("乾", "☰", "111", "金", "西北", "父"), ("兑", "☱", "110", "金", "西", "少女"),
        ("离", "☲", "101", "火", "南", "中女"), ("震", "☳", "100", "木", "东", "长男"),
        ("巽", "☴", "011", "木", "东南", "长女"), ("坎", "☵", "010", "水", "北", "中男"),
        ("艮", "☶", "001", "土", "东北", "少男"), ("坤", "☷", "000", "土", "西南", "母"),
    ]
    trigrams = []
    trigram_imagery_rows = []
    for i, (n, s, b, e, d, f) in enumerate(trigram_data, 1):
        img = trigram_imagery_config.get(n, {})
        trigrams.append(dict(
            earlier_heaven_ordinal=i, name=n, symbol=s, binary_code=b,
            element=e, direction_later_heaven=d, family_role=f,
            essence=img.get("象意", []),
            natural_phenomena=img.get("自然", []),
            persons=img.get("人物", []),
            family_members=img.get("家庭", []),
            body_parts=img.get("身体", []),
            animals=img.get("动物", []),
            objects=img.get("事物", []),
            places=img.get("场所", []),
            actions=img.get("行为", []),
            colors=img.get("色彩", []),
            foods=img.get("饮食", []),
            illnesses=img.get("疾病", []),
            source_id=SOURCE, rule_version=VERSION,
        ))
        for dimension, items in img.items():
            trigram_imagery_rows.append(dict(
                earlier_heaven_ordinal=i,
                trigram_name=n,
                trigram_symbol=s,
                element=e,
                dimension=dimension,
                imagery_items=items,
                source_id=SOURCE,
                rule_version=VERSION,
            ))

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

    hexagram_exp_raw = json.loads((ROOT / "data" / "rules" / "hexagram-explanations.json").read_text(encoding="utf-8"))
    hexagram_explanations = []
    for item in hexagram_exp_raw:
        row = dict(item)
        row["source_id"] = SOURCE
        row["rule_version"] = VERSION
        hexagram_explanations.append(row)

    # 二十八宿全维度定义（源自《历法溯源》、《星空帝国》、《漫步中国星空》及步天歌）
    mansion_data = [
        # 东方苍龙七宿
        (1, "角", "东方苍龙", "角木蛟", "木", "蛟", "木", 12.0, 12.0, "室女座α (Spica)", 2, "辰", "180°-192°", "吉",
         "南北两星正直悬，中有平道上天田。天门两扇当关立，左右摄提引万年。",
         ["天门", "春生", "青龙之角", "农耕播种", "将领统率", "纲纪秩序"]),
        (2, "亢", "东方苍龙", "亢金龙", "金", "龙", "金", 9.0, 9.5, "室女座κ", 4, "辰", "192°-201°", "凶",
         "四星恰似大朝槎，直立苍龙第二家。大角一星天帝座，天庭纲纪重权加。",
         ["天庭之府", "朝廷纲纪", "文教礼仪", "青龙之咽喉", "裁决审理"]),
        (3, "氐", "东方苍龙", "氐土貉", "土", "貉", "土", 15.0, 16.0, "天秤座α (Zubenelgenubi)", 4, "卯", "201°-216°", "凶",
         "四星似斗侧量天，青龙之腹近天泉。亢宿之后氐当路，后宫路寝息神全。",
         ["天根", "路寝", "休养受纳", "青龙之胸腹", "承接生息"]),
        (4, "房", "东方苍龙", "房日兔", "日", "兔", "火", 5.0, 5.5, "天蝎座π", 4, "卯", "216°-221°", "吉",
         "四星形若竖双门，日月所经天帝存。左角右角分明在，天驷明堂福泽繁。",
         ["天府", "天驷", "天子明堂", "日月经纬", "青龙之腹胁", "吉庆集聚"]),
        (5, "心", "东方苍龙", "心月狐", "月", "狐", "火", 5.0, 5.0, "天蝎座σ (Al Niyat)", 3, "卯", "221°-226°", "凶",
         "三星中央大火红，天王明堂威令崇。前星后星夹太子，荧惑守心警兆通。",
         ["大火", "天王本位", "君王心志", "青龙之心", "威严决断"]),
        (6, "尾", "东方苍龙", "尾火虎", "火", "虎", "火", 18.0, 19.0, "天蝎座μ", 9, "寅", "226°-244°", "吉",
         "九星勾曲似龙尾，后宫嫔妃九子随。江河入海波涛涌，万物繁衍福禄绥。",
         ["后宫嗣绪", "继绝立嗣", "江河之渊", "青龙之尾", "繁衍昌盛"]),
        (7, "箕", "东方苍龙", "箕水豹", "水", "豹", "水", 11.0, 10.5, "人马座γ (Alnasl)", 4, "寅", "244°-255°", "吉",
         "四星如箕簸扬风，口向东方接岁功。八风之本司风雨，受纳五谷万仓隆。",
         ["天鸡司晨", "风伯", "八风之宗", "扬清激浊", "受纳五谷"]),
        # 北方玄武七宿
        (8, "斗", "北方玄武", "斗木獬", "木", "獬", "木", 26.0, 25.5, "人马座φ", 6, "丑", "255°-281°", "吉",
         "六星斜立似柄杓，天府之柄宰相朝。天关道路权衡定，南斗注生福寿高。",
         ["南斗星君", "天关枢机", "延寿注生", "宰辅大臣", "玄武之首"]),
        (9, "牛", "北方玄武", "牛金牛", "金", "牛", "金", 8.0, 7.5, "摩羯座β (Dabih)", 6, "丑", "281°-289°", "凶",
         "六星如矢牵牛行，天关道路关梁明。牺牲农牧勤耕作，桥梁津渡保太平。",
         ["牵牛星", "牺牲祀典", "农桑劳作", "津梁关卡", "玄武之角"]),
        (10, "女", "北方玄武", "女土蝠", "土", "蝠", "土", 12.0, 11.0, "宝瓶座ε (Albali)", 4, "子", "289°-301°", "凶",
         "四星如箕独坐空，天之织女治女工。布帛藏库供御用，巧手天工造化中。",
         ["婺女", "织造女工", "布帛府库", "嫁娶事宜", "玄武之身"]),
        (11, "虚", "北方玄武", "虚日鼠", "日", "鼠", "水", 10.0, 9.0, "宝瓶座β (Sadalsuud)", 2, "子", "301°-311°", "凶",
         "二星南北正相当，天帝冢宰临太常。宗庙祭祀悲欢事，虚耗虚惊守静防。",
         ["天节冢宰", "宗庙祭祀", "虚耗守静", "清虚无为", "玄武之躯"]),
        (12, "危", "北方玄武", "危月燕", "月", "燕", "水", 17.0, 16.0, "宝瓶座α (Sadalmelik)", 3, "子", "311°-328°", "凶",
         "三星正立如张弓，天府高盖在虚东。修营盖屋防风雨，履险如夷运化通。",
         ["天府高盖", "宗庙修营", "居安思危", "土木构筑", "玄武之脊"]),
        (13, "室", "北方玄武", "室火猪", "火", "猪", "火", 16.0, 17.0, "飞马座α (Markab)", 2, "亥", "328°-344°", "吉",
         "二星直下立如墙，营室离宫宴飨方。修造宫室纳百福，国泰民安岁月长。",
         ["营室清庙", "宫室土木", "离宫别苑", "安居乐业", "玄武之体"]),
        (14, "壁", "北方玄武", "壁水貐", "水", "貐", "水", 9.0, 9.0, "飞马座γ (Algenib)", 2, "亥", "344°-353°", "吉",
         "二星下垂连营室，图书秘府文明秩。文章翰墨光千丈，道统昭垂日月质。",
         ["东壁天图", "秘府文章", "图书典籍", "文化昭明", "文昌科第"]),
        # 西方白虎七宿
        (15, "奎", "西方白虎", "奎木狼", "木", "狼", "木", 16.0, 18.0, "仙女座η", 16, "戌", "353°-9°", "吉",
         "十六星如曲尺连，天府武库兵戈旋。文章武功兼济处，白虎振威御极全。",
         ["天豕武库", "文章府库", "武备防御", "文武兼备", "白虎之尾翅"]),
        (16, "娄", "西方白虎", "娄金狗", "金", "狗", "金", 12.0, 12.5, "白羊座β (Sheratan)", 3, "戌", "9°-21°", "吉",
         "三星似品立中天，天狱群臣聚宴筵。招聚众贤兴礼乐，牺牲祭祀降甘泉。",
         ["聚众兴礼", "宗庙牺牲", "召集群贤", "祀典百神", "白虎之体"]),
        (17, "胃", "西方白虎", "胃土雉", "土", "雉", "土", 14.0, 15.0, "白羊座35", 3, "酉", "21°-35°", "吉",
         "三星成鼎形横侧，天仓大储五谷色。丰盈万斛充国用，富贵丰隆受天德。",
         ["天仓大储", "仓廪丰足", "积粟纳实", "五谷丰登", "白虎之腹"]),
        (18, "昴", "西方白虎", "昴日鸡", "日", "鸡", "金", 11.0, 11.0, "金牛座17 (Electra)", 7, "酉", "35°-46°", "凶",
         "七星连缀聚白光，西方旄头肃杀方。狱讼兵刑察秋毫，肃清四海靖维纲。",
         ["旄头胡星", "白虎之目", "兵刑狱讼", "霜露严凝", "秋杀之气"]),
        (19, "毕", "西方白虎", "毕月乌", "月", "乌", "金", 16.0, 16.0, "金牛座ε (Ain)", 8, "酉", "46°-62°", "吉",
         "八星开张如掩兔，天门网罗边防护。月离于毕滂沱雨，惠泽群生润九衢。",
         ["罕毕网罗", "天街边防", "行云致雨", "滋润万物", "边境宁谧"]),
        (20, "觜", "西方白虎", "觜火猴", "火", "猴", "火", 2.0, 0.5, "猎户座λ (Meissa)", 3, "申", "62°-64°", "凶",
         "三星品立如花蕊，白虎颔首微相随。军旅刍牧谨慎动，动止安详守机微。",
         ["觜觿虎口", "军旅刍牧", "谨言慎行", "伺机而动", "白虎之喙"]),
        (21, "参", "西方白虎", "参水猿", "水", "猿", "水", 9.0, 10.5, "猎户座ζ (Alnitak)", 7, "申", "64°-73°", "吉",
         "七星环佩大将军，腰带三星伐将勋。斩伐威勇安边境，权衡权度震乾坤。",
         ["白虎将军", "参伐武功", "威镇边疆", "权衡刚断", "参商相望"]),
        # 南方朱雀七宿
        (22, "井", "南方朱雀", "井木犴", "木", "犴", "木", 33.0, 33.0, "双子座μ", 8, "未", "73°-106°", "吉",
         "八星东西列两行，东井天泉天水光。法令平正平如水，澄清百虑润遐荒。",
         ["东井天泉", "水衡法令", "平正公正", "润泽生民", "朱雀之羽冠"]),
        (23, "鬼", "南方朱雀", "鬼金羊", "金", "羊", "金", 4.0, 2.5, "巨蟹座θ", 4, "未", "106°-110°", "凶",
         "四星如方中积尸，天帝祠祀斩贼旗。阴阳幽明察隐微，敬谨事神祸不起。",
         ["舆鬼天目", "积尸之气", "祠祀祷告", "幽微显彰", "朱雀之眼"]),
        (24, "柳", "南方朱雀", "柳土獐", "土", "獐", "土", 15.0, 13.5, "长蛇座δ", 8, "午", "110°-125°", "凶",
         "八星垂下如柳枝，天之厨宴调羹匙。膳食调和谨饮食，燮理阴阳万姓怡。",
         ["天厨天膳", "调和鼎鼐", "节制饮食", "朱雀之颈", "滋养调理"]),
        (25, "星", "南方朱雀", "星日马", "日", "马", "火", 7.0, 6.5, "长蛇座α (Alphard)", 7, "午", "125°-132°", "凶",
         "七星联缀若引弓，民事天衣职岁丰。七星高照当夏令，万象欣欣化育通。",
         ["七星之首", "天之衣裳", "朱雀之心", "民事稼穑", "离明盛德"]),
        (26, "张", "南方朱雀", "张月鹿", "月", "鹿", "火", 18.0, 17.0, "长蛇座υ", 6, "午", "132°-150°", "吉",
         "六星弯曲似引张，天宴珍羞四海疆。宗庙飨宴纳贡赋，百宝丰呈耀国光。",
         ["天府盛宴", "朝觐进献", "百物丰盈", "朱雀之嗉囊", "文物荟萃"]),
        (27, "翼", "南方朱雀", "翼火蛇", "火", "蛇", "火", 18.0, 19.0, "巨爵座α (Alkes)", 22, "巳", "150°-168°", "凶",
         "二十二星若舒翅，南宫羽翼威仪侍。声乐歌舞四夷宾，礼乐交辉光四极。",
         ["朱雀之翼", "礼乐教化", "声乐仪仗", "南极殊方", "声名远扬"]),
        (28, "轸", "南方朱雀", "轸水蚓", "水", "蚓", "水", 17.0, 17.0, "乌鸦座γ (Gienah)", 4, "巳", "168°-185°", "吉",
         "四星如车轸形长，长沙附辅乘车翔。天车运载行千里，四通八达吉无疆。",
         ["天车兵车", "载物载德", "通达四方", "朱雀之尾", "出行通畅"]),
    ]

    twenty_eight_mansions = []
    for item in mansion_data:
        twenty_eight_mansions.append(dict(
            ordinal=item[0],
            name=item[1],
            quadrant=item[2],
            beast_spirit=item[3],
            seven_governor=item[4],
            animal=item[5],
            element=item[6],
            ancient_degrees=float(item[7]),
            song_degrees=float(item[8]),
            determinative_star=item[9],
            star_count=item[10],
            earthly_branch=item[11],
            solar_longitude_range=item[12],
            luck_nature=item[13],
            song_lyrics=item[14],
            imagery_meanings=item[15],
            source_id="calendar-source-xingkongdiguo",
            rule_version=VERSION,
        ))

    # 三垣星官体系
    enclosure_data = [
        (1, "紫微垣", "中垣（中宫天阙）", 163, 39,
         "天帝皇宫、政令枢纽、紫微天阙，统摄北极、北斗与三台尚书文昌诸星官",
         "中元北极紫微宫，五星高居紫微中。勾陈六星六宫宿，北斗七星车运穹。太常尚书列两旁，三台文昌耀帝光。",
         ["北极五星", "勾陈", "北斗七星", "文昌", "三台", "天柱", "尚书", "华盖", "天床", "大理"]),
        (2, "太微垣", "上垣（天子明堂百官朝贺）", 78, 20,
         "朝廷文武百官、天子明堂听政之府，统领五帝座、三公、九卿、灵台与郎位",
         "上元南极太微宫，五帝座在黄道中。左右执法诸卿在，明堂灵台测象通。郎官虎贲威仪肃，九卿三公佐治隆。",
         ["五帝座", "太子", "从官", "三公", "九卿", "明堂", "灵台", "屏星", "郎位", "虎贲"]),
        (3, "天市垣", "下垣（天下市井贸易权衡）", 87, 19,
         "天下市场、平准贸易、物价律度与百工聚落，统辖帝座、候星、市楼与车肆贯索",
         "下元天市东南向，帝座当中星朗亮。市楼列肆商贾聚，平准权衡天下量。贯索天牢警奸宄，宗正宗室福绵长。",
         ["帝座", "候星", "宦者", "斗勺", "市楼", "车肆", "贯索", "宗人", "宗正", "帛度"]),
    ]
    three_enclosures = []
    for item in enclosure_data:
        three_enclosures.append(dict(
            ordinal=item[0],
            name=item[1],
            alias=item[2],
            star_count=item[3],
            official_count=item[4],
            symbolism=item[5],
            song_lyrics=item[6],
            key_officials=item[7],
            source_id="calendar-source-xingkongdiguo",
            rule_version=VERSION,
        ))

    # 中国古代历代代表性历法参数与算法体系（源自《中国古代天体测量学及天文仪器》与《历法溯源》）
    calendar_history_data = [
        (1, "guliu-calendar", "古六历（黄帝/颛顼/夏/殷/周/鲁历）", "先秦/战国", "先秦诸侯国历官", "公元前4世纪",
         365.250000, 29.530851, "十九年七闰（章法）", "未引入岁差", "甲子朔旦冬至",
         ["确立四分历常数体制（岁实365.25日、朔策29+499/940日）", "确立十九年七闰章法", "奠定干支纪日与二十四节气框架"],
         "中国古代最早成系统的四分历法代表，为后世历法奠定基础构架"),
        (2, "taichu-calendar", "太初历", "西汉", "落下闳、邓平、唐都", "公元前104年（汉武帝太初元年）",
         365.250164, 29.530864, "以无中气之月为闰月（首创置闰准则）", "未引入岁差", "汉武帝太初元年十一月甲子朔旦冬至",
         ["正式将二十四节气系统编入历法并确定节气时刻", "发明以无中气之月置闰的科学方法", "确立以建寅之月（夏历正月）为岁首的传统"],
         "中国历史上第一部由朝廷颁布并保存完整算法记载的里程碑式历法"),
        (3, "santong-calendar", "三统历", "西汉末", "刘歆", "公元5年",
         365.250164, 29.530864, "统法（19年7闰，562年207闰，4617年1701闰）", "未引入岁差", "三统上元",
         ["世界上第一部完整保存下来的成体系历法专著（载于《汉书·律历志》）", "建立五星会合周期数学模型与推步算法", "建立超辰法纠正太岁纪年与岁星实际天象的累计误差"],
         "建立了中国古代律历融通的天文数学演绎体系"),
        (4, "sifen-calendar", "后汉四分历", "东汉", "李梵、编訢", "公元85年（汉章帝元和二年）",
         365.250000, 29.530851, "十九年七闰", "未引入岁差", "永元四年甲寅",
         ["高精度实测冬至时刻与八尺圭表晷影长", "引入黄道与赤道坐标精确数值换算表", "建立月行迟疾与近地点进动的几何概念"],
         "全面恢复并修正了汉代四分历常数，提升了推步精度"),
        (5, "daming-calendar", "大明历", "南北朝（刘宋）", "祖冲之", "公元462年（宋孝武帝大明六年）",
         365.242814, 29.530593, "391年144闰（打破十九年七闰传统）", "45年11个月差1度（中国历法首创引入岁差）", "宋孝武帝大明七年甲子",
         ["中国天文学史上首次将岁差正式引入历法推算", "打破传统十九年七闰章法，创制391年144闰的高精度置闰周期", "精确测定交点月日数（27.21223日），极大提升日食月食推算精度"],
         "古代历法计算精度的革命性飞跃，是南北朝天文学最高成就"),
        (6, "huangji-calendar", "皇极历", "隋代", "刘焯", "公元600年（隋文帝开皇二十年）",
         365.245098, 29.530597, "1024年377闰", "75年差1度", "仁寿二年甲子",
         ["首创等间距二次内插法（招差术），精确计算太阳与月亮视运动的不均匀性", "发明推算日食视差的黄经与黄纬双重修正算法", "建立平气与定气结合的交食计算模型"],
         "开创中国古代内插法天文学算法的先河，奠定了唐宋高阶数学历法的基础"),
        (7, "dayan-calendar", "大衍历", "唐代", "僧一行（张遂）", "公元727年（唐玄宗开元十五年）",
         365.244365, 29.530596, "3040年1120闰", "82年差1度", "开元十二年朔旦冬至",
         ["首创不等间距二次内插法（不等距招差术）", "组织全国十三处天文大地观测（南宫说等），实测得出子午线一度长为351里80步", "创立九服晷影算法，精确计算全国不同纬度的昼夜漏刻与出没分"],
         "结构极为严谨、算法高度成熟的唐代官方典范历法，对东亚各国产生深远影响"),
        (8, "shoushi-calendar", "授时历", "元代", "郭守敬、王恂、许衡", "公元1281年（元世祖至元十八年）",
         365.242500, 29.530593, "消长法微调无中气置闰", "66年8个月差1度", "至元十八年辛巳",
         ["确定回归年长度为365.2425日，与现代格里高利公历完全一致，领先西方300余年", "发明三次差内插法（高阶招差术）与弧矢割圆术（球面三角法基础）", "创制简仪、高表、仰仪、景符等13种高精度天文仪器，累积大量实测数据"],
         "中国古代历法的巅峰之作，行用达360余年（含明代大统历），为世界天文学瑰宝"),
        (9, "datong-calendar", "大统历", "明代", "元统、马沙亦黑", "公元1384年（明太祖洪武十七年）",
         365.242500, 29.530593, "沿用授时历置闰法", "沿用授时历", "洪武十七年甲子",
         ["继承元代授时历算法精髓，停止使用消长法以保证算法稳定性", "完善国家官方颁历制度与历书版刻标准", "融合回回司天监算法进行日月交食多地推步比对"],
         "明代官方行用全期的标准历法，保障了国家礼制与民用授时"),
        (10, "shixian-calendar", "时宪历（西洋新法历书）", "明末清初", "徐光启、汤若望、李天经", "公元1645年（清顺治二年）",
         365.242334, 29.530588, "基于定气定朔的无中气置闰法", "50.26角秒/年", "顺治二年",
         ["由平气平朔彻底改为定气定朔，以太阳实际真黄经时刻定义二十四节气", "引入球面几何学、第谷天文体系与黄道赤道坐标立体转换法", "系统应用对数表与连续几何逼近法计算行星轨迹"],
         "中国现代农历（紫金山天文台现行历法计算规范）的算法直接源头"),
    ]
    historical_calendars = []
    for item in calendar_history_data:
        historical_calendars.append(dict(
            ordinal=item[0],
            calendar_id=item[1],
            name=item[2],
            dynasty=item[3],
            author=item[4],
            year_created=item[5],
            tropical_year_days=float(item[6]),
            synodic_month_days=float(item[7]),
            intercalary_cycle=item[8],
            precession_constant=item[9],
            epoch_baseline=item[10],
            innovations=item[11],
            historical_significance=item[12],
            source_id="calendar-source-tianticeliang",
            rule_version=VERSION,
        ))

    # 河图五行生成数理（源自《历法溯源》第二章：河图解密）
    hetu_data = [
        (1, 1, 6, "水", "北", "冬", "坤", "坎",
         "天一生水，地六成之。一六共宗居北方，太阴水之体也。",
         "天干丙辛合化水，地支子亥北方水局。一为阳之生数，六为阴之成数，阴阳和合而化水。",
         ["水", "北方", "冬", "玄武", "黑色", "咸味", "肾", "坎卦", "智", "潜藏闭蓄"]),
        (2, 2, 7, "火", "南", "夏", "乾", "离",
         "地二生火，天七成之。二七同道居南方，太阳火之位也。",
         "天干戊癸合化火，地支巳午南方火局。二为阴之生数，七为阳之成数，阴阳相摩而化火。",
         ["火", "南方", "夏", "朱雀", "红色", "苦味", "心", "离卦", "礼", "炎上昭明"]),
        (3, 3, 8, "木", "东", "春", "离", "震巽",
         "天三生木，地八成之。三八为朋居东方，少阳木之发也。",
         "天干丁壬合化木，地支寅卯东方木局。三为阳之生数，八为阴之成数，少阳萌动而化木。",
         ["木", "东方", "春", "青龙", "青色", "酸味", "肝", "震卦", "巽卦", "仁", "曲直条达"]),
        (4, 4, 9, "金", "西", "秋", "坎", "兑乾",
         "地四生金，天九成之。四九为友居西方，少阴金之肃也。",
         "天干乙庚合化金，地支申酉西方金局。四为阴之生数，九为阳之成数，少阴肃降而化金。",
         ["金", "西方", "秋", "白虎", "白色", "辛味", "肺", "兑卦", "乾卦", "义", "从革收敛"]),
        (5, 5, 10, "土", "中", "四季", "兑艮", "坤艮中宫",
         "天五生土，地十成之。五十同途居中央，冲气以为和，万物之母也。",
         "天干甲己合化土，地支辰戌丑未四季土局。五为阳生数，十为阴成数，中和敦厚而化土。",
         ["土", "中央", "四季长夏", "黄色", "甘味", "脾", "坤卦", "艮卦", "信", "稼穑生化"]),
    ]
    hetu_numerology = []
    for item in hetu_data:
        hetu_numerology.append(dict(
            pair_id=item[0],
            generating_number=item[1],
            forming_number=item[2],
            element=item[3],
            direction=item[4],
            season=item[5],
            trigram_earlier=item[6],
            trigram_later=item[7],
            principle=item[8],
            yinyang_formula=item[9],
            imagery_items=item[10],
            source_id="calendar-source-lifasuyuan",
            rule_version=VERSION,
        ))

    # 西周金文四分月相体系（源自《历法溯源》第九章与第十四章：金文历谱）
    lunar_phase_data = [
        (1, "chuji", "初吉", 1, 8,
         "新月至上弦（农历初一至初八）",
         "西周青铜器铭文中指月光初生、吉日良辰之时，多见于天子册命、征伐出师与重器铭功定点",
         "月芽始苏，阳德初升，万物始萌，利于谋篇布局与肇造新基"),
        (2, "jishengba", "既生霸", 8, 15,
         "上弦至望月（农历初八至十五）",
         "霸即月魄光辉。既生霸指月魄大半已生、光芒充盈，自上弦至于满月，为阳光渐满盛期",
         "光辉敷布，蓄势腾骧，事理融通，利于扩充推进与全面展开"),
        (3, "jiwang", "既望", 15, 23,
         "满月至下弦（农历十五至廿三）",
         "望者日月相望。既望指满月之后月魄始亏之时，周王行赏、祭祖告捷多选定于既望吉日",
         "圆满极盛，持盈保泰，审度全局，利于酬功封赏与成果固化"),
        (4, "jisiba", "既死霸", 23, 30,
         "下弦至晦日（农历廿三至月末）",
         "死霸指月魄亏损隐没之期，自下弦至于日月合朔之晦日，为归息内照、去故鼎新之期",
         "余辉敛曜，虚堂纳静，潜龙勿用，利于休养生息与去旧图新"),
    ]
    lunar_phase_regimes = []
    for item in lunar_phase_data:
        lunar_phase_regimes.append(dict(
            ordinal=item[0],
            phase_code=item[1],
            name=item[2],
            lunar_day_start=item[3],
            lunar_day_end=item[4],
            astronomical_phase=item[5],
            bronze_inscription_usage=item[6],
            cultural_implication=item[7],
            source_id="calendar-source-lifasuyuan",
            rule_version=VERSION,
        ))

    counts = {
        "data_sources": write_jsonl("data_sources", source_rows),
        "five_elements": write_jsonl("five_elements", five_elements),
        "heavenly_stems": write_jsonl("heavenly_stems", stems),
        "earthly_branches": write_jsonl("earthly_branches", branches),
        "branch_imagery": write_jsonl("branch_imagery", branch_imagery_rows),
        "trigrams": write_jsonl("trigrams", trigrams),
        "trigram_imagery": write_jsonl("trigram_imagery", trigram_imagery_rows),
        "hexagrams": write_jsonl("hexagrams", hexagrams),
        "hexagram_explanations": write_jsonl("hexagram_explanations", hexagram_explanations),
        "solar_terms": write_jsonl("solar_terms", terms),
        "sexagenary_cycle": write_jsonl("sexagenary_cycle", cycles),
        "fengshui_mountains": write_jsonl("fengshui_mountains", mountains),
        "luoshu_palaces": write_jsonl("luoshu_palaces", luoshu),
        "twenty_eight_mansions": write_jsonl("twenty_eight_mansions", twenty_eight_mansions),
        "three_enclosures": write_jsonl("three_enclosures", three_enclosures),
        "historical_calendars": write_jsonl("historical_calendars", historical_calendars),
        "hetu_numerology": write_jsonl("hetu_numerology", hetu_numerology),
        "lunar_phase_regimes": write_jsonl("lunar_phase_regimes", lunar_phase_regimes),
    }
    print(json.dumps(counts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

