"""Advisory generation integrating hexagram wisdom, multi-system deduction, and domain-specific questions."""

from typing import Any, Dict, List, Optional
from app.core.hexagram_service import get_hexagram_explanation

CATEGORY_PROFILES = {
    "career": {
        "label": "事业",
        "objective": "明晰事业发展阶段、核心决策权限与关键推进节点",
        "dimension_focus": "关注责权分配、晋升通道、平台稳定性与关键人支持",
        "recommendations": [
            ("理清核心权责与验收指标", "明确下一阶段主攻目标与衡量标准，将口头支持落实为明确的资源、团队或预算。"),
            ("小步验证并建立关键人协同", "对重大变动先做小范围试点验证，加强与核心决策者和跨部门协作方的定期对齐。"),
            ("留足转换缓冲与底线预案", "在作出不可逆选择前评估最坏承受力，确保个人专业能力与风险备选方案完备。"),
        ],
        "questions": ["谁对该事项拥有最终决策权？", "当前阶段最关键的业务或人脉瓶颈在哪里？", "若推进不如预期，可承受的最大试错成本与退出机制是什么？"],
    },
    "finance": {
        "label": "财务",
        "objective": "把控现金流安全、收益预期合理性与最大亏损底线",
        "dimension_focus": "关注资产流动性、合同细则、风险敞口与止损机制",
        "recommendations": [
            ("量化收支与现金流压力测试", "分别测算乐观、中性与最差情景下的现金流，避免以单一乐观预期作为决策支撑。"),
            ("预设硬性止损与退出阈值", "在投入前严格设定最大亏损线与撤退触发条件，触及红线时坚决执行预案。"),
            ("严核合同凭证与法律权属", "重点核对资金划转路径、合作协议权责及流动性锁定周期，防范隐性债务与合伙纷争。"),
        ],
        "questions": ["最坏情景下最大可能损失是多少，是否会影响基本盘？", "资金锁定期与变现通道是否顺畅？", "收益逻辑是否基于真实市场需求而非情绪跟风？"],
    },
    "relationship": {
        "label": "关系",
        "objective": "理清事实与诉求、建立健康边界与良性互动共识",
        "dimension_focus": "关注双方真实意图、信任基础、沟通方式与边界共识",
        "recommendations": [
            ("区分客观事实与主观猜想", "记录具体行为与事实，减少因情绪推测导致的误解与立场对立。"),
            ("以建设性坦诚进行深度对齐", "选择合适时机就彼此的核心诉求、未来规划进行直接而不带指责的真诚沟通。"),
            ("建立可持续的相处边界与默契", "确立双方认可的边界与互动节奏，以长期的行为一致性作为信任基础。"),
        ],
        "questions": ["双方已达成明确共识的核心部分是什么？", "矛盾的核心究竟是认知差异、沟通模式还是利益诉求冲突？", "各自愿意为维护关系做出的切实调整是什么？"],
    },
    "travel": {
        "label": "出行",
        "objective": "确保行程周密、风险可控与应急预案完备",
        "dimension_focus": "关注交通时效、人身财产安全、气候环境与突发应对",
        "recommendations": [
            ("核验行程证件与关键节点衔接", "提前核实交通班次、住宿、证件有效期及目的地特殊政策，预留充足换乘时间。"),
            ("准备备选路线与应急离线资料", "将紧急联络人、行程凭证、保单等离线备份，遇单点延误时快速切换备用路线。"),
            ("顺应天时地利，安全为先", "关注沿途气象与路况，不盲目涉险或赶路，遇突发状况依规处置。"),
        ],
        "questions": ["哪个换乘或行程环节最容易引发连锁延误？", "若遇突发延误或取消，备选应对方案是什么？", "紧急医疗与救援保障是否到位？"],
    },
    "study": {
        "label": "学业",
        "objective": "夯实知识体系、突破思维瓶颈与提升应试/应用能力",
        "dimension_focus": "关注学习方法、基础功底、复盘节奏与考运心态",
        "recommendations": [
            ("拆解知识模块并定额定量攻坚", "将庞杂科目拆解为每周具体输出指标，以高频练习与复述巩固代替被动阅读。"),
            ("精准定位薄弱环节重点突破", "梳理错题与卡点知识盲区，实施靶向强化训练，避免在已熟练领域耗费过多精力。"),
            ("保持规律模拟与心智调适", "定期进行全真模拟测试，在实战节奏中优化答题策略，保持从容自信的考场心态。"),
        ],
        "questions": ["当前制约成绩突破的核心薄弱点在哪里？", "每周能保证的高专注深度学习时长是多少？", "距离目标考核标准的差距如何量化？"],
    },
    "other": {
        "label": "其他",
        "objective": "明确问题核心、梳理主客观条件与制定可逆执行路径",
        "dimension_focus": "关注内外因匹配、关键变量控制与复盘调整机制",
        "recommendations": [
            ("定义核心诉求与根本矛盾", "剖析事物表象背后的核心驱动力，明确真正需要解决的关键问题。"),
            ("分清可控、可影响与不可控要素", "将有限资源集中投入在自身能够掌控和产生直接反馈的环节。"),
            ("采取小步快跑、定期复盘策略", "以最小成本行动试探反馈，根据实际结果动态校准下一步方案。"),
        ],
        "questions": ["该事项取得成功的最核心驱动要素是什么？", "当前最大的未知变量是什么？", "第一步最具可行性的切入点在哪里？"],
    },
}

