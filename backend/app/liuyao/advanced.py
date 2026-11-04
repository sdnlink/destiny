"""六爻进阶推导：用神候选、伏神出伏条件、刑害、三合局成局条件。

口径与依据：
- 用神/元神/忌神/仇神定义引自《增删卜易》用神元神忌神仇神章（本地语料检索原文）；
- 取舍次序（动>静、旺>衰、不空破>空破）按通行取舍法排序，仅作候选排序，不断吉凶；
- 伏神出伏条件、三合局成局条件引自《增删卜易》伏神章与三合局章原文（运行时从典籍库检索挂入 evidence）；
- 刑害为通行地支表，属确定组合关系，不涉断语。
"""

from app.common.five_elements import FIVE_ELEMENTS_CONTROLS, FIVE_ELEMENTS_GENERATES
from app.common.ganzhi import (
    BRANCH_CLASH, BRANCH_ELEMENTS, HAI_PAIRS, SELF_XING_BRANCHES, XING_PAIRS,
)

from .engine import HIDDEN_RELATIVE_ORDER


def _six_relative(palace_element, line_element):
    if palace_element == line_element:
        return "兄弟"
    if FIVE_ELEMENTS_GENERATES[line_element] == palace_element:
        return "父母"
    if FIVE_ELEMENTS_GENERATES[palace_element] == line_element:
        return "子孙"
    if FIVE_ELEMENTS_CONTROLS[line_element] == palace_element:
        return "官鬼"
    if FIVE_ELEMENTS_CONTROLS[palace_element] == line_element:
        return "妻财"
    raise ValueError("unknown five-element relationship")


# 用神取法表（通行口径，婚姻分男女占）。
FOCUS_TARGETS = {
    "自身": {"targets": ["世爻"], "note": "占自身以世爻为用神"},
    "父母长辈": {"targets": ["父母"]},
    "文书契约": {"targets": ["父母"]},
    "房屋宅舍": {"targets": ["父母"]},
    "子女晚辈": {"targets": ["子孙"]},
    "六畜医药": {"targets": ["子孙"]},
    "婚姻男占": {"targets": ["妻财"], "note": "男占婚姻取妻财为用神"},
    "婚姻女占": {"targets": ["官鬼"], "note": "女占婚姻取官鬼为用神"},
    "求财买卖": {"targets": ["妻财"], "support": "子孙", "note": "妻财为用神，子孙为元神（生财之源）"},
    "功名官职": {"targets": ["官鬼"]},
    "官司词讼": {"targets": ["官鬼"]},
    "疾病鬼祟": {"targets": ["官鬼"], "support": "子孙", "note": "官鬼为病症，子孙为医药"},
    "兄弟朋友": {"targets": ["兄弟"]},
}
FOCUS_ALIASES = {name: name for name in list(FOCUS_TARGETS) + list(HIDDEN_RELATIVE_ORDER) + ["世爻"]}

# 三合局五行之墓库：局成而局爻入墓者待冲开（引《增删卜易》三合局章）。
TRINE_TOMB = {"水": "辰", "木": "未", "火": "戌", "金": "丑"}


def _relative_for_element(palace_element, element):
    if not element:
        return ""
    return _six_relative(palace_element, element)


def _line_strength_rank(strength):
    return {"旺": 3, "相": 2, "休": 1, "囚": 0, "死": 0}.get(strength, 0)


