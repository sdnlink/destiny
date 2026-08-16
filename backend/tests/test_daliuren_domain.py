from dataclasses import FrozenInstanceError
import sys
from pathlib import Path

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.daliuren import auto_cast, number_cast, time_cast
from app.daliuren.models import OccupationNumberInput, PlateInput
from app.daliuren.rules import MONTH_GENERALS, TRANSMISSION_COVERAGE


TZ = "Asia/Shanghai"


def test_domain_models_are_immutable_and_strict():
    request = OccupationNumberInput(4)
    with pytest.raises(FrozenInstanceError):
        request.value = 5
    for invalid in (True, 4.0, "4"):
        with pytest.raises(ValueError):
            OccupationNumberInput(invalid)


def test_plate_requires_a_complete_branch_permutation():
    branches = tuple("子丑寅卯辰巳午未申酉戌亥")
    assert PlateInput(branches).heaven_branches == branches
    with pytest.raises(ValueError):
        PlateInput(branches[:-1] + ("子",))


def test_rule_configuration_is_read_only_and_lists_every_required_path():
    with pytest.raises(TypeError):
        MONTH_GENERALS["雨水"] = ("子", "错误")
    paths = {item["path"]: item["status"] for item in TRANSMISSION_COVERAGE}
    assert set(paths) == {"贼克", "克", "比用", "涉害", "遥克", "昴星", "别责", "八专", "伏吟", "返吟"}
    assert paths["遥克"] == "implemented_engineering_baseline"
    assert paths["涉害"] == "pending_rule_selection"


def test_existing_direct_control_case_remains_replayable():
    result = time_cast("2026-08-15T16:00:00", TZ)
    facts = result["facts"]
    assert facts["three_transmissions"]["lesson_type"] == "克"
    assert facts["three_transmissions"]["transmissions"] == ["午", "辰", "寅"]
    assert len(facts["four_lessons"]) == 4
    assert len(facts["heaven_plate"]) == 12
    assert len(facts["heavenly_generals"]["by_ground"]) == 12


def test_remote_control_uses_remote_branch_then_plate_progression():
    result = number_cast(4, "2026-01-01T12:00:00", TZ)
    transmissions = result["facts"]["three_transmissions"]
    assert transmissions["status"] == "completed"
    assert transmissions["lesson_type"] == "遥克"
    assert transmissions["source_path"] == "蒿矢"
    assert transmissions["transmissions"] == ["酉", "未", "巳"]


def test_star_method_uses_yin_day_downward_rule():
    result = number_cast(5, "2026-01-03T12:00:00", TZ)
    transmissions = result["facts"]["three_transmissions"]
    assert transmissions["status"] == "completed"
    assert transmissions["lesson_type"] == "昴星"
    assert transmissions["source_path"] == "阴日俯视"
    assert transmissions["transmissions"] == ["子", "辰", "戌"]


@pytest.mark.parametrize(
    "expected_path,local_datetime,number",
    (
        ("涉害", "2026-01-01T12:00:00", 6),
        ("别责", "2026-01-23T12:00:00", 3),
        ("八专", "2026-02-02T12:00:00", 2),
        ("伏吟", "2026-01-02T12:00:00", 2),
        ("返吟", "2026-01-03T12:00:00", 8),
    ),
)
def test_unsigned_special_paths_are_identified_without_fabricated_transmissions(expected_path, local_datetime, number):
    transmissions = number_cast(number, local_datetime, TZ)["facts"]["three_transmissions"]
    assert transmissions["status"] == "pending_rule_selection"
    assert transmissions["pending_path"] == expected_path
    assert transmissions["transmissions"] == []
    assert transmissions["reason"]


def test_result_contains_versions_normalized_input_trace_and_rule_steps():
    result = number_cast(4, "2026-01-01T12:00:00", TZ)
    assert result["algorithm_version"] == "daliuren-engine-2.0.0+lunar-python-1.4.8"
    assert result["normalized_input"]["occupation_branch"] == "卯"
    assert len(result["calculation_trace"]) >= 8
    assert [step["sequence"] for step in result["steps"]] == [1, 2, 3, 4]
    assert result["steps"][2]["rule_ids"] == ["LR-REMOTE-001"]
    assert result["judgements"] == []


def test_personalized_report_number_is_replayable_and_private():
    nonce = "person-0000000000000001"
    first = auto_cast(nonce, "2026-08-15T16:00:00", TZ)
    second = auto_cast(nonce, "2026-08-15T16:00:00", TZ)
    assert first == second
    assert nonce not in str(first)