RELATION_GUIDANCE = {
    "same_element": {
        "focus": "体用比和：同舟共济，内和外顺，宜强化共识同频",
        "rationale": "梅花易数本卦体用同属一行（比和），象征主体与外部环境能量和谐、气机相通。利于寻求共赢合作、凝聚团队力量，只要目标一致便能顺水推舟。",
        "action": ("凝聚各方共识，建立同向合力", "确认相关协作方对目标、交付标准与推进节奏理解一致，避免因细小职责模糊产生摩擦。"),
    },
    "use_generates_body": {
        "focus": "用生体：得道多助，良机临门，宜主动借势承接",
        "rationale": "梅花易数本卦呈现用生体之象，外部环境、贵人长者或外部资源对主体产生生旺与滋养作用。代表外部条件有利，常有意外支持或顺境助力。",
        "action": ("敏锐捕捉外部利好，将善意转化为确切成果", "主动对接潜在支持者与外部资源，将口头支持固化为实际的合作协议、资源倾斜或专业指导。"),
    },
    "body_generates_use": {
        "focus": "体生用：付出消耗，循序蓄养，宜节制过度透支",
        "rationale": "梅花易数本卦呈现体生用之象，象征主体对外部环境持续输出、精力资金持续投入。若无节制消耗容易导致自身虚耗，需防范过度付出而未见正向回馈。",
        "action": ("设立阶段投入预算，防范单向消耗", "为各项精力、资金投入设置明确的验收节点与上限，若连续投入未见有效反馈，应及时停步复盘调整。"),
    },
    "use_controls_body": {
        "focus": "用克体：外力制约，逆境考验，宜守正防守避锋芒",
        "rationale": "梅花易数本卦呈现用克体之象，象征外部规则、客观环境或竞争对手给主体施加较大压力与阻力。此时不可盲目硬顶硬碰，应低调防守、遵纪守法、化解矛盾。",
        "action": ("正视客观规则与外部约束，以柔克刚稳扎稳打", "梳理所有不可抗拒的外部硬性限制，准备充分的合规预案与防御措施，避开正面冲突。"),
    },
    "body_controls_use": {
        "focus": "体克用：主导进取，克服阻碍，宜果断掌控留余地",
        "rationale": "梅花易数本卦呈现体克用之象，象征主体具备克服困难、主导局面与驾驭外部资源的能力。只要自身实力过硬、方法得当，便可破局制胜，但需注意防范骄兵必败。",
        "action": ("发挥自身核心优势，果敢推进行动落实", "充分调动自身已有资源与掌控力，快速突破关键卡点；同时关照各方利益，留有余地以得人心。"),
    },
}


def _find_module(module_results, name):
    for item in module_results:
        if item.get("module") == name:
            return item.get("result")
    return None