def analyze_yongshen(focus, lines, changed_lines, coverage, palace):
    """按所问事项给出用神候选、元神忌神仇神与取舍排序，不断吉凶。"""
    normalized = FOCUS_ALIASES.get(focus or "")
    if not normalized:
        return None
    spec = FOCUS_TARGETS.get(normalized, {"targets": [normalized], "note": "直接以该六亲为用神"})
    targets = spec["targets"]
    support = spec.get("support")

    candidates = []
    for line in lines:
        hit = (
            ("世爻" in targets and "世" in line["roles"])
            or line["six_relative"] in targets
        )
        if hit:
            candidates.append(_candidate("本卦爻", line["position"], line))
    for hidden in coverage["hidden_spirits"]:
        if hidden["six_relative"] in targets:
            candidates.append({
                "source": "伏神", "position": hidden["position"],
                "branch": hidden["najia_branch"], "element": hidden["element"],
                "moving": False, "month_strength": "", "void_state": "",
                "is_month_break": False, "is_day_break": False, "roles": [],
            })
    for line, changed in zip(lines, changed_lines):
        if line["is_moving"] and changed["six_relative"] in targets:
            candidates.append({
                "source": "变爻", "position": line["position"],
                "branch": changed["najia_branch"], "element": changed["element"],
                "moving": True, "month_strength": line["month_strength"],
                "void_state": "", "is_month_break": False, "is_day_break": False,
                "roles": [],
            })
    for candidate in candidates:
        score = 0
        if candidate["moving"]:
            score += 4
        score += _line_strength_rank(candidate["month_strength"])
        if candidate["roles"]:
            score += 2
        if candidate["void_state"] or candidate["is_month_break"] or candidate["is_day_break"]:
            score -= 3
        candidate["rank_score"] = score
    candidates.sort(key=lambda item: (-item["rank_score"], item["position"]))

    target_elements = {
        candidate["element"] for candidate in candidates if candidate["element"]
    }
    meta = []
    if target_elements:
        element = sorted(target_elements)[0]
        meta = _meta_relatives(palace["element"], element, lines)

    return {
        "focus": focus,
        "normalized_focus": normalized,
        "targets": targets,
        "support": support,
        "note": spec.get("note", ""),
        "candidates": candidates,
        "selection_note": "用神多现时按 动>静、旺>衰、不空破>空破 排序，仅列候选次序，吉凶须结合典籍原文与问事语境复核。",
        "yuan_shen": meta.get("元神", []),
        "ji_shen": meta.get("忌神", []),
        "chou_shen": meta.get("仇神", []),
    }


def _candidate(source, position, line):
    return {
        "source": source,
        "position": position,
        "branch": line["najia_branch"],
        "element": line["element"],
        "moving": line["is_moving"] or line["is_dark_move"],
        "month_strength": line["month_strength"],
        "void_state": line["void_state"],
        "is_month_break": line["is_month_break"],
        "is_day_break": line["is_day_break"],
        "roles": line["roles"],
    }


def _meta_relatives(palace_element, target_element, lines):
    """元神（生用神）、忌神（克用神）、仇神（克元神生忌神）所对应六亲与本卦爻位。"""
    generating = next(e for e, v in FIVE_ELEMENTS_GENERATES.items() if v == target_element)
    controlling = next(e for e, v in FIVE_ELEMENTS_CONTROLS.items() if v == target_element)
    chou_element = next(e for e, v in FIVE_ELEMENTS_CONTROLS.items() if v == generating)
    result = {}
    for label, element in (("元神", generating), ("忌神", controlling), ("仇神", chou_element)):
        relative = _relative_for_element(palace_element, element)
        positions = [line["position"] for line in lines if line["six_relative"] == relative]
        result[label] = {"relative": relative, "element": element, "positions": positions}
    return result


def annotate_hidden_emerge(coverage, lines, month_branch, day_branch, month_element):
    """伏神出伏条件：空、破、日月克伤者不得出（《增删卜易》伏神章口径）。"""
    for hidden in coverage["hidden_spirits"]:
        branch = hidden["najia_branch"]
        element = hidden["element"]
        host = lines[hidden["position"] - 1]
        blockers = []
        if host["void_state"] == "旬空":
            blockers.append({"type": "旬空", "reason": "伏神值旬空"})
        if host["void_state"] == "填实":
            blockers.append({"type": "填实", "reason": "伏神空亡逢日辰填实，反可引出"})
        if BRANCH_CLASH.get(month_branch) == branch:
            blockers.append({"type": "月破", "reason": "伏神被月建冲破"})
        if host["is_day_break"]:
            blockers.append({"type": "日破", "reason": "伏神静而被日辰冲破"})
        if month_element and FIVE_ELEMENTS_CONTROLS.get(month_element) == element:
            blockers.append({"type": "月克", "reason": "月建克伏神"})
        if host["day_relation"] == "受克":
            blockers.append({"type": "日克", "reason": "日辰克伏神"})
        if host["day_relation"] == "冲" and not host["is_day_break"] and host["month_strength"] in ("旺", "相"):
            blockers.append({"type": "暗动", "reason": "伏神被日辰冲而暗动，反主引出"})
        hidden["emerge_blockers"] = blockers
        hidden["can_emerge"] = not any(
            item["type"] in ("旬空", "月破", "日破", "月克", "日克") for item in blockers
        )
    coverage["emerge_note"] = "伏神空破与受日月克伤者不得出，逢冲空、暗动、填实者反有引出之机；口径出自《增删卜易》伏神章，原文见 evidence。"


