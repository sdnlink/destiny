"""模块E：多方人物取象。

问题涉及两人及以上时，分别取各方专属用神，分别解析立场、心态、诉求。
支持针对单一人物深化解读，不重复完整大盘。
"""

from typing import Any, Dict, List, Optional


# 人物角色 → 六親/用神映射
ROLE_YONGSHEN_MAP = {
    "求测人": {"yongshen": "世爻/体卦", "nature": "自身立场、状态、能力"},
    "对方": {"yongshen": "应爻/用卦", "nature": "对方立场、态度、动向"},
    "领导/上级": {"yongshen": "官鬼爻/父母爻", "nature": "管理者、决策者、职权方"},
    "同事/同级": {"yongshen": "兄弟爻", "nature": "协作者、竞争者、资源分流方"},
    "下属/晚辈": {"yongshen": "子孙爻", "nature": "执行者、产出方、被管理方"},
    "客户/合作方": {"yongshen": "妻财爻/应爻", "nature": "资金来源、交易对手、利益相关方"},
    "长辈/父母": {"yongshen": "父母爻", "nature": "长辈、庇护方、文书资质方"},
    "竞争者": {"yongshen": "兄弟爻", "nature": "竞争对手、资源争夺方"},
    "中介/第三方": {"yongshen": "间爻/六合", "nature": "中间方、撮合者、信息传递方"},
}

# 非卦象体系没有世应/六亲，按本体系成立的人物符号取象
DOMAIN_PARTY_SYMBOLS = {
    "奇门遁甲": {
        "求测人": "日干",
        "对方": "时干",
        "领导/上级": "值符",
        "下属/晚辈": "值使",
        "客户/合作方": "时干",
        "竞争者": "时干",
        "中介/第三方": "中宫/值使",
    },
    "大六壬": {
        "求测人": "日干",
        "对方": "三传",
        "领导/上级": "三传",
        "下属/晚辈": "三传",
        "客户/合作方": "三传",
        "竞争者": "三传",
        "中介/第三方": "四课",
    },
    "八字命理": {
        "求测人": "日主",
        "对方": "对应十神（配偶/财官）",
        "领导/上级": "官星",
        "下属/晚辈": "食伤",
        "客户/合作方": "财星",
        "竞争者": "比劫",
        "长辈/父母": "印星",
    },
    "紫微斗数": {
        "求测人": "命宫",
        "对方": "夫妻宫/交友宫",
        "领导/上级": "官禄宫",
        "下属/晚辈": "仆役宫",
        "客户/合作方": "财帛宫",
        "竞争者": "交友宫",
        "长辈/父母": "父母宫",
    },
}


def detect_parties(question: str) -> List[str]:
    """从求测问题中识别涉及的人物角色。"""
    parties = ["求测人"]  # 始终包含求测人
    keywords = {
        "对方": "对方", "他": "对方", "她": "对方", "他们": "对方",
        "领导": "领导/上级", "老板": "领导/上级", "上级": "领导/上级", "主管": "领导/上级",
        "同事": "同事/同级", "合伙人": "同事/同级", "搭档": "同事/同级",
        "下属": "下属/晚辈", "员工": "下属/晚辈", "团队": "下属/晚辈",
        "客户": "客户/合作方", "合作方": "客户/合作方", "甲方": "客户/合作方", "乙方": "客户/合作方",
        "父母": "长辈/父母", "长辈": "长辈/父母", "家人": "长辈/父母",
        "竞争": "竞争者", "对手": "竞争者",
        "中介": "中介/第三方", "第三方": "中介/第三方", "介绍人": "中介/第三方",
    }
    # 「其他/其它」是泛指，不是人物；不剔除会让单字「他」误判出「对方」
    matching_text = question.replace("其他", "").replace("其它", "")
    for kw, role in keywords.items():
        if kw in matching_text and role not in parties:
            parties.append(role)
    # 如果涉及感情/合作但未明确对方，补充
    if any(kw in question for kw in ["感情", "恋爱", "婚姻", "合作", "合伙", "谈判"]):
        if "对方" not in parties:
            parties.append("对方")
    return parties


