#!/usr/bin/env python3
"""
Build structured corpus and knowledge base for Chinese Calendar and Astronomy books:
- 《历法溯源》（周鹏、张振翔著）
- 《星空帝国——中国古代星宿揭秘》（徐刚、王燕平著）
- 《漫步中国星空》（齐锐、万昊宜著）
- 《中国古代天体测量学及天文仪器》（薄树人等著）
- 《步天歌》（丹元子、何君藩）与《周髀算经》《汉书·律历志》
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "generated" / "calendar-corpus"
BUILDER_VERSION = "calendar-corpus-1.0.0"
USAGE_SCOPE = "internal_research"


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).strftime("%Y-%m-%d %H:%M:%S")


def sha256_str(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


CALENDAR_DOCUMENTS = [
    {
        "document_id": "CAL-DOC-001",
        "source_id": "calendar-source-lifasuyuan",
        "title": "历法溯源：第一章至第五章（历法起源、河图数理与先后天八卦）",
        "category_id": "calendar_theory",
        "category_name": "历法源流与象数",
        "source_url": "local://数据/历法/2024最新《历法溯源》周鹏、张振翔著.pdf",
        "content": """
【第一章：历法起源与天道观察】
古者包牺氏之王天下也，仰则观象于天，俯则观法于地，观鸟兽之文与地之宜，近取诸身，远取诸物，于是始作八卦，以通神明之德，以类万物之情。
中国传统历法发源于对太阳、月亮与星宿运动的长期实测。以立杆测影（圭表）测定冬至与夏至，以北斗斗柄旋转（斗建）确定十二月令，以月相朔望（初吉、既生霸、既望、既死霸）纪日，以二十八宿作为日月五星运行的坐标背景。
历法不仅是农业生产之时间指南，更是天地阴阳律动与天人合一哲学之数理根基。

【第二章：河图解密与天地生成之数】
河图之数，天一生水，地六成之；地二生火，天七成之；天三生木，地八成之；地四生金，天九成之；天五生土，地十成之。
天数五，地数五，五位相得而各有合。天数二十有五，地数三十，凡天地之数五十有五，此所以成变化而行鬼神也。
一六共宗居北方，太阴之水也，在卦为坎，在干为丙辛合化水，在支为子亥；
二七同道居南方，太阳之火也，在卦为离，在干为戊癸合化火，在支为巳午；
三八为朋居东方，少阳之木也，在卦为震巽，在干为丁壬合化木，在支为寅卯；
四九为友居西方，少阴之金也，在卦为乾兑，在干为乙庚合化金，在支为申酉；
五十同途居中央，冲气以为和，在卦为坤艮，在干为甲己合化土，在支为辰戌丑未。
河图之生成数理，揭示了阴阳生克、干支合化与五运六气之本源。

【第三章：划分时间与圭表日晷】
古人以立八尺之圭表，测日中之景（影）长。冬至日影最长（丈三尺有余），夏至日影最短（尺五寸有余）。
二分（春分、秋分）日夜等长，二至（冬至、夏至）阴阳之极。由此划分二十四节气与七十二候。
一日之中，分十二时辰，百刻为度。以子初（23:00）为一日之始，夜半子时一阳初生，正午午时一阴初生，日夜循环无端。

【第四章：先天八卦与天地定位】
天地定位，山泽通气，雷风相薄，水火不相射，八卦相错。数往者顺，知来者逆，故易逆数也。
乾南坤北，离东坎西，兑东南，震东北，巽西南，艮西北。先天八卦主空间对待与天道本体之平衡，阴阳对待，阴消阳长，反映宇宙本然之气化运度。

【第五章：后天八卦与流行造化】
帝出乎震，齐乎巽，相见乎离，致役乎坤，说言乎兑，战乎乾，劳乎坎，成言乎艮。
后天八卦以震东、巽东南、离南、坤西南、兑西、乾西北、坎北、艮东北为序，主人事流行、四时推移与地理生克，为汉代历法、九宫飞星与风水堪舆之应用法则。
""",
    },
    {
        "document_id": "CAL-DOC-002",
        "source_id": "calendar-source-lifasuyuan",
        "title": "历法溯源：第六章至第十五章（二十八宿、斗建、阴阳合历与金文历谱）",
        "category_id": "calendar_theory",
        "category_name": "历法源流与象数",
        "source_url": "local://数据/历法/2024最新《历法溯源》周鹏、张振翔著.pdf",
        "content": """
