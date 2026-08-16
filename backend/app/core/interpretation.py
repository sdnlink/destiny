MODULE_LABELS = {"zhouyi": "周易", "meihua": "梅花易数", "liuyao": "六爻", "liuren": "大六壬"}
CATEGORY_LABELS = {"career": "事业", "finance": "财务", "relationship": "关系", "travel": "出行", "study": "学业", "other": "当前事项"}
RELATIVE_MEANINGS = {
    "父母": "文书、规则、资质、信息或支持条件",
    "兄弟": "同类、同事、协作者、竞争者或资源分配",
    "子孙": "产出、方案、反馈、缓冲或执行结果",
    "妻财": "资金、资源、交易成果或可支配条件",
    "官鬼": "职责、约束、风险、压力或必须处理的问题",
}
RELATION_MEANINGS = {
    "same_element": "体用同属一行，可优先核对双方目标、标准和节奏是否真正一致",
    "use_generates_body": "用生体，可优先核对外部支持、资源或信息是否能够实际兑现",
    "body_generates_use": "体生用，可优先核对自身投入是否持续外流，以及投入是否形成反馈",
    "use_controls_body": "用克体，可优先核对外部规则、环境或对手方形成的约束",
    "body_controls_use": "体克用，可优先核对自身真正能够控制的变量和执行余量",
}


def _find(module_results, name):
    return next((item["result"] for item in module_results if item["module"] == name), None)


def _imagery_for(imagery, module, roles=None):
    rows = []
    for candidate in (imagery or {}).get("candidates", []):
        if candidate["module"] != module or (roles and candidate["role"] not in roles):
            continue
        phrases = []
        for dimension, values in candidate["selected_imagery"].items():
            phrases.append("{}可联想到{}".format(dimension, "、".join(values)))
        rows.append({
            "candidate_id": candidate["candidate_id"], "role": candidate["role"],
            "symbol": candidate["symbol"], "text": "；".join(phrases),
        })
    return rows


def _zhouyi(result, imagery):
    facts = result["facts"]
    moving = facts["moving_lines"]
    imagery_rows = _imagery_for(imagery, "zhouyi")
    if not moving:
        change = "没有动爻，解释重点放在核对现有结构和原有假设。"
    elif len(moving) == 1:
        change = "变化集中在第{}爻，适合把当前事项拆出一个关键变量单独核实。".format(moving[0])
    else:
        change = "共有{}处动爻，表示模型中存在多个变化位置，应分别核实，避免合并成单一原因。".format(len(moving))
    correspondence = "本卦{}描述起卦时的结构，变卦{}只表示动爻转换后的结构。{}".format(
        facts["original"]["name"], facts["changed"]["name"], change
    )
    if imagery_rows:
        correspondence += " 本卦上下卦的事项类象包括：{}。".format("；".join(row["text"] for row in imagery_rows[:2]))
    return {
        "module": "zhouyi", "title": "周易：现状结构与变化位置",
        "chart_fact": "{}卦，动爻{}，变{}卦。".format(facts["original"]["name"], "、".join(map(str, moving)) if moving else "无", facts["changed"]["name"]),
        "correspondence": correspondence,
        "verification": "核对当前事项中哪些条件已经存在，哪些条件正对应动爻所代表的变化位置；不要只凭卦名确定结果。",
        "evidence_refs": [row["candidate_id"] for row in imagery_rows],
        "rule_ids": ["INTERP-CORRESPONDENCE-001", "YI-RELATION-001", "XIANG-CONTEXT-001"],
    }


def _meihua(result, imagery):
    facts = result["facts"]
    body_use = facts["body_use"]
    original_evidence = next((item for item in result["evidence"] if item["stage"] == "original"), result["evidence"][0])
    relation_text = RELATION_MEANINGS[original_evidence["code"]]
    imagery_rows = _imagery_for(imagery, "meihua", {"body", "use", "changed_use"})
    body_image = next((row["text"] for row in imagery_rows if row["role"] == "body"), "")
    use_image = next((row["text"] for row in imagery_rows if row["role"] == "use"), "")
    return {
        "module": "meihua", "title": "梅花：主体、外部条件与作用关系",
        "chart_fact": "体卦{}、用卦{}，本卦阶段为{}。".format(body_use["body_trigram"]["name"], body_use["use_trigram"]["name"], original_evidence["label"]),
        "correspondence": "体用于本次解释中分别作为主体和作用条件的观察位置。{}。体卦类象：{}；用卦类象：{}。".format(relation_text, body_image or "暂无", use_image or "暂无"),
        "verification": "先明确谁或什么是本次事项的主体，再核对外部条件、资源投入和约束是否与体用位置相符。",
        "evidence_refs": [original_evidence["evidence_id"]] + [row["candidate_id"] for row in imagery_rows],
        "rule_ids": ["INTERP-CORRESPONDENCE-001", "MH-BODYUSE-001", "MH-FIVE-ELEMENT-001", "XIANG-CONTEXT-001"],
    }


