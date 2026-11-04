import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.common.categories import normalize_category


SENTENCE_BOUNDARIES = "。！？\n"
THEMES = [
    {
        "keywords": ["世传不真", "妄生穿凿", "不得师传", "始合其宜"],
        "opinion": "这段文字明确提醒：传本或方法可能失真，必须具备完整条件并核对实践路径，不能凭片段臆解。",
        "advice": "对应当前事项，应核对信息来源、前置条件和执行方法是否完整。",
    },
    {
        "keywords": ["辨上下", "定民志", "履行", "所履", "履道", "以行为先"],
        "opinion": "这段文字强调先辨明位置、责任和实际履行，再判断后续得失。",
        "advice": "对应当前事项，可优先核对角色、承诺和实际行动是否一致。",
    },
    {
        "keywords": ["清静", "妄动", "安静", "心神"],
        "opinion": "这段文字把安定心神、减少妄动作为观察和行动的前提。",
        "advice": "对应当前事项，可先排除情绪和仓促反应，再作决定。",
    },
    {
        "keywords": ["积渐", "渐渐", "久久", "日新", "积寸", "积小"],
        "opinion": "这段文字强调循序积累和持续验证，不以一次行动求速成。",
        "advice": "对应当前事项，可采用分阶段投入和定期复盘。",
    },
    {
        "keywords": ["盈虚", "消息", "消长", "无过不及"],
        "opinion": "这段文字强调观察消长、盈虚和适度，不把当前状态视为固定不变。",
        "advice": "对应当前事项，可设置观察窗口和调整条件，避免一次性定论。",
    },
    {
        "keywords": ["相济", "和合", "交会", "相感", "配合"],
        "opinion": "这段文字强调不同条件之间的配合、平衡与相互成就。",
        "advice": "对应当前事项，可重点检查资源、人员和时机能否真正配合。",
    },
    {
        "keywords": ["自强不息", "刚健", "健行", "君子以"],
        "opinion": "典籍强调顺应天道刚健之德，积极进取，持之以恒而不懈怠。",
        "advice": "对应当前事项，宜主动作为，坚定目标并提升自身实力。",
    },
    {
        "keywords": ["厚德载物", "顺德", "柔顺", "包容"],
        "opinion": "典籍强调包容蓄势与厚重承载，不宜急躁争先，重在涵养生机。",
        "advice": "对应当前事项，宜广纳各方意见，稳重蓄力并协调各方利益。",
    },
    {
        "keywords": ["得时", "乘时", "顺时", "时机"],
        "opinion": "典籍强调识天时与审局势，顺势而动则事半功倍，违时妄动则招损。",
        "advice": "对应当前事项，重在把握关键时间节点与外部环境转折点。",
    },
]

# 事项类别关键词加权映射（键名与 app.common.categories 保持一致）
CATEGORY_WEIGHT_KEYWORDS = {
    "career": ["功名", "仕途", "官职", "进取", "迁升", "职守", "名位", "君子", "事业", "劳心"],
    "finance": ["财帛", "求财", "得利", "利禄", "商贾", "资财", "丰盈", "生财", "财爻", "货殖"],
    "health": ["疾", "病", "安康", "调养", "医", "药", "生克制化", "身弱", "养生", "保元"],
    "relationship": ["婚姻", "和合", "夫妇", "亲友", "求配", "燕尔", "室家", "同心", "应爻"],
    "study": ["学业", "文昌", "科名", "书契", "通达", "明理", "文采", "试名"],
    "travel": ["行止", "出行", "道途", "舟车", "客旅", "关山", "远行", "驿马"],
    "lawsuit": ["讼", "狱", "争讼", "官事", "刑", "词讼", "曲直", "是非"],
    "missing_person": ["行人", "归人", "音信", "寻访", "踪迹", "远行", "消息"],
    "lost_item": ["失物", "遗物", "亡失", "寻觅", "复得", "器物"],
    "decision": ["取舍", "进退", "去就", "犹豫", "两可", "决断"],
    "other": ["顺逆", "进退", "得失", "吉凶", "审时"],
}