def generate_advisory(module_results: List[Dict[str, Any]], context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not context:
        return None
    category = context.get("category", "other")
    if category not in CATEGORY_PROFILES:
        raise ValueError(f"unsupported advisory category: {category}")
    question = context.get("question_summary", "").strip()
    profile = CATEGORY_PROFILES[category]

    zhouyi = _find_module(module_results, "zhouyi")
    meihua = _find_module(module_results, "meihua")
    liuyao = _find_module(module_results, "liuyao")
    liuren = _find_module(module_results, "liuren")
    ziwei = _find_module(module_results, "ziwei")

    evidence_basis = []
    
    # 1. 周易卦意提取
    zy_facts = (zhouyi or {}).get("facts", {})
    orig_hex_name = zy_facts.get("original", {}).get("name")
    chg_hex_name = zy_facts.get("changed", {}).get("name")
    moving_lines = zy_facts.get("moving_lines", [])

    orig_exp = get_hexagram_explanation(orig_hex_name) if orig_hex_name else None
    chg_exp = get_hexagram_explanation(chg_hex_name) if chg_hex_name else None

    # 2. 梅花体用指导
    mh_guidance = None
    if meihua and meihua.get("evidence"):
        original_evidence = next(
            (item for item in meihua["evidence"] if item.get("stage") == "original"),
            meihua["evidence"][0],
        )
        mh_guidance = RELATION_GUIDANCE.get(original_evidence["code"])
        evidence_basis.append({
            "module": "meihua",
            "fact": f"体用关系：{original_evidence['label']}",
            "rule_ids": original_evidence.get("rule_ids", []),
        })

    # 3. 综合现状剖析 (Status Quo)
    status_quo_points = []
    if orig_exp:
        cat_key = f"{category}_interpretation"
        hex_cat_insight = orig_exp.get(cat_key) or orig_exp.get("summary", "")
        status_quo_points.append(f"【本卦卦象】所处基准卦为《{orig_exp['full_name']}》，其卦德为“{orig_exp['nature']}”。大象传曰：“{orig_exp['great_image']}”。在{profile['label']}层面，{hex_cat_insight}")
    if meihua:
        mh_facts = meihua.get("facts", {})
        bu = mh_facts.get("body_use", {})
        status_quo_points.append(f"【体用定位】以【{bu.get('body_trigram', {}).get('name')}】（属{bu.get('body_trigram', {}).get('element')}）为主体，【{bu.get('use_trigram', {}).get('name')}】（属{bu.get('use_trigram', {}).get('element')}）为外部事态。{mh_guidance['rationale'] if mh_guidance else ''}")
    if liuyao:
        ly_facts = liuyao.get("facts", {})
        palace = ly_facts.get("palace", {})
        status_quo_points.append(f"【六爻世应】归于{palace.get('name')}宫（{palace.get('stage')}），世爻居第{palace.get('host_line')}爻代表自身根基，应爻居第{palace.get('response_line')}爻代表对方与目标环境，日旬空在【{'、'.join(ly_facts.get('xun', {}).get('empty_branches', []))}】。")
    if ziwei:
        zw_facts = ziwei.get("facts", {})
        ming_p = next((p for p in zw_facts.get("palaces_by_order", []) if p.get("name") == "命宫"), None)
        main_s = "、".join(s["name"] for s in (ming_p.get("main_stars", []) if ming_p else [])) or "无主星"
        status_quo_points.append(f"【紫微命局】五行局定为{zw_facts.get('bureau', {}).get('name')}，命宫坐落于{zw_facts.get('ming_palace', {}).get('palace_stem_branch')}，主星为【{main_s}】，命主{zw_facts.get('ming_zhu')}，整体格局重在修养心性与发挥主星特质。")

    # 4. 演变趋势与转折 (Trend Evolution)
    trend_points = []
    if moving_lines:
        m_str = "、".join(f"第{v}爻" for v in moving_lines)
        if chg_exp:
            trend_points.append(f"【动变趋向】由《{orig_hex_name}》卦中{m_str}发动，转化发展为《{chg_exp['full_name']}》卦（{chg_exp['nature']}）。提示事物由初始阶段向变卦形态演化，变化关口集中在{m_str}，宜重点关注此关键转折点。")
        else:
            trend_points.append(f"【动爻指示】卦中{m_str}发动，提示局势存在动态演化空间，应在变动位置多做针对性准备。")
    else:
        trend_points.append(f"【静态持守】当前周易推演六爻均安（无动爻），提示短期内外部基本架构保持稳定，事物处于持续积累和常态运行期，不宜凭空预设剧烈突变。")
    if liuren:
        lr_trans = liuren.get("facts", {}).get("three_transmissions", {})
        if lr_trans.get("status") == "completed":
            trend_points.append(f"【六壬三传】课体为“{lr_trans.get('lesson_type')}”，三传以初传【{lr_trans.get('transmissions', [])[0]}】为起因发端，中传【{lr_trans.get('transmissions', [])[1]}】为移易过程，末传【{lr_trans.get('transmissions', [])[2]}】为最终归结，层层推进。")

    # 5. 潜在盲区与风险 (Risk & Pitfalls)
    risk_points = []
    if orig_exp:
        risk_points.append(f"【卦象反思】处于《{orig_exp['full_name']}》之时，最忌{orig_exp.get('general_advice', '')}。须谨防因表面顺利而忽视隐性制度、财务或人际漏洞。")
    if ziwei:
        zw_facts = ziwei.get("facts", {})
        sihua = zw_facts.get("si_hua", {})
        if "化忌" in sihua:
            risk_points.append(f"【四化化忌】出生生年干触发【{sihua['化忌']}化忌】，提示在涉及该星曜掌管的领域（情绪执念、文书合约或利益沟通）容易产生卡点与考验，需特别谨慎防范。")
    if liuyao:
        ly_facts = liuyao.get("facts", {})
        moving_lines_ly = [l for l in ly_facts.get("line_chart", []) if l.get("is_moving")]
        for l in moving_lines_ly:
            if l.get("six_relative") == "官鬼":
                risk_points.append("【官鬼动爻】盘中官鬼爻发动，提示涉及规章制度、监管压力、竞争对手或职场风波时须高度谨慎，守法守规方能化险为夷。")
            elif l.get("six_relative") == "兄弟":
                risk_points.append("【兄弟动爻】盘中兄弟爻发动，提示需防范同行竞争、同伴分歧或利益分流，合作协议应白纸黑字写明利益分配。")

    # 6. 综合研判结论 (Strategic Conclusion)
    headline = mh_guidance["focus"] if mh_guidance else (orig_exp["nature"] if orig_exp else profile["objective"])
    summary_text = (
        f"针对用户所问事项“{question}”（{profile['label']}领域），"
        f"综合卦盘推演，当前核心定调为：【{headline}】。"
        f"{orig_exp['summary'] if orig_exp else ''} "
        f"{mh_guidance['rationale'] if mh_guidance else ''} "
        f"{profile['objective']}。"
    )

    # 7. 针对性落地建议 (Recommendations)
    recommendations = []
    if mh_guidance:
        recommendations.append({
            "priority": 1,
            "title": f"【象法策略】{mh_guidance['action'][0]}",
            "detail": mh_guidance["action"][1],
            "basis": mh_guidance["rationale"],
            "phase": "第一阶段：立足当下",
            "rule_ids": ["ADV-MH-RELATION-001", "MH-FIVE-ELEMENT-001"],
        })
    if orig_exp:
        recommendations.append({
            "priority": len(recommendations) + 1,
            "title": f"【卦德践行】{orig_exp['general_advice']}",
            "detail": orig_exp.get(f"{category}_interpretation") or orig_exp.get("summary", ""),
            "basis": f"周易《{orig_exp['full_name']}》大象传与卦德指导",
            "phase": "第二阶段：谋势推进",
            "rule_ids": ["ADV-CONTEXT-001", "YI-RELATION-001"],
        })
    for index, (title, detail) in enumerate(profile["recommendations"], len(recommendations) + 1):
        recommendations.append({
            "priority": index,
            "title": f"【专业务实】{title}",
            "detail": detail,
            "basis": f"{profile['label']}事项决策原则与风险控制规范",
            "phase": "第三阶段：落地防守",
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
            "headline": headline,
            "text": summary_text,
            "polarity": "indeterminate",
            "confidence_label": "理象融合研判",
        },
        "domain_analysis": {
            "status_quo": status_quo_points,
            "trend_evolution": trend_points,
            "risk_and_pitfalls": risk_points,
        },
        "recommendations": recommendations,
        "verification_questions": list(profile["questions"]),
        "evidence_basis": evidence_basis,
        "risk_notes": [
            "建议来自未审核的工程模板，只能作为问题整理和决策检查清单。",
            "涉及医疗、法律、投资、安全等高影响事项时，应以具备资质的专业意见和可核验数据为准。",
            "不要仅依据本推演作出不可逆、超出承受范围或影响他人权益的决定。",
            "卦由心生，事在人为；知进退、明得失、顺天应人方为上上之选。",
        ],
        "rule_ids": ["ADV-CONTEXT-001"] + (["ADV-MH-RELATION-001"] if mh_guidance else []),
    }
