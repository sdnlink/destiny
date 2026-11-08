"""铁板神数（铁版神数）能力状态：如实声明数据缺口，不伪造条文或断语。

铁板神数的核心是「考刻定分 → 条文编号 → 条文断语」：以生辰干支加时辰刻度
推出一个条文序号，再查对应底本条文（如六亲、流年条目）。经核查本仓库：
- 本地典籍库（data/generated/wikisource-corpus/corpus_documents.jsonl）无
  《铁板神数》《鐵版神數》或任何条文底本；
- 无条文编号表、无考刻/校时算法、无四柱→条数映射；
- 全仓无条文库数据。

在此前提下**不得输出任何条数、条文或断语**（那将是编造）。本模块只提供
可读的能力状态与「若要实现所需的资料清单」，供后续按来源/版本补录。
"""
from app.common.classics import get_library

RULE_ID = "BZ-TIEBAN-STATUS-001"
STATUS = "data_gap_pending_source_acquisition"
SCHOOL = "tieban-shenshu-not-implemented"

MISSING = (
    {"item": "条文底本", "detail": "本地典籍库无《铁板神数》类书名，条文原文未入库",
     "needed": "确定版本底本（含卷次、条文编号、条文全文）并取得可公开使用的来源"},
    {"item": "条文编号表", "detail": "无条数索引与编号→条文映射",
     "needed": "编号表与校勘记录，逐条可追溯"},
    {"item": "考刻/校时算法", "detail": "无时辰刻度划分与考刻定分口径",
     "needed": "据底本明文还原推数步骤，并建立标准案例逆行验证"},
    {"item": "四柱→条数映射", "detail": "无命盘干支到条文的确定性映射规则",
     "needed": "映射规则原文 + 专家签署的标准案例"},
    {"item": "标准验证案例", "detail": "data/validation-cases 无铁板神数案例",
     "needed": "带已知条数的案例集，用于回归"},
)


def tieban_status() -> dict:
    """返回铁板神数能力状态与所需资料清单（不含任何条数或断语）。"""
    library = get_library()
    exact_titles = []
    related_titles = []
    try:
        if library.available:
            for row in library.evidence(
                ("鐵板", "铁板", "神數", "神数", "條文", "条文"),
                category="mingli", per_query=2, limit=12,
            ):
                title = row.get("title", "")
                if "鐵板" in title or "铁板" in title or "鐵版" in title or "铁版" in title:
                    exact_titles.append(title)
                elif title:
                    related_titles.append(title)
    except Exception:
        pass
    return {
        "schema_version": "1.0",
        "rule_id": RULE_ID,
        "system": "tieban",
        "school": SCHOOL,
        "status": STATUS,
        "implemented": False,
        "available_capabilities": [],
        "unavailable_capabilities": [
            "考刻定分", "条文编号推数", "条文查询", "六亲/流年条文断语",
        ],
        "missing_prerequisites": [dict(item) for item in MISSING],
        "tieban_corpus_titles": sorted(set(exact_titles)),
        "related_but_not_tieban_titles": sorted(set(related_titles)),
        "corpus_note": "按书名精确核查：本地典籍库无《铁板神数》类条文底本；"
                      "related_but_not_tieban_titles 仅为「神数/条文」泛词命中的其他典籍，不能作为铁板依据。",
        "judgements": [],
        "warnings": [
            "铁板神数条文底本、编号表、考刻算法与映射规则均未入库，系统不生成任何条数或断语。",
            "在取得可追溯底本与专家签署的标准案例前，本状态端点不提供推算能力。",
            "本端点仅声明资料缺口，任何「条数/条文」输出都应视为伪造。",
        ],
    }


__all__ = ("tieban_status", "RULE_ID", "STATUS")