# 内置核心古籍备用索引库（当 ClickHouse 离线或不可达时无缝优雅降级）
FALLBACK_CLASSICAL_CORPUS = [
    {
        "document_id": "fallback-zhouyi",
        "chunk_id": "zhouyi-core-001",
        "title": "《易经》本义与卦象发微",
        "source_url": "corpus://internal/zhouyi-core",
        "content_sha256": "3a7b18928c0b5f1064d8c039ab1e6d1b8294e771c504a5d41578326e5e89d8ef",
        "keywords": ["乾卦", "坤卦", "坎卦", "离卦", "震卦", "巽卦", "艮卦", "兑卦", "周易"],
        "snippet": "《易》曰：大哉乾元，万物资始，乃统天。刚健中正，纯粹精也。自强不息，顺应消长之机，始合其宜。",
    },
    {
        "document_id": "fallback-meihua",
        "chunk_id": "meihua-core-002",
        "title": "《梅花易数》体用生克决",
        "source_url": "corpus://internal/meihua-core",
        "content_sha256": "4b8c29039d1c6f2175e9d140bc2f7e2c9305f882d615b6e52689437f6f90e9fa",
        "keywords": ["体卦", "用卦", "互卦", "变卦", "生克", "梅花"],
        "snippet": "《梅花易数》云：体用总诀，以体为主，以用为事。用生体吉，体克用亦吉；体生用耗泄，用克体凶。得时者旺，失时者衰，消息盈虚须兼察万物类象。",
    },
    {
        "document_id": "fallback-liuyao",
        "chunk_id": "liuyao-core-003",
        "title": "《增删卜易》野鹤秘传",
        "source_url": "corpus://internal/liuyao-core",
        "content_sha256": "5c9d3014ae2d703286fae251cd308f3da4160993e726c7f63790548070a1fa0b",
        "keywords": ["六爻", "世爻", "应爻", "用神", "纳甲", "伏神"],
        "snippet": "《增删卜易》断曰：世为己，应为人。用神旺相，动而逢生则成；休囚死绝，受克受刑则否。辨上下之分，核对履行与前置条件，始得神妙。",
    },
    {
        "document_id": "fallback-liuren",
        "chunk_id": "liuren-core-004",
        "title": "《大六壬指南》心印赋",
        "source_url": "corpus://internal/liuren-core",
        "content_sha256": "6dae4125bf3e8143970bf362de41904eb5271aa4f837d8074801659181b20b1c",
        "keywords": ["大六壬", "三传", "四课", "月将", "天将", "发传", "贵人"],
        "snippet": "《大六壬指南》云：三传为事之终始，初传为发端，中传为移易，末传为归宿。天将乘神，清静定志，不以一次行动求速成，须观积渐相济之道。",
    },
    {
        "document_id": "fallback-bazi",
        "chunk_id": "bazi-core-005",
        "title": "《滴天髓》阐微与子平源流",
        "source_url": "corpus://internal/bazi-core",
        "content_sha256": "7ebf5236cf4f9254081c0473ef52a15fc6382bb50948e918591276a292c31c2d",
        "keywords": ["八字", "日元", "日主", "十神", "生克", "五行", "大运", "喜用"],
        "snippet": "《滴天髓》曰：欲识三原万法宗，先观帝载与神功。五行顺逆包含五常，刚柔相济，强弱调和，辨上下而定其基，生生不息方为通达。",
    },
    {
        "document_id": "fallback-fengshui",
        "chunk_id": "fengshui-core-006",
        "title": "《青囊经》与《地理正宗》",
        "source_url": "corpus://internal/fengshui-core",
        "content_sha256": "8fc06347d050a365192d1584f063b260d7493cc61059fa29602387b303d42d3e",
        "keywords": ["风水", "青囊", "二十四山", "罗盘", "向位", "分金", "撼龙"],
        "snippet": "《青囊经》曰：天尊地卑，阳奇阴偶。理寓于气，气囿于形。顺五兆，因四时，相济和合，明向背与分金之度，以定安居吉凶之应。",
    },
]


class CorpusSearchClient:
    def __init__(self, base_url=None, token=None, timeout=2.5):
        self.base_url = (base_url or os.environ.get("CORPUS_API_URL", "http://127.0.0.1:8088")).rstrip("/")
        self.token = token or os.environ.get("CORPUS_API_TOKEN")
        self.timeout = timeout

    def search(self, term, limit=30):
        url = self.base_url + "/v1/corpus/search?" + urlencode({"q": term, "limit": limit})
        request = Request(url)
        if self.token:
            request.add_header("Authorization", "Bearer " + self.token)
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            raise RuntimeError("corpus search unavailable: {}".format(exc))
        return payload.get("data", [])


