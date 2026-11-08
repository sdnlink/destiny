"""Data models for BaZi (子平八字) calculations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BaZiInput(BaseModel):
    local_datetime: str = Field(..., json_schema_extra={"example": "2026-08-15T16:00:00"})
    timezone: str = Field("Asia/Shanghai", json_schema_extra={"example": "Asia/Shanghai"})
    gender: str = Field("男", json_schema_extra={"example": "男"})
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    use_true_solar_time: bool = False


class HiddenStemDetail(BaseModel):
    stem: str
    element: str
    ten_god: str
    weight: float
    type: str  # 本气 / 中气 / 余气


class PillarDetail(BaseModel):
    name: str  # 年柱 / 月柱 / 日柱 / 时柱
    stem: str
    branch: str
    ganzhi: str
    stem_element: str
    branch_element: str
    stem_ten_god: str
    hidden_stems: List[HiddenStemDetail]
    nayin: str
    twelve_stage: str
    shensha: List[str]


class ElementDistribution(BaseModel):
    element: str
    score: float
    percentage: float


class DayMasterStrength(BaseModel):
    day_master: str
    element: str
    score: float
    level: str  # 极弱 / 偏弱 / 中和 / 偏旺 / 极旺
    favorable_elements: List[str]  # 喜用五行
    unfavorable_elements: List[str]  # 忌神五行
    analysis: Dict[str, Any]


class LuckPillar(BaseModel):
    index: int
    ganzhi: str
    stem_ten_god: str
    start_age: int
    end_age: int
    start_year: int
    end_year: int
    nayin: str


class BaZiResult(BaseModel):
    schema_version: str
    rule_id: str
    system: str
    school: str
    rule_version: str
    status: str
    gender: str
    input: BaZiInput
    solar_datetime: str
    lunar_datetime: str
    day_master: str
    # 对外结果按 facts 包裹排盘事实；旧 models.py 里的顶层 pillars 与实际响应不一致，
    # 这里改为按实际信封校验，避免“声明了契约但从未接线”。
    facts: Dict[str, Any]
    element_scores: Dict[str, float]
    element_distribution: List[ElementDistribution]
    day_master_strength: DayMasterStrength
    all_shensha: Dict[str, List[str]]
    luck_start_info: Dict[str, Any]
    luck_pillars: List[LuckPillar]
    advisory: Dict[str, str]
    judgements: List[Any]
    warnings: List[str]