def analyze_multi_party(
    session,
    parties: Optional[List[str]] = None,
    focus_party: Optional[str] = None,
) -> Dict[str, Any]:
    """分析多方人物取象。

    Args:
        session: 推演会话（snapshot 已冻结）
        parties: 指定人物角色列表，None 则自动检测
        focus_party: 聚焦单一人物深化解读

    Returns:
        {
            "parties": 各方分析列表,
            "focus_party": 聚焦人物深化解读（如有）,
            "snapshot_unchanged": True,
        }
    """
    if session.snapshot is None:
        return {"error": "盘面尚未生成，请先执行排盘。"}

    if parties is None:
        parties = detect_parties(session.question or "")

    framework = _domain_framework(session)
    party_analyses = []
    for party in parties:
        if framework:
            party_analyses.append(_domain_party(party, framework))
            continue
        mapping = ROLE_YONGSHEN_MAP.get(party, {"yongshen": "应爻", "nature": "相关方"})
        analysis = {
            "party": party,
            "yongshen": mapping["yongshen"],
            "nature": mapping["nature"],
            "position": _infer_party_position(session, party),
            "mindset": _infer_party_mindset(session, party),
            "demands": _infer_party_demands(session, party),
        }
        party_analyses.append(analysis)

    result = {
        "parties": party_analyses,
        "snapshot_unchanged": True,  # 铁律：原始盘面不动
    }

    # 聚焦单一人物深化解读
    if focus_party:
        focus = next((p for p in party_analyses if p["party"] == focus_party), None)
        if focus:
            result["focus_party"] = {
                **focus,
                "deep_analysis": _deep_party_analysis(session, focus_party, framework),
            }

    return result


def _infer_party_position(session, party: str) -> str:
    """推断人物在事项中的位置（基于卦象）。"""
    if party == "求测人":
        return "世爻/体卦位置，代表求测人自身在事项中的立足点与状态"
    if party == "对方":
        return "应爻/用卦位置，代表对方在事项中的立场与态度"
    return f"基于{party}的角色定位，对应卦中相关爻位/卦象"


def _infer_party_mindset(session, party: str) -> str:
    """推断人物心态。"""
    if party == "求测人":
        return "求测人心态：关注事项走向，寻求确定性与行动指引，可能存在焦虑或期待"
    if party == "对方":
        return "对方心态：需结合应爻旺衰与动爻判断，旺则主动积极，衰则消极观望，动则有变化意图"
    return f"{party}心态：需结合其用神旺衰与卦中动变综合判断"


def _infer_party_demands(session, party: str) -> str:
    """推断人物诉求。"""
    if party == "求测人":
        return f"求测人核心诉求：在{session.category}事项中获得有利结果，寻求行动方向与风险预警"
    if party == "对方":
        return "对方核心诉求：需结合应爻所临六神、六亲推断，可能关注利益分配、控制权或关系稳定性"
    return f"{party}诉求：需结合其用神所临六亲六神与卦象综合推断"


def _domain_framework(session) -> str:
    """非卦象体系返回体系名，卦象体系返回空串。"""
    workflow = session.workflow_result or {}
    step3 = workflow.get("step3") or {}
    step4 = workflow.get("step4") or {}
    framework = step3.get("yongshen_framework") or step4.get("yongshen_framework") or ""
    return "" if framework in ("", "卦象体系") else framework


def _domain_party(party: str, framework: str) -> Dict[str, Any]:
    """非卦象体系的人物取象：只给本体系符号，不谈世应六亲。"""
    symbol = DOMAIN_PARTY_SYMBOLS.get(framework, {}).get(party, "本体系对应宫位/符号")
    return {
        "party": party,
        "yongshen": symbol,
        "nature": ROLE_YONGSHEN_MAP.get(party, {"nature": "相关方"})["nature"],
        "position": f"本盘为{framework}，没有世应爻位；{party}按{symbol}取象",
        "mindset": f"{party}心态：需结合{symbol}所在宫位/十神/三传的现实对应核对，本盘不套用六神六亲推断",
        "demands": f"{party}诉求：需结合{symbol}与用神的生克合冲关系，以及现实中的角色利益判断",
    }


def _deep_party_analysis(session, party: str, framework: str = "") -> str:
    """单一人物深化解读。"""
    if framework:
        symbol = DOMAIN_PARTY_SYMBOLS.get(framework, {}).get(party, "本体系对应宫位/符号")
        return (
            f"针对「{party}」的深化解读（{framework}口径）：\n"
            f"1. 取象符号：{symbol}\n"
            f"2. 盘面位置：在本体系中查该符号所在宫位/十神/三传，核对现实角色是否对应\n"
            f"3. 与用神关系：看{symbol}与用神（或用事宫）的生克合冲，判断配合度与阻力来源\n"
            f"4. 时间信号：结合本体系时间符号（节气/时辰、大运流年、大限）看其态度或行动的变化窗口\n"
            f"5. 边界说明：本盘未排卦象体系，不动用世应、六亲、六神概念"
        )
    return (
        f"针对「{party}」的深化解读：\n"
        f"1. 用神定位：{ROLE_YONGSHEN_MAP.get(party, {}).get('yongshen', '待确定')}\n"
        f"2. 旺衰状态：需结合月令日辰对该用神的生克冲合判断\n"
        f"3. 动变影响：该用神是否临动爻、是否被冲合，决定其行为动向\n"
        f"4. 六神临爻：临六神不同反映其心态与行为风格（青龙喜庆/朱雀口舌/勾陈拖延/螣蛇疑虑/白虎刚决/玄武隐秘）\n"
        f"5. 与求测人关系：世应生克关系反映双方互动模式与力量对比"
    )