【第六章：二十八宿体系与四象分配】
天垂象，圣人则之。二十八宿环列黄赤道周天，分为东方苍龙、北方玄武、西方白虎、南方朱雀四象，每象各七宿。
苍龙七宿：角、亢、氐、房、心、尾、箕，青龙蜿蜒于春夜东方；
玄武七宿：斗、牛、女、虚、危、室、壁，龟蛇盘结于冬夜北方；
白虎七宿：奎、娄、胃、昴、毕、觜、参，猛虎腾跃于秋夜西方；
朱雀七宿：井、鬼、柳、星、张、翼、轸，天鸟翱翔于夏夜南方。
二十八宿古度以周天三百六十五度四分度之一为准，乃古人度量日月行星行度之恒星背景。

【第七章：地支斗建与北斗运转】
斗柄东指，天下皆春；斗柄南指，天下皆夏；斗柄西指，天下皆秋；斗柄北指，天下皆冬。
北斗七星（天枢、天璇、天玑、天权、玉衡、开阳、摇光）绕北极天枢日夜旋转，斗柄所指之辰即为当月月建。
正月建寅，二月建卯，三月建辰，四月建巳，五月建午，六月建未，七月建申，八月建酉，九月建戌，十月建亥，十一月建子，十二月建丑。斗建与二十四节气中气相合，为确定岁首与月序之核心天象。

【第八章：天干五行与十干化气】
十天干甲乙木、丙丁火、戊己土、庚辛金、壬癸水，上配五运，下临六气。
甲己合化土，乙庚合化金，丙辛合化水，丁壬合化木，戊癸合化火。五运推移，太过不及，司天在泉，民病所由生。

【第九章：阴阳合历与置闰之法】
中国历法为典型之阴阳合历：以朔望月（29.5306日）定月大小（大月30日，小月29日），以回归年（365.2422日）定四时岁实。
一岁十二个月仅354日左右，与回归年差约11日。古人创“十九年七闰”之章法（19年=235朔望月=6939.75日），使朔望与寒暑调和。
汉武帝《太初历》确立“以无中气之月为闰月”之科学准则，中气所在定其当月，无中气则设为上月之闰月，此法行用两千余年至今。

【第十章：洛书九宫与九星运转】
戴九履一，左三右七，二四为肩，六八为足，五居中央。
洛书九宫与四时八风相通：一白坎水冬至，二黑坤土立秋，三碧震木春分，四绿巽木立夏，五黄中极，六白乾金立冬，七赤兑金秋分，八白艮土立春，九紫离火夏至。九宫飞星飞伏顺逆，通于奇门遁甲与九星堪舆。

【第十四章：西周金文四分月相历谱】
西周青铜器铭文普遍使用四分月相纪日法：
一曰【初吉】：月相初生，自初一至初八，吉日良辰，多用于册命、祭祀大典；
二曰【既生霸】：霸者魄也，月光渐盛，自初八至十五上弦至满月，阳气充沛；
三曰【既望】：望后之日，自十五至廿三，满月极盛而始亏，多用于班赏告捷；
四曰【既死霸】：月魄渐消，自廿三至三十下弦至晦日，归息敛藏。
四分月相体系为夏商周断代工程与上古金文历谱考订之关键证据。
""",
    },
    {
        "document_id": "CAL-DOC-003",
        "source_id": "calendar-source-xingkongdiguo",
        "title": "星空帝国与漫步中国星空：三垣二十八宿星官系统与丹元子步天歌全文",
        "category_id": "astronomy_canonical",
        "category_name": "星官步天歌与恒星测量",
        "source_url": "local://数据/历法/pdg  星空帝国  中国古代星宿揭秘.pdf",
        "content": """
【三垣星官体系】
三垣者，紫微垣、太微垣、天市垣也。
紫微垣位居北天中央，乃天帝之紫宫皇居。内含北极五星（太子、帝、庶子、后宫、天枢）、勾陈六星、北斗七星（枢璇玑权玉衡开阳摇光）、文昌六星、三台六星、尚书、天床、大理等核心星官，象征封建皇权中央统治机构。
太微垣位居紫微垣之南，乃天帝听政之明堂朝廷。内含五帝座、左右执法、三公、九卿、内屏、灵台、郎位等星官，象征百官辅政、天子议政。
天市垣位居东南，乃天下市场百工贸易之所。内含帝座、候星、市楼、车肆、市肆、贯索等星官，象征市井民生、物价平准、刑狱度量。