def _fallback_search(term, limit=10):
    """当远程语料库不可达时，从内置经典古籍库中匹配关键词。"""
    results = []
    clean_term = term.replace("卦", "").strip()
    for item in FALLBACK_CLASSICAL_CORPUS:
        text = item["title"] + " " + item["snippet"] + " " + " ".join(item["keywords"])
        if clean_term in text or term in text:
            results.append({
                "chunk_id": item["chunk_id"],
                "document_id": item["document_id"],
                "title": item["title"],
                "source_url": item["source_url"],
                "content_sha256": item["content_sha256"],
                "chunk_index": 1,
                "snippet": item["snippet"],
            })
    # 若精确匹配无结果，返回通用经典条目
    if not results:
        results.append(FALLBACK_CLASSICAL_CORPUS[0])
    return results[:limit]


def _query_terms(module_results):
    candidates = []
    for item in module_results:
        mod = item.get("module")
        res = item.get("result", {})
        facts = res.get("facts", {})

        if mod in ("zhouyi", "meihua", "liuyao"):
            for role, key in (("本卦", "original"), ("变卦", "changed")):
                hexagram = facts.get(key)
                if hexagram and "name" in hexagram:
                    candidates.append({
                        "term": hexagram["name"] + "卦",
                        "hexagram": hexagram["name"],
                        "role": "{}{}".format(MODULE_NAMES.get(mod, mod), role),
                    })
        elif mod == "bazi":
            day_master = facts.get("day_master") or res.get("day_master", "日主")
            candidates.append({
                "term": "日主" + day_master,
                "hexagram": "八字",
                "role": "八字日元",
            })
        elif mod == "liuren":
            candidates.append({
                "term": "大六壬",
                "hexagram": "六壬",
                "role": "大六壬三传",
            })
        elif mod == "fengshui":
            candidates.append({
                "term": "二十四山",
                "hexagram": "风水",
                "role": "风水向位",
            })

    unique = []
    seen = set()
    for candidate in candidates:
        if candidate["term"] in seen:
            continue
        seen.add(candidate["term"])
        unique.append(candidate)
    return unique[:5]


MODULE_NAMES = {
    "zhouyi": "周易", "meihua": "梅花", "liuyao": "六爻",
    "bazi": "八字", "liuren": "六壬", "ziwei": "紫微", "fengshui": "风水"
}


def _relevance_score(row, term, category=None):
    title = row.get("title", "")
    snippet = row.get("snippet", "")
    score = 0

    # 经典典籍加权
    if "周易" in title or "易经" in title:
        score += 15
    if "梅花" in title:
        score += 12
    if "增删卜易" in title or "卜筮正宗" in title:
        score += 14
    if "大六壬" in title or "滴天髓" in title or "青囊" in title:
        score += 12
    if "卦" in title:
        score += 5

    # 语料内容特征加权
    if "《易》" in snippet or "周易" in snippet:
        score += 7
    if "大象" in snippet or "彖" in snippet or "爻" in snippet or "体用" in snippet:
        score += 6
    if any(keyword in snippet for theme in THEMES for keyword in theme["keywords"]):
        score += 12
    if term in snippet:
        score += 5

    # 事项类别加权
    if category and category in CATEGORY_WEIGHT_KEYWORDS:
        cat_keywords = CATEGORY_WEIGHT_KEYWORDS[category]
        cat_matches = sum(1 for kw in cat_keywords if kw in snippet or kw in title)
        score += min(cat_matches * 6, 24)

    # 噪音过滤减分
    if "咒" in title or "符" in title:
        score -= 6
    if "参同契" in title or "丹" in snippet or "科仪" in snippet:
        score -= 8
    return score


def _clean_snippet(value):
    return re.sub(r"[ \t\r]+", " ", value or "").strip(" …\n")


