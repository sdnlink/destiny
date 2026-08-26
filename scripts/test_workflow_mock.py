"""Mock驱动的工作流集成测试。

不依赖 pytz/lunar-python 等重依赖，通过 mock 排盘结果验证7步推理逻辑。
"""
import sys
import os
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.session import create_session, freeze_snapshot
from app.workflow.steps import (
    step1_info_validation,
    step2_format_plate,
    step3_identify_yongshen,
    step4_wangshuai_analysis,
    step5_xiangyi_deduction,
    step6_synthesis_judgement,
    step7_advice_and_disclaimer,
)


def make_mock_session():
    """创建一个带 mock 排盘数据的会话。"""
    session = create_session(
        question="近期事业发展如何？",
        category="career",
        system="auto",
        casting_method="time",
    )
    session.casting_source = {
        "local_datetime": "2026-08-26T10:00:00",
        "timezone": "Asia/Shanghai",
        "cast_nonce": "test1234567890",
    }
    return session


def make_mock_module_results():
    """构造 mock 的各模块排盘结果。"""
    return [
        {
            "module": "calendar",
            "status": "completed",
            "result": {
                "facts": {
                    "ganzhi": {"year": "丙午", "month": "丙申", "day": "庚子", "hour": "辛巳"},
                    "lunar": {"year": 2026, "month": 7, "day": 14},
                    "solar_term": "处暑",
                }
            },
        },
        {
            "module": "meihua",
            "status": "completed",
            "result": {
                "facts": {
                    "original": {"name": "风火家人", "upper": "巽", "lower": "离"},
                    "mutual": {"name": "火水未济"},
                    "changed": {"name": "风雷益"},
                    "moving_line": 3,
                    "ti_yong": {"ti": "离", "yong": "巽", "relation": "用生体"},
                }
            },
        },
        {
            "module": "liuyao",
            "status": "completed",
            "result": {
                "facts": {
                    "original_hexagram": "风火家人",
                    "changed_hexagram": "风雷益",
                    "moving_lines": [3],
                    "six_spirits": ["青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武"],
                    "liuqin": ["子孙", "妻财", "官鬼", "父母", "兄弟", "世"],
                    "wangshuai": {"官鬼": "旺", "妻财": "相", "子孙": "休"},
                }
            },
        },
    ]


def test_step1():
    """步骤1：信息校验。"""
    session = make_mock_session()
    result = step1_info_validation(session)
    assert result["step"] == 1
    assert result["ready"] is True
    assert result["missing_fields"] == []
    assert result["category_label"] == "事业"
    print("  step1 OK: ready=True, category=事业")


def test_step1_missing():
    """步骤1：信息缺失检测。"""
    session = create_session(question="", category="career")
    session.casting_source = {}
    session.casting_method = "numbers"
    result = step1_info_validation(session)
    assert result["ready"] is False
    assert "求测事由" in result["missing_fields"]
    assert "报数" in result["missing_fields"]
    print("  step1 missing OK: detected 求测事由+报数缺失")


def test_step2():
    """步骤2：排盘格式化。"""
    results = make_mock_module_results()
    plate = step2_format_plate(results, ["meihua", "liuyao"])
    assert plate["step"] == 2
    assert "meihua" in plate["plates"]
    assert "liuyao" in plate["plates"]
    assert "calendar" in plate
    print("  step2 OK: plates contain meihua+liuyao+calendar")


def test_step3():
    """步骤3：用神定位。"""
    session = make_mock_session()
    results = make_mock_module_results()
    plate = step2_format_plate(results, ["meihua", "liuyao"])
    yongshen = step3_identify_yongshen(session, plate)
    assert yongshen["step"] == 3
    assert "primary_yongshen" in yongshen
    assert "logic" in yongshen
    print(f"  step3 OK: primary_yongshen={yongshen['primary_yongshen']}")


def test_step4():
    """步骤4：旺衰分析。"""
    session = make_mock_session()
    results = make_mock_module_results()
    plate = step2_format_plate(results, ["meihua", "liuyao"])
    yongshen = step3_identify_yongshen(session, plate)
    wangshuai = step4_wangshuai_analysis(session, plate, yongshen)
    assert wangshuai["step"] == 4
    assert "yongshen_wangshuai" in wangshuai
    assert "tiyong_relation" in wangshuai
    print(f"  step4 OK: wangshuai={wangshuai['yongshen_wangshuai']}")