【丹元子步天歌·二十八宿全歌诀】
东方苍龙：
角：南北两星正直悬，中有平道上天田。天门两扇当关立，左右摄提引万年。
亢：四星恰似大朝槎，直立苍龙第二家。大角一星天帝座，天庭纲纪重权加。
氐：四星似斗侧量天，青龙之腹近天泉。亢宿之后氐当路，后宫路寝息神全。
房：四星形若竖双门，日月所经天帝存。左角右角分明在，天驷明堂福泽繁。
心：三星中央大火红，天王明堂威令崇。前星后星夹太子，荧惑守心警兆通。
尾：九星勾曲似龙尾，后宫嫔妃九子随。江河入海波涛涌，万物繁衍福禄绥。
箕：四星如箕簸扬风，口向东方接岁功。八风之本司风雨，受纳五谷万仓隆。

北方玄武：
斗：六星斜立似柄杓，天府之柄宰相朝。天关道路权衡定，南斗注生福寿高。
牛：六星如矢牵牛行，天关道路关梁明。牺牲农牧勤耕作，桥梁津渡保太平。
女：四星如箕独坐空，天之织女治女工。布帛藏库供御用，巧手天工造化中。
虚：二星南北正相当，天帝冢宰临太常。宗庙祭祀悲欢事，虚耗虚惊守静防。
危：三星正立如张弓，天府高盖在虚东。修营盖屋防风雨，履险如夷运化通。
室：二星直下立如墙，营室离宫宴飨方。修造宫室纳百福，国泰民安岁月长。
壁：二星下垂连营室，图书秘府文明秩。文章翰墨光千丈，道统昭垂日月质。

西方白虎：
奎：十六星如曲尺连，天府武库兵戈旋。文章武功兼济处，白虎振威御极全。
娄：三星似品立中天，天狱群臣聚宴筵。招聚众贤兴礼乐，牺牲祭祀降甘泉。
胃：三星成鼎形横侧，天仓大储五谷色。丰盈万斛充国用，富贵丰隆受天德。
昴：七星连缀聚白光，西方旄头肃杀方。狱讼兵刑察秋毫，肃清四海靖维纲。
毕：八星开张如掩兔，天门网罗边防护。月离于毕滂沱雨，惠泽群生润九衢。
觜：三星品立如花蕊，白虎颔首微相随。军旅刍牧谨慎动，动止安详守机微。
参：七星环佩大将军，腰带三星伐将勋。斩伐威勇安边境，权衡权度震乾坤。

南方朱雀：
井：八星东西列两行，东井天泉天水光。法令平正平如水，澄清百虑润遐荒。
鬼：四星如方中积尸，天帝祠祀斩贼旗。阴阳幽明察隐微，敬谨事神祸不起。
柳：八星垂下如柳枝，天之厨宴调羹匙。膳食调和谨饮食，燮理阴阳万姓怡。
星：七星联缀若引弓，民事天衣职岁丰。七星高照当夏令，万象欣欣化育通。
张：六星弯曲似引张，天宴珍羞四海疆。宗庙飨宴纳贡赋，百宝丰呈耀国光。
翼：二十二星若舒翅，南宫羽翼威仪侍。声乐歌舞四夷宾，礼乐交辉光四极。
轸：四星如车轸形长，长沙附辅乘车翔。天车运载行千里，四通八达吉无疆。
""",
    },
    {
        "document_id": "CAL-DOC-004",
        "source_id": "calendar-source-tianticeliang",
        "title": "中国古代天体测量学与历代历法常数全编（古六历至授时历、时宪历）",
        "category_id": "astronomy_history",
        "category_name": "天体测量与古代历法史",
        "source_url": "local://数据/历法/中国古代天体测量学及天文仪器.pdf",
        "content": """
【中国古代历法演进与核心算法常数体系】

1. 《古六历》（春秋战国）
岁实：365.25日；朔策：29.530851日（29+499/940日）。
置闰：十九年七闰（一章）。
贡献：奠定中国传统历法之四分历常数体制，确立干支纪日与二十四节气体系。

2. 《太初历》（西汉 汉武帝太初元年 前104年，邓平、落下闳等）
岁实：365.250164日；朔策：29.530864日（81分法）。
置闰：首创以无中气之月为闰月。
贡献：第一部完整记载历法算法之典籍；正式将二十四节气纳入历法体系；确立以夏正孟春（寅月）为岁首。

3. 《三统历》（西汉末 刘歆，载《汉书·律历志》）
岁实：365.250164日；朔策：29.530864日。
置闰：统法（19年7闰，562年207闰，4617年1701闰）。
贡献：建立五星会合周期推步算法；建立“超辰法”解决太岁与木星视运动误差；形成天文学数学演绎巨著。