def _relation_marks(first, second):
    pair = frozenset((first, second))
    marks = []
    if first == second and first in SELF_XING_BRANCHES:
        marks.append(("自刑", pair))
    elif pair in XING_PAIRS:
        marks.append(("三刑", pair))
    if pair in HAI_PAIRS:
        marks.append(("六害", pair))
    return marks


def punishments_harms(lines, moving_branches, month_branch, day_branch):
    """动爻与月建、日辰之间的三刑、自刑、六害组合，不涉断语。"""
    pool = {}
    for position, branch in enumerate(
        (line["najia_branch"] for line in lines if line["is_moving"]), 1
    ):
        pool.setdefault(branch, []).append("动爻{}".format(position))
    for branch, source in ((month_branch, "月建"), (day_branch, "日辰")):
        if branch in BRANCH_ELEMENTS:
            pool.setdefault(branch, []).append(source)
    marks = []
    branches = sorted(pool)
    for index, first in enumerate(branches):
        for second in branches[index + 1:]:
            for label, _pair in _relation_marks(first, second):
                marks.append({
                    "type": label,
                    "branches": [first, second],
                    "members": [
                        {"branch": branch, "sources": sorted(set(pool[branch]))}
                        for branch in (first, second)
                    ],
                })
    for branch in branches:
        if branch in SELF_XING_BRANCHES and len(pool[branch]) >= 2:
            marks.append({
                "type": "自刑",
                "branches": [branch, branch],
                "members": [{"branch": branch, "sources": sorted(set(pool[branch]))}],
            })
    return {
        "marks": marks,
        "note": "三刑（寅巳申、丑戌未、子卯、辰午酉亥自刑）与六害（子未、丑午、寅巳、卯辰、申亥、酉戌）为通行地支组合表，仅列组合事实。",
    }


def assess_sanhe_conditions(structures, lines):
    """按《增删卜易》三合局章口径评估成局条件：全动成局、两动待补凑（虚待用）、空破待填、入墓待冲开。"""
    assessments = []
    for group in structures["sanhe"]:
        moving_sources = 0
        issues = []
        for member in group["members"]:
            sources = member["sources"]
            branch = member["branch"]
            if any(source.startswith("动爻") for source in sources):
                line = next(
                    (item for item in lines if item["najia_branch"] == branch and item["is_moving"]),
                    None,
                )
                if line is not None:
                    moving_sources += 1
                    if line["void_state"] == "旬空":
                        issues.append("{}爻值旬空，待填实之日月成局".format(line["position"]))
                    elif line["is_month_break"]:
                        issues.append("{}爻值月破，待填满成局".format(line["position"]))
            else:
                issues.append("{}支来自{}，须待引动".format(branch, "、".join(sources)))
        if moving_sources == 3 and not issues:
            status = "成局"
        elif moving_sources == 3:
            status = "成局但待填实"
        else:
            status = "不成局（待补凑，虚待用口径）"
        tomb = TRINE_TOMB.get(group["element"])
        if tomb and tomb in group["branches"]:
            issues.append("局中{}为{}之墓，待冲开之日成之".format(tomb, group["element"]))
        assessments.append({
            "element": group["element"],
            "branches": group["branches"],
            "moving_member_count": moving_sources,
            "status": status,
            "conditions": issues,
        })
    return assessments
