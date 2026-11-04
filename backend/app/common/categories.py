"""事项分类唯一真源。

历史上 API、建议、标签、文献加权、用神映射各自维护了一份分类键名，
导致「官司/寻人/失物/健康/抉择」等类别静默落到 other 分支，
文献加权对 finance/relationship/study 永不生效。
所有模块必须引用本模块，禁止再自定义分类字符串。
"""

from types import MappingProxyType

CATEGORIES = (
    "career",
    "finance",
    "relationship",
    "study",
    "lawsuit",
    "travel",
    "missing_person",
    "lost_item",
    "health",
    "decision",
    "other",
)

CATEGORY_LABELS = MappingProxyType({
    "career": "事业",
    "finance": "财运",
    "relationship": "感情姻缘",
    "study": "考试学业",
    "lawsuit": "官司是非",
    "travel": "出行",
    "missing_person": "寻人",
    "lost_item": "失物",
    "health": "健康",
    "decision": "抉择",
    "other": "其他谋事",
})


# 历史键名 → 规范键名。旧数据、旧前端请求可能仍带这些键名。
LEGACY_CATEGORY_ALIASES = MappingProxyType({
    "wealth": "finance",
    "money": "finance",
    "marriage": "relationship",
    "love": "relationship",
    "academics": "study",
    "exam": "study",
    "job": "career",
    "work": "career",
    "litigation": "lawsuit",
    "trip": "travel",
    "missing": "missing_person",
    "lost": "lost_item",
})


def normalize_category(value, strict=False):
    """把历史别名归一为规范分类键。

    strict=True 时未知分类直接报错（写入口必须拒绝脏数据）；
    默认宽松模式把未知值收敛到 other，用于读取侧兜底。
    """
    if not isinstance(value, str):
        if strict:
            raise ValueError("category must be a string, got {!r}".format(value))
        return "other"
    key = value.strip()
    if key in CATEGORIES:
        return key
    if key in LEGACY_CATEGORY_ALIASES:
        return LEGACY_CATEGORY_ALIASES[key]
    if strict:
        raise ValueError("unsupported category: {}".format(value))
    return "other"


def category_label(value):
    return CATEGORY_LABELS[normalize_category(value)]
