CATEGORY_PROFILES = {
    "career": {
        "label": "事业",
        "objective": "把目标、决策权限和时间窗口说清楚",
        "recommendations": [
            ("明确下一阶段唯一主目标，并写出可验收的完成标准。", "避免同时追逐多个模糊目标。"),
            ("列出关键决策人、协作者和资源缺口，逐项确认承诺。", "把口头支持转换为时间、人员或预算。"),
            ("先做一个可逆的小范围验证，再决定是否扩大投入。", "用实际反馈修正假设。"),
        ],
        "questions": ["谁拥有最终决定权？", "最晚需要在什么时间点作出决定？", "失败时可以承受的最大时间和资源成本是多少？"],
    },
    "finance": {
        "label": "财务",
        "objective": "先确认现金流、损失上限和退出条件",
        "recommendations": [
            ("把收入、固定支出、可变支出和最坏情形分别量化。", "不要用单一乐观预测代替现金流测算。"),
            ("在行动前确定最大损失和停止条件。", "达到边界时按预案执行，不临时追加风险。"),
            ("核对合同、税费、期限和流动性限制。", "重点检查不能快速撤回的承诺。"),
        ],
        "questions": ["最坏情形会损失多少？", "资金被占用的最长时间是多少？", "哪些数据来自可核验记录而不是口头预期？"],
    },
    "relationship": {
        "label": "关系",
        "objective": "区分事实、感受、需求和边界",
        "recommendations": [
            ("分别记录已发生的事实和自己的解释，避免把推测当成事实。", "先减少信息误差，再讨论立场。"),
            ("用一次直接、具体且不指责的沟通确认彼此需求。", "讨论可观察行为和时间安排。"),
            ("设定双方都能执行的边界，并观察后续行为是否一致。", "持续行为比一次表态更有参考价值。"),
        ],
        "questions": ["双方已经明确表达了什么？", "哪些判断仍只是推测？", "不能接受的边界和可协商部分分别是什么？"],
    },
    "travel": {
        "label": "出行",
        "objective": "优先检查时间、交通和备选方案",
        "recommendations": [
            ("核对证件、天气、交通状态和目的地限制。", "以官方实时信息为准。"),
            ("为关键衔接预留缓冲时间，并准备替代路线。", "避免单点延误破坏全部安排。"),
            ("把紧急联系人、保险和必要资料离线保存。", "确保网络或设备异常时仍可使用。"),
        ],
        "questions": ["哪个环节最容易造成连锁延误？", "取消或变更的成本是多少？", "出现突发情况时由谁作决定？"],
    },
    "study": {
        "label": "学业",
        "objective": "把学习目标转化为可测试的能力",
        "recommendations": [
            ("把目标拆成每周可完成、可检查的输出。", "用练习和复述替代只看材料。"),
            ("先定位最薄弱的知识环节，再安排集中练习。", "不要平均分配有限时间。"),
            ("建立定期模拟和错题复盘节奏。", "根据结果调整计划，而不是只增加时长。"),
        ],
        "questions": ["最终需要通过什么形式验收？", "当前失分或卡点主要来自哪里？", "每周能稳定投入的时间是多少？"],
    },
    "other": {
        "label": "其他",
        "objective": "明确问题边界、关键变量和可逆行动",
        "recommendations": [
            ("把期望结果、当前条件和主要障碍分别写清楚。", "先确认真正需要解决的问题。"),
            ("区分可控制、可影响和不可控制的因素。", "优先投入可产生反馈的部分。"),
            ("选择一个成本可控的下一步，并提前设定复盘时间。", "根据实际结果继续、调整或停止。"),
        ],
        "questions": ["最重要的结果是什么？", "当前缺少的关键信息是什么？", "最小可验证行动是什么？"],
    },
}


