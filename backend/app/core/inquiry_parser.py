"""Inquiry intent parser extracting semantic targets from user questions."""

import re
from typing import Any, Dict, List, Set

INTENT_KEYWORDS = {
    "clothing_color": [
        "衣服", "颜色", "穿", "着装", "服饰", "色彩", "上衣", "裤子", "裙子", "外套", "穿戴", "色系", "何色", "什么色"
    ],
    "current_activity": [
        "在做什么", "做什么事情", "做什么事", "干什么", "正在做", "活动", "动态", "举动", "行为", "在干嘛", "在忙什么", "当前状态", "正在", "动作", "事由"
    ],
    "location_direction": [
        "在哪里", "在何处", "哪儿", "去向", "方位", "地点", "场所", "环境", "位置", "方向", "哪个方向", "何方", "所处"
    ],
    "character_state": [
        "状态", "心情", "情绪", "性格", "相貌", "长相", "外貌", "心思", "态度", "想法", "健康", "精神"
    ],
    "item_nature": [
        "什么东西", "物品", "材质", "形状", "丢了", "寻找", "失物", "钱包", "钥匙", "文件", "射覆", "何物"
    ],
    "outcome_timing": [
        "吉凶", "成败", "结果", "如何", "能否", "可否", "应期", "何时", "什么时候", "顺利吗", "前景", "走势", "合作", "投资", "工作"
    ],
}


def parse_inquiry_intent(question: str, category: str = "other") -> Dict[str, Any]:
    """Parse user question to extract specific inquiry intents and targets."""
    text = (question or "").strip()
    detected_intents: Set[str] = set()

    for intent, keywords in INTENT_KEYWORDS.items():
        for kw in keywords:
            if kw in text:
                detected_intents.add(intent)
                break

    # If no specific intent matched via keywords, fallback to outcome_timing
    if not detected_intents:
        detected_intents.add("outcome_timing")

    # Extract subject entity if present (e.g. "推算李笑穿的是什么..." -> "李笑")
    subject = ""
    match = re.search(r"(?:推算|测|算|问|看|占)?([\u4e00-\u9fa5]{2,4}?)(?:穿|在|去|的|是否|能否|现在|今天)", text)
    if match:
        candidate = match.group(1).strip()
        noise = {"什么", "对方", "自己", "我们", "他们", "关于", "近期", "本次", "项目", "工作", "公司"}
        if candidate and candidate not in noise:
            subject = candidate

    return {
        "raw_question": text,
        "category": category,
        "intents": sorted(detected_intents),
        "has_clothing_color": "clothing_color" in detected_intents,
        "has_current_activity": "current_activity" in detected_intents,
        "has_location_direction": "location_direction" in detected_intents,
        "has_character_state": "character_state" in detected_intents,
        "has_item_nature": "item_nature" in detected_intents,
        "has_outcome_timing": "outcome_timing" in detected_intents,
        "subject": subject or "求问主体",
    }