def test_step5():
    """步骤5：象义拆解。"""
    session = make_mock_session()
    results = make_mock_module_results()
    plate = step2_format_plate(results, ["meihua", "liuyao"])
    yongshen = step3_identify_yongshen(session, plate)
    # mock get_hexagram_explanation
    with patch("app.workflow.steps.get_hexagram_explanation", return_value={"summary": "家人卦象征家庭和睦、事业有序"}):
        xiangyi = step5_xiangyi_deduction(session, plate, yongshen)
    assert xiangyi["step"] == 5
    assert len(xiangyi["symbol_mappings"]) > 0
    print(f"  step5 OK: {len(xiangyi['symbol_mappings'])} symbol mappings")


def test_step6():
    """步骤6：综合吉凶定性。"""
    session = make_mock_session()
    results = make_mock_module_results()
    plate = step2_format_plate(results, ["meihua", "liuyao"])
    yongshen = step3_identify_yongshen(session, plate)
    wangshuai = step4_wangshuai_analysis(session, plate, yongshen)
    with patch("app.workflow.steps.get_hexagram_explanation", return_value={"summary": "家人卦"}):
        xiangyi = step5_xiangyi_deduction(session, plate, yongshen)
    # mock 重依赖调用
    with patch("app.workflow.steps.synthesize", return_value={"summary": "综合研判结果"}), \
         patch("app.workflow.steps.generate_advisory", return_value=["建议1", "建议2"]), \
         patch("app.workflow.steps.collect_imagery", return_value=[]), \
         patch("app.workflow.steps.collect_literature_opinions", return_value=[]), \
         patch("app.workflow.steps.analyze_yuan_hui_yun_shi", return_value={}):
        synthesis = step6_synthesis_judgement(session, results, plate, yongshen, wangshuai, xiangyi)
    assert synthesis["step"] == 6
    assert "fortune_level" in synthesis
    assert synthesis["fortune_level"] in ("大吉", "小吉", "平", "小凶", "大凶")
    assert "fortune_basis" in synthesis
    print(f"  step6 OK: fortune_level={synthesis['fortune_level']}")


def test_step7():
    """步骤7：行动建议。"""
    session = make_mock_session()
    advice = step7_advice_and_disclaimer(session, {"fortune_level": "小吉"})
    assert advice["step"] == 7
    assert "advice" in advice
    assert "disclaimer" in advice
    assert "传统易经术数文化" in advice["disclaimer"]
    print(f"  step7 OK: {len(advice['advice'])} advice + disclaimer")


def test_full_workflow_chain():
    """完整7步链式执行（mock驱动）。"""
    print("\n=== 完整7步工作流链式测试 ===")
    session = make_mock_session()
    results = make_mock_module_results()

    s1 = step1_info_validation(session)
    assert s1["ready"]

    s2 = step2_format_plate(results, ["meihua", "liuyao"])
    s3 = step3_identify_yongshen(session, s2)
    s4 = step4_wangshuai_analysis(session, s2, s3)

    with patch("app.workflow.steps.get_hexagram_explanation", return_value={"summary": "家人卦，事业有序"}):
        s5 = step5_xiangyi_deduction(session, s2, s3)

    with patch("app.workflow.steps.synthesize", return_value={"summary": "mock"}), \
         patch("app.workflow.steps.generate_advisory", return_value=["建议1"]), \
         patch("app.workflow.steps.collect_imagery", return_value=[]), \
         patch("app.workflow.steps.collect_literature_opinions", return_value=[]), \
         patch("app.workflow.steps.analyze_yuan_hui_yun_shi", return_value={}):
        s6 = step6_synthesis_judgement(session, results, s2, s3, s4, s5)

    s7 = step7_advice_and_disclaimer(session, s6)

    # 验证数据单向流动
    assert s1["step"] == 1
    assert s2["step"] == 2
    assert s3["step"] == 3
    assert s4["step"] == 4
    assert s5["step"] == 5
    assert s6["step"] == 6
    assert s7["step"] == 7

    # 验证冻结快照
    raw_plate = {"step_results": {f"step{i}": eval(f"s{i}") for i in range(1, 8)}}
    session = freeze_snapshot(session, raw_plate, results, {"q": "test"})
    assert session.snapshot.frozen is True

    print("  全部7步链式执行通过，快照冻结成功")
    print(f"  最终吉凶定性：{s6['fortune_level']}")


if __name__ == "__main__":
    print("=== Mock驱动工作流集成测试 ===\n")
    test_step1()
    test_step1_missing()
    test_step2()
    test_step3()
    test_step4()
    test_step5()
    test_step6()
    test_step7()
    test_full_workflow_chain()
    print("\n=== 全部测试通过 ===")