RELATION_GUIDANCE = {
    "same_element": {
        "focus": "先校准共识，再推进细节",
        "rationale": "梅花本卦阶段呈现体用比和，体与用属于同一五行，可将其作为检查目标一致性和协作节奏的提示。",
        "action": ("确认相关各方对目标、范围和完成标准是否一致。", "即使方向相近，也要排除职责和时间理解不同。"),
    },
    "use_generates_body": {
        "focus": "识别外部支持，并验证支持能否兑现",
        "rationale": "梅花本卦阶段呈现用生体，可将其作为检查外部资源、信息或协作者支持的提示。",
        "action": ("把可能的外部支持转换为可确认的资源、负责人和时间。", "不要仅依据善意表达安排关键路径。"),
    },
    "body_generates_use": {
        "focus": "控制投入，避免资源持续外流",
        "rationale": "梅花本卦阶段呈现体生用，可将其作为检查时间、精力或资金投入强度的提示。",
        "action": ("为投入设置预算、期限和阶段验收点。", "若连续投入没有产生可见反馈，应及时复盘。"),
    },
    "use_controls_body": {
        "focus": "先处理外部约束，再决定推进速度",
        "rationale": "梅花本卦阶段呈现用克体，可将其作为检查规则、对手方、环境或资源限制的提示。",
        "action": ("列出当前无法自行改变的约束，并为每项准备应对或退出方案。", "不要把外部限制误当成仅靠意愿可以解决的问题。"),
    },
    "body_controls_use": {
        "focus": "运用已有控制力，但保留余量",
        "rationale": "梅花本卦阶段呈现体克用，可将其作为检查自身可控资源和执行能力的提示。",
        "action": ("明确当前真正可控制的变量，并优先形成一个可验证结果。", "避免因局部可控而低估后续成本。"),
    },
}


def _find_module(module_results, name):
    for item in module_results:
        if item["module"] == name:
            return item["result"]
    return None


def generate_advisory(module_results, context):
    if not context:
        return None
    category = context["category"]
    question = context["question_summary"].strip()
    if category not in CATEGORY_PROFILES:
        raise ValueError("unsupported advisory category: {}".format(category))
    profile = CATEGORY_PROFILES[category]
    meihua = _find_module(module_results, "meihua")
    zhouyi = _find_module(module_results, "zhouyi")

    guidance = None
    evidence_basis = []
    if meihua and meihua.get("evidence"):
        original_evidence = next(
            (item for item in meihua["evidence"] if item.get("stage") == "original"),
            meihua["evidence"][0],
        )
        guidance = RELATION_GUIDANCE.get(original_evidence["code"])
        evidence_basis.append({
            "module": "meihua",
            "fact": original_evidence["label"],
            "rule_ids": original_evidence["rule_ids"],
        })

    if guidance:
        focus = guidance["focus"]
        rationale = guidance["rationale"]
    else:
        focus = profile["objective"]
        rationale = "当前可用模块没有已登记的体用关系，建议优先按事项类别检查目标、条件和风险。"

    change_text = ""
    if zhouyi:
        moving = zhouyi["facts"]["moving_lines"]
        evidence_basis.append({
            "module": "zhouyi",
            "fact": "动爻{}".format("、".join(str(value) for value in moving) if moving else "无"),
            "rule_ids": ["YI-RELATION-001"],
        })
        if not moving:
            change_text = "周易结果没有动爻，可把重点放在检查既有条件和原假设，而不是预设短期内自然发生明显变化。"
        elif len(moving) == 1:
            change_text = "周易结果的变化集中在第{}爻，可把本次事项拆出一个最关键变量单独验证。".format(moving[0])
        else:
            change_text = "周易结果包含多处动爻，可把它视为多变量联动提示，避免一次性作出不可逆决定。"

    recommendations = []
    if guidance:
        recommendations.append({
            "priority": 1,
            "title": guidance["action"][0],
            "detail": guidance["action"][1],
            "basis": rationale,
            "rule_ids": ["ADV-MH-RELATION-001", "MH-FIVE-ELEMENT-001"],
        })
    for index, (title, detail) in enumerate(profile["recommendations"], len(recommendations) + 1):
        recommendations.append({
            "priority": index,
            "title": title,
            "detail": detail,
            "basis": "{}事项建议模板".format(profile["label"]),
            "rule_ids": ["ADV-CONTEXT-001"],
        })

    return {
        "schema_version": "1.0",
        "status": "provisional_research_advice",
        "review_status": "unreviewed_engineering_template",
        "context": {
            "category": category,
            "category_label": profile["label"],
            "question_summary": question,
        },
        "conclusion": {
            "headline": focus,
            "text": "针对“{}”，当前推演更适合把注意力放在：{}。{}{}".format(
                question, profile["objective"], rationale, " " + change_text if change_text else ""
            ),
            "polarity": "indeterminate",
            "confidence_label": "不评估现实概率",
        },
        "recommendations": recommendations,
        "verification_questions": list(profile["questions"]),
        "evidence_basis": evidence_basis,
        "risk_notes": [
            "建议来自未审核的工程模板，只能作为问题整理和决策检查清单。",
            "涉及医疗、法律、投资、安全等高影响事项时，应以具备资质的专业意见和可核验数据为准。",
            "不要仅依据本推演作出不可逆、超出承受范围或影响他人权益的决定。",
        ],
        "rule_ids": ["ADV-CONTEXT-001"] + (["ADV-MH-RELATION-001"] if guidance else []),
    }
