"""7步排盘推理工作流引擎。

强制完整执行7步流程，禁止跳过逻辑直接输出结论。
每一步的输出都记录在会话中，步骤间数据单向流动。
"""

from typing import Any, Dict, Tuple

from app.session import (
    DivinationSession,
    freeze_snapshot,
    get_store,
)

from .casting import execute_calculations
from .format import render_fixed_format
from .plate_facts import build_plate_facts, compact_plate_output
from .scheduler import build_calculation_requests, select_systems
from .steps import (
    step1_info_validation,
    step2_format_plate,
    step3_identify_yongshen,
    step4_wangshuai_analysis,
    step5_xiangyi_deduction,
    step6_synthesis_judgement,
    step7_advice_and_disclaimer,
)


class WorkflowEngine:
    """7步工作流引擎。"""

    def __init__(self, session: DivinationSession):
        self.session = session
        self.store = get_store()

    def run(self) -> Tuple[DivinationSession, Dict[str, Any]]:
        """执行完整7步工作流。

        Returns:
            (session, workflow_result)

        Raises:
            ValueError: 信息不足无法排盘时，返回信息补全提示
        """
        # 步骤1：信息校验
        step1 = step1_info_validation(self.session)
        if not step1["ready"]:
            raise ValueError(
                "起盘信息不足，缺失：" + "、".join(step1["missing_fields"])
            )

        # 术数调度
        systems, scheduling_note = select_systems(self.session.system)

        # 构建并执行计算
        requests = build_calculation_requests(
            systems, self.session.casting_method, self.session.casting_source
        )
        module_results = execute_calculations(requests)

        # 冻结快照（铁律：盘面一经生成永久固定）
        # plate_facts 把各体系 facts 归一后一起冻结，交互层才有卦名、动爻、体用卦可读
        raw_plate = {
            "scheduling_note": scheduling_note,
            "systems_used": systems,
            "calculation_requests": requests,
            "plate_facts": build_plate_facts(module_results),
        }
        input_payload = {
            "question": self.session.question,
            "casting_method": self.session.casting_method,
            "casting_source": self.session.casting_source,
            "systems": systems,
        }
        self.session = freeze_snapshot(
            self.session,
            raw_plate=raw_plate,
            module_results=module_results,
            input_payload=input_payload,
            rule_version="workflow-engine-1.0.0",
            systems_used=systems,
        )

        # 步骤2：完整排盘输出
        step2 = step2_format_plate(module_results, systems)

        # 步骤3：定用神
        step3 = step3_identify_yongshen(self.session, step2)

        # 步骤4：旺衰状态计算
        step4 = step4_wangshuai_analysis(self.session, step2, step3)

        # 步骤5：象义拆解推理
        step5 = step5_xiangyi_deduction(self.session, step2, step3)

        # 步骤6：综合吉凶定性 & 事态推演
        step6 = step6_synthesis_judgement(
            self.session, module_results, step2, step3, step4, step5
        )

        # 步骤7：行动建议与免责提示
        step7 = step7_advice_and_disclaimer(self.session, step6)

        # 拓展参考资料库（模块C）
        reference_library = self._build_reference_library(step2, step5, step6)

        # 卦象现状核对（模块B）
        reality_check = self._build_reality_check(step2, step3, step6)

        # 后续交互入口（模块D）
        followup_menu = self._build_followup_menu()

        # 渲染固定格式
        formatted = render_fixed_format(
            self.session, step1, step2, step3, step4, step5, step6, step7,
            reference_library, reality_check, followup_menu,
        )

        # 保存工作流结果到会话
        # step2 只存展示字段：完整盘面已在快照 module_results 里，重复存一份会让
        # 每个会话文件翻倍（实测单个会话 ~270KB 中 step2 占 ~36KB 且与快照同源）。
        self.session.workflow_result = {
            "step1": step1,
            "step2": compact_plate_output(step2),
            "step3": step3,
            "step4": step4,
            "step5": step5,
            "step6": step6,
            "step7": step7,
            "reference_library": reference_library,
            "reality_check": reality_check,
            "followup_menu": followup_menu,
            "formatted_text": formatted["text"],
            "scheduling_note": scheduling_note,
        }
        self.store.save(self.session)

        return self.session, self.session.workflow_result

    def _build_reference_library(self, step2, step5, step6) -> Dict[str, Any]:
        """构建拓展参考资料库（模块C）。"""
        hex_name = step5.get("hexagram_name", "")
        fortune = step6.get("fortune_level", "平")

        # 核心符号原始象义
        core_symbols = []
        for m in step5.get("symbol_mappings", []):
            core_symbols.append(f"{m['symbol']}：{m['original_meaning']}")
        core_symbols_text = "；".join(core_symbols) if core_symbols else f"本卦「{hex_name}」核心象义需结合卦辞爻辞进一步拆解"

        # 风险隐患
        risks = []
        for o in step6.get("obstacles", []):
            risks.append(o)
        if fortune in ("小凶", "大凶"):
            risks.append("卦象整体偏凶，重大决策宜暂缓，优先排查风险")
        risks_text = "；".join(risks) if risks else "当前无显著风险隐患，但仍需关注细节变化"

        # 时间窗口
        if fortune in ("大吉", "小吉"):
            time_window = "适合行动：用神旺相时段可积极推进；适合观望：节气交接前后；尽量规避：用神休囚死之日"
        elif fortune == "平":
            time_window = "适合行动：小范围验证阶段；适合观望：大局未定之时；尽量规避：冲动冒进、孤注一掷"
        else:
            time_window = "适合行动：待用神得令、外部条件转好后；适合观望：当前阶段宜守不宜攻；尽量规避：重大投入、不可逆决策"

        # 多发展可能性
        possibilities = (
            "①顺势发展：若用神得令生扶，事项按有利方向推进，触发条件为关键人支持/资源到位；"
            "②阻滞反复：若用神受克休囚，事项出现拖延或反复，触发条件为外部阻力/关键人变动；"
            "③意外转变：若动爻逢冲逢值，事项出现意料之外的变化，触发条件为突发因素/时间节点到达。"
        )

        # 误读误区
        misreadings = (
            "①忌仅凭卦名吉凶断事，需结合用神旺衰、体用生克、动爻变化综合判断；"
            "②忌将研究性结论当作确定性预言，卦象反映的是趋势与概率，非绝对结果；"
            "③忌忽略起盘时间与用神的对应关系，同一卦在不同月令日辰下旺衰不同。"
        )

        return {
            "core_symbols": core_symbols_text,
            "risks": risks_text,
            "time_window": time_window,
            "possibilities": possibilities,
            "misreadings": misreadings,
        }

    def _build_reality_check(self, step2, step3, step6) -> Dict[str, Any]:
        """构建卦象现状核对条目（模块B）。"""
        items = []

        # 从卦象提取现状描述
        plates = step2.get("plates", {})
        for module, plate in plates.items():
            label = plate.get("system_label", module)
            facts = plate.get("facts", {})
            original = facts.get("original") or facts.get("original_hexagram")
            if original and isinstance(original, dict):
                items.append(f"{label}本卦为「{original.get('name', '')}」，提示当前事项处于{original.get('name', '')}所象之状态")
            moving = facts.get("moving_line")
            if moving:
                items.append(f"动爻在第{moving}爻，提示事项的关键变化点与该爻所象之事相关")

        # 用神状态
        ys = step3.get("primary_yongshen", "")
        items.append(f"用神为{ys}，其旺衰状态反映了事项核心要素的当前力量对比")

        # 吉凶趋势
        fortune = step6.get("fortune_level", "平")
        items.append(f"综合定性为「{fortune}」，整体趋势{ '偏有利' if fortune in ('大吉','小吉') else '偏阻滞' if fortune in ('小凶','大凶') else '吉凶参半' }")

        return {"items": items[:3]}

    def _build_followup_menu(self) -> Dict[str, Any]:
        """构建后续交互入口（模块D）。"""
        options = [
            "①核对上面的卦局现状描述，告诉我是否符合你的现实；",
            "②针对盘局某一个符号、某一句断语进行深度追问；",
            "③换角度解读：备选方案、多方人物心态分析；",
            "④更换术数门派，对此事重新起盘参断；",
            "⑤代入不同选择，推演不同选择之下事态变化；",
            "⑥留存本卦，后续反馈现实结果进行复盘对照。",
        ]
        return {"options": options}


def run_workflow(session: DivinationSession) -> Tuple[DivinationSession, Dict[str, Any]]:
    """便捷函数：执行工作流。"""
    engine = WorkflowEngine(session)
    return engine.run()