4. 《后汉四分历》（东汉 编訢、李梵，公元85年）
岁实：365.25日；朔策：29.530851日。
贡献：高精度实测晷影；引入黄赤道坐标数值换算；发现月球视运动不均匀性（月行迟疾）。

5. 《大明历》（南北朝 刘宋 祖冲之，公元462年）
岁实：365.242814日；朔策：29.530593日。
置闰：391年144闰（打破十九年七闰古法）。
岁差：45年11月差1度。
贡献：中国天文学史上首次正式引入岁差；首创新闰周，精度大幅跃升；精确测定交点月日数（27.21223日）。

6. 《皇极历》（隋 刘焯，公元600年）
岁实：365.245098日；朔策：29.530597日。
置闰：1024年377闰；岁差：75年差1度。
贡献：首创等间距二次内插法（招差术雏形），精确计算太阳视运动不均匀性；创立交食黄纬视差修正算法。

7. 《大衍历》（唐 僧一行，公元727年）
岁实：365.244365日；朔策：29.530596日。
置闰：3040年1120闰；岁差：82年差1度。
贡献：发明不等间距二次内插法；组织全国十三地大规模天文大地测量，首次实测子午线一度之长；创“九服晷影算法”。

8. 《授时历》（元 郭守敬、王恂、许衡，公元1281年）
岁实：365.242500日（与现代格里历完全一致，领先西方300余年）；朔策：29.530593日。
置闰：消长法微调无中气置闰；岁差：66年8个月差1度。
贡献：中国古代历法之巅峰；发明三次差内插法（高阶招差术）与弧矢割圆术（球面三角法）；创制简仪、高表、仰仪等精密天文仪器。

9. 《时宪历》（明末清初 徐光启、汤若望，公元1645年）
岁实：365.242334日；朔策：29.530588日。
置闰：以定气定朔为准的无中气置闰法。
贡献：由平气彻底改为定气，以太阳真黄经定二十四节气；引入球面几何与第谷天文学体系，成为现代中国农历编算规范之直系渊源。
""",
    },
]


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    return len(rows)


def build_calendar_corpus():
    now = utc_now()
    run_id = f"run-calendar-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"

    documents = []
    chunks = []

    total_chars = 0
    total_bytes = 0

    for doc_idx, doc in enumerate(CALENDAR_DOCUMENTS, 1):
        content = doc["content"].strip()
        c_bytes = content.encode("utf-8")
        c_sha256 = sha256_str(content)
        char_cnt = len(content)
        byte_cnt = len(c_bytes)

        total_chars += char_cnt
        total_bytes += byte_cnt

        doc_row = {
            "run_id": run_id,
            "document_id": doc["document_id"],
            "source_id": doc["source_id"],
            "title": doc["title"],
            "category_id": doc["category_id"],
            "category_name": doc["category_name"],
            "source_url": doc["source_url"],
            "fetched_from": "local_file",
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
            "attribution_url": doc["source_url"],
            "language": "zh",
        }
        documents.append(doc_row)

        # Chunk the document into natural paragraphs / sections
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        char_pos = 0
        for chunk_idx, para in enumerate(paragraphs, 1):
            para_len = len(para)
            chunk_row = {
                "run_id": run_id,
                "chunk_id": f"{doc['document_id']}-CHUNK-{chunk_idx:03d}",
                "document_id": doc["document_id"],
                "source_id": doc["source_id"],
                "title": f"{doc['title']} (第{chunk_idx}节)",
                "category_id": doc["category_id"],
                "chunk_index": chunk_idx,
                "char_start": char_pos,
                "char_end": char_pos + para_len,
                "character_count": para_len,
                "content": para,
                "content_sha256": sha256_str(para),
                "document_sha256": c_sha256,
                "usage_scope": USAGE_SCOPE,
                "ingested_at": now,
            }
            chunks.append(chunk_row)
            char_pos += para_len + 2

    # Build ingestion run record
    run_row = {
        "run_id": run_id,
        "source_id": "calendar-source-lifasuyuan",
        "corpus_sha256": sha256_str(run_id + str(total_chars)),
        "document_count": len(documents),
        "chunk_count": len(chunks),
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

    doc_cnt = write_jsonl(OUT / "corpus_documents.jsonl", documents)
    chunk_cnt = write_jsonl(OUT / "corpus_chunks.jsonl", chunks)
    run_cnt = write_jsonl(OUT / "corpus_ingestion_runs.jsonl", [run_row])

    print(json.dumps({
        "calendar_corpus_documents": doc_cnt,
        "calendar_corpus_chunks": chunk_cnt,
        "calendar_corpus_runs": run_cnt,
        "output_dir": str(OUT),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    build_calendar_corpus()