def _liuyao(result, imagery):
    facts = result["facts"]
    moving_lines = [line for line in facts["line_chart"] if line["is_moving"]]
    moving_texts = []
    for line in moving_lines:
        status = []
        if line["roles"]:
            status.append("、".join(line["roles"]))
        if line["is_void"]:
            status.append("旬空")
        moving_texts.append("第{}爻{}，对应{}{}".format(
            line["position"], line["six_relative"], RELATIVE_MEANINGS[line["six_relative"]],
            "，并处于{}".format("、".join(status)) if status else "",
        ))
    imagery_rows = _imagery_for(imagery, "liuyao", {"palace"})
    return {
        "module": "liuyao", "title": "六爻：角色关系与动爻落点",
        "chart_fact": "{}宫{}，世爻第{}爻，应爻第{}爻；{}。".format(
            facts["palace"]["name"], facts["palace"]["stage"], facts["palace"]["host_line"],
            facts["palace"]["response_line"], "；".join(moving_texts) if moving_texts else "无动爻",
        ),
        "correspondence": "世应只标记模型中的主体与对应位置，六亲用于分类可能涉及的角色和条件。{}。".format("；".join(moving_texts) if moving_texts else "当前应先核对静态角色配置"),
        "verification": "把动爻六亲转换成现实检查项，并核对世应双方、文书资源和约束条件；旬空只作为盘面状态，不等同于现实中必然不存在。",
        "evidence_refs": [row["candidate_id"] for row in imagery_rows],
        "rule_ids": ["INTERP-CORRESPONDENCE-001", "LY-PALACE-001", "LY-RELATIVE-001", "CYCLE-XUN-001"],
    }


def _liuren(result, imagery):
    facts = result["facts"]
    transmissions = facts["three_transmissions"]
    imagery_rows = _imagery_for(imagery, "liuren")
    if transmissions["status"] == "completed":
        values = transmissions["transmissions"]
        progression = "初传{}、中传{}、末传{}依次作为起始、过程和后续落点观察。".format(*values)
        verification = "分别核对事项当前触发点、推进过程和后续承接条件，不把三传顺序直接当成时间承诺。"
    else:
        progression = "本课进入{}，首版没有可审核的三传，因此不作过程对应。".format(transmissions["pending_path"])
        verification = "补充该课体的专家规则和标准案例后再解释过程，不使用猜测三传。"
    images = "；".join("{}：{}".format(row["symbol"], row["text"]) for row in imagery_rows)
    return {
        "module": "liuren", "title": "大六壬：环境、起因与过程链",
        "chart_fact": "{}将加临{}时；{}".format(facts["month_general"]["name"], facts["occupation_time"]["branch"], progression),
        "correspondence": "月将和天地盘用于观察占时环境，三传在规则覆盖时用于拆分过程层次。{} 类象候选：{}。".format(progression, images or "暂无"),
        "verification": verification,
        "evidence_refs": [row["candidate_id"] for row in imagery_rows],
        "rule_ids": ["INTERP-CORRESPONDENCE-001", "LR-PLATE-001", "LR-TRANSMISSION-001", "XIANG-BRANCH-001"],
    }


def explain_correspondences(module_results, context, imagery=None, yuan_hui=None):
    if not context:
        return None
    modules = []
    builders = {"zhouyi": _zhouyi, "meihua": _meihua, "liuyao": _liuyao, "liuren": _liuren}
    for module in ("zhouyi", "meihua", "liuyao", "liuren"):
        result = _find(module_results, module)
        if result:
            modules.append(builders[module](result, imagery))
    category = context["category"]
    question = context["question_summary"].strip()
    cross_layer = []
    if yuan_hui:
        facts = yuan_hui["facts"]
        cross_layer.append({
            "title": "宏观时间背景",
            "text": "公历{}年在当前工程基线中位于{}、{}（{}会、五行{}）、{}、{}，世内第{}年。该层用于标记宏观周期位置，不替代各模块盘面，也不直接决定个人事项。".format(
                facts["solar_year"], facts["yuan"]["label"], facts["hui"]["label"], facts["hui"]["branch"],
                facts["hui"]["element"], facts["yun"]["label"], facts["shi"]["label"], facts["shi"]["year_in_shi"],
            ),
            "evidence_refs": [item["evidence_id"] for item in yuan_hui["evidence"]],
            "rule_ids": ["INTERP-INTEGRATE-001", "YHYS-CYCLE-001", "YHYS-RELATION-001"],
        })
    return {
        "schema_version": "1.0", "status": "provisional_correspondence_explanation",
        "review_status": "unreviewed_deterministic_template",
        "context": {"category": category, "category_label": CATEGORY_LABELS[category], "question_summary": question},
        "headline": "把盘面对应到可核实的人、条件和过程",
        "summary": "针对“{}”，本次解释把{}个术数模块分别对应到现状结构、主体与外部条件、角色关系和过程链。对应内容来自本次盘面、事项类象和宏观时间事实，不是对现实结果的保证。".format(question, len(modules)),
        "modules": modules, "cross_layer": cross_layer,
        "verification_points": [item["verification"] for item in modules],
        "rule_ids": ["INTERP-CORRESPONDENCE-001", "INTERP-INTEGRATE-001"],
        "limitations": ["对应解释用于组织核实方向，不表示类象已经与现实对象一一确认。", "未经专家签署，不从对应关系生成吉凶、应期或成功概率。"],
    }