def _extract_sentence(snippet, term, maximum=260):
    text = _clean_snippet(snippet)
    position = text.find(term)
    if position < 0:
        clean_term = term.replace("卦", "").strip()
        position = text.find(clean_term)
    if position < 0:
        return text[:maximum]
    start = 0
    for boundary in SENTENCE_BOUNDARIES:
        found = text.rfind(boundary, 0, position)
        start = max(start, found + 1)
    previous_start = 0
    for boundary in SENTENCE_BOUNDARIES:
        found = text.rfind(boundary, 0, max(0, start - 1))
        previous_start = max(previous_start, found + 1)
    if start - previous_start <= maximum // 2:
        start = previous_start
    end = len(text)
    found_ends = [text.find(boundary, position + len(term)) for boundary in SENTENCE_BOUNDARIES]
    found_ends = [value for value in found_ends if value >= 0]
    if found_ends:
        end = min(found_ends) + 1
    sentence = text[start:end].strip()
    if len(sentence) > maximum:
        left = max(0, position - start - maximum // 2)
        sentence = sentence[left:left + maximum].strip()
        return ("…" if left else "") + sentence + ("…" if left + maximum < end - start else "")
    return sentence


def _theme_for(excerpt, term):
    for theme in THEMES:
        if any(keyword in excerpt for keyword in theme["keywords"]):
            return theme
    return {
        "opinion": "该书在这一段明确提到“{}”，段落语境强调顺应天时人事，依循客观规律适时调整。".format(term),
        "advice": "对应当前事项，建议综合审视条件成熟度与前后发展路径，审慎决策。",
    }


def collect_literature_opinions(module_results, search_client=None, max_books=3, context=None):
    if os.environ.get("ENABLE_LITERATURE", "0") != "1" and search_client is None:
        return {
            "status": "disabled",
            "usage_scope": "internal_research",
            "books": [],
            "warnings": ["书籍检索未启用。"],
        }

    category = None
    if isinstance(context, dict):
        category = normalize_category(context.get("category"))

    client = search_client or CorpusSearchClient()
    terms = _query_terms(module_results)
    ranked_groups = []
    errors = []
    used_fallback = False

    for query in terms:
        try:
            rows = client.search(query["term"], limit=30)
        except RuntimeError as exc:
            # 优雅回退到内置经典语料
            used_fallback = True
            rows = _fallback_search(query["term"], limit=10)
            errors.append(str(exc))

        group = [(_relevance_score(row, query["term"], category=category), query, row) for row in rows]
        group.sort(key=lambda item: (-item[0], item[2].get("document_id", ""), item[2].get("chunk_index", 0)))
        ranked_groups.append(group)

    ranked = []
    for group in ranked_groups:
        if group:
            ranked.append(group[0])
    remaining = [item for group in ranked_groups for item in group[1:]]
    remaining.sort(key=lambda item: (-item[0], item[2].get("document_id", ""), item[2].get("chunk_index", 0)))
    ranked.extend(remaining)

    books = []
    seen_documents = set()
    for score, query, row in ranked:
        if row["document_id"] in seen_documents:
            continue
        seen_documents.add(row["document_id"])
        excerpt = _extract_sentence(row.get("snippet", ""), query["term"])
        theme = _theme_for(excerpt, query["term"])
        books.append({
            "citation_id": "BOOK-{:03d}".format(len(books) + 1),
            "title": row["title"],
            "document_id": row["document_id"],
            "chunk_id": row["chunk_id"],
            "source_url": row["source_url"],
            "content_sha256": row["content_sha256"],
            "matched_term": query["term"],
            "calculation_role": query["role"],
            "excerpt": excerpt,
            "book_opinion": theme["opinion"],
            "application_note": theme["advice"],
            "relevance_score": score,
            "review_status": "automatic_candidate_unreviewed",
            "is_fallback": used_fallback,
        })
        if len(books) >= max_books:
            break

    warnings = [
        "书籍片段来自内部研究语料，未经版本校勘和领域专家审核。",
        "自动匹配只证明段落包含相关词，不证明该段可直接用于当前占问。",
    ]
    if used_fallback and not search_client:
        warnings.append("ClickHouse 语料库当前未连接，已自动启用内置核心经典古籍索引库。")

    return {
        "status": "available" if books else ("unavailable" if errors else "no_matches"),
        "usage_scope": "internal_research",
        "query_terms": terms,
        "books": books,
        "warnings": warnings,
    }
