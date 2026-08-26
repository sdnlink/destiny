"""模块A：起盘前信息补全。

信息残缺按需选取最多3项询问，禁止一次性大量提问。
用户回复"直接起盘，不用多问"则跳过询问，使用默认起盘。
"""

from typing import Any, Dict, List, Optional


# 补全问题模板
COMPLETION_QUESTIONS = {
    "casting_method": {
        "question": "是否指定起盘方式？可选：报数起卦、当下时间起卦、事件发生时间起卦。不指定则默认自动起卦。",
        "field": "casting_method",
    },
    "gender_age": {
        "question": "求测人性别与大致年龄？（用于八字/紫微等需性别参数的体系，以及用神取向）",
        "field": "user_profile.gender_age",
    },
    "current_stage": {
        "question": "事件当前所处阶段与简单现状？（有助于定用神与取象映射，例如：尚未开始/进行中遇阻/已出结果待抉择）",
        "field": "user_profile.current_stage",
    },
    "system": {
        "question": "是否指定术数门类？可选：梅花易数（默认）、六爻纳甲、奇门遁甲、大六壬。不指定则默认主用梅花+六爻辅助。",
        "field": "system",
    },
}


def detect_missing(session) -> List[str]:
    """检测会话中缺失的信息，返回需要补全的字段列表（最多3项）。"""
    missing = []

    # 起盘方式
    if not session.casting_method or session.casting_method == "auto":
        if not session.casting_source.get("cast_nonce"):
            missing.append("casting_method")

    # 性别年龄（如果涉及八字/紫微/感情类）
    if session.category in ("relationship", "health") or session.system in ("bazi", "ziwei", "auto"):
        if not session.user_profile.get("gender"):
            missing.append("gender_age")

    # 当前阶段
    if not session.user_profile.get("current_stage"):
        missing.append("current_stage")

    # 术数门类（如果未指定）
    if not session.system or session.system == "auto":
        missing.append("system")

    return missing[:3]


def generate_completion_prompt(session) -> Dict[str, Any]:
    """生成信息补全提示。

    Returns:
        {
            "type": "info_completion",
            "questions": [{field, question}],
            "instruction": "请回复以上信息，或回复'直接起盘，不用多问'跳过。",
            "skip_keyword": "直接起盘，不用多问",
        }
    """
    missing = detect_missing(session)
    if not missing:
        return {
            "type": "info_completion",
            "questions": [],
            "instruction": "信息已充足，可直接起盘。",
            "ready": True,
        }

    questions = []
    for field in missing:
        template = COMPLETION_QUESTIONS.get(field)
        if template:
            questions.append({"field": template["field"], "question": template["question"]})

    return {
        "type": "info_completion",
        "questions": questions,
        "instruction": "请逐项回复以上信息（最多3项），或回复\"直接起盘，不用多问\"使用默认方式起盘。",
        "skip_keyword": "直接起盘，不用多问",
        "ready": False,
    }


def apply_completion_answers(session, answers: Dict[str, Any]) -> Any:
    """应用用户的补全答案到会话。

    Args:
        answers: {field: value}，field 对应 COMPLETION_QUESTIONS 中的 field

    Returns:
        更新后的 session
    """
    for field, value in answers.items():
        if field == "casting_method":
            session.casting_method = value
        elif field == "system":
            session.system = value
        elif field.startswith("user_profile."):
            key = field.replace("user_profile.", "")
            session.user_profile[key] = value
    return session
