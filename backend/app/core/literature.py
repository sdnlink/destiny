import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


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
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            raise RuntimeError("corpus search unavailable: {}".format(exc))
        return payload.get("data", [])


def _query_terms(module_results):
    candidates = []
    for item in module_results:
        if item["module"] not in ("zhouyi", "meihua", "liuyao"):
            continue
        facts = item["result"]["facts"]
        for role, key in (("本卦", "original"), ("变卦", "changed")):
            hexagram = facts[key]
            candidates.append({
                "term": hexagram["name"] + "卦",
                "hexagram": hexagram["name"],
                "role": "{}{}".format(MODULE_NAMES[item["module"]], role),
            })
    unique = []
    seen = set()
    for candidate in candidates:
        if candidate["term"] in seen:
            continue
        seen.add(candidate["term"])
        unique.append(candidate)
    return unique[:4]


MODULE_NAMES = {"zhouyi": "周易", "meihua": "梅花", "liuyao": "六爻"}


def _relevance_score(row, term):
    title = row.get("title", "")
    snippet = row.get("snippet", "")
    score = 0
    if "周易" in title:
        score += 12
    if "易" in title:
        score += 8
    if "卦" in title:
        score += 5
    if "梅花" in title:
        score += 10
    if "《易》" in snippet or "周易" in snippet:
        score += 7
    if "大象" in snippet or "彖" in snippet or "爻" in snippet:
        score += 5
    if any(keyword in snippet for theme in THEMES for keyword in theme["keywords"]):
        score += 12
    if term in snippet:
        score += 3
    if "咒" in title or "符" in title:
        score -= 4
    if "参同契" in title or "丹" in snippet or "科仪" in snippet:
        score -= 8
    return score


def _clean_snippet(value):
    return re.sub(r"[ \t\r]+", " ", value or "").strip(" …\n")


def _extract_sentence(snippet, term, maximum=260):
    text = _clean_snippet(snippet)
    position = text.find(term)
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
        "opinion": "该书在这一段明确提到“{}”，但段落语境未形成可直接用于当前事项的完整断语。".format(term),
        "advice": "应先阅读前后文和版本说明，再决定是否采用其中观点。",
    }


def collect_literature_opinions(module_results, search_client=None, max_books=3):
    if os.environ.get("ENABLE_LITERATURE", "0") != "1" and search_client is None:
        return {
            "status": "disabled",
            "usage_scope": "internal_research",
            "books": [],
            "warnings": ["书籍检索未启用。"],
        }
    client = search_client or CorpusSearchClient()
    terms = _query_terms(module_results)
    ranked_groups = []
    errors = []
    for query in terms:
        try:
            rows = client.search(query["term"], limit=30)
        except RuntimeError as exc:
            errors.append(str(exc))
            continue
        group = [(_relevance_score(row, query["term"]), query, row) for row in rows]
        group.sort(key=lambda item: (-item[0], item[2].get("document_id", ""), item[2].get("chunk_index", 0)))
        ranked_groups.append(group)

    ranked = []
    # Preserve one candidate per distinct hexagram before filling remaining slots.
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
        })
        if len(books) >= max_books:
            break

    warnings = [
        "书籍片段来自内部研究语料，未经版本校勘和领域专家审核。",
        "自动匹配只证明段落包含相关词，不证明该段可直接用于当前占问。",
    ]
    warnings.extend(errors)
    return {
        "status": "available" if books else ("unavailable" if errors else "no_matches"),
        "usage_scope": "internal_research",
        "query_terms": terms,
        "books": books,
        "warnings": warnings,
    }
