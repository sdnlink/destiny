"""Data models for Qimen Dunjia (奇门遁甲) calculations."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QimenInput(BaseModel):
    local_datetime: str = Field(..., example="2026-08-15T16:00:00")
    timezone: str = Field("Asia/Shanghai", example="Asia/Shanghai")
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    use_true_solar_time: bool = False


class QimenPalace(BaseModel):
    palace_number: int
    palace_name: str
    trigram: str
    element: str
    direction: str
    di_pan_stem: str
    tian_pan_stem: str
    nine_star: str
    eight_gate: str
    eight_spirit: str
    is_tian_qin_present: bool = False
    qin_stem: Optional[str] = None
    patterns: List[Dict[str, str]] = []


class QimenResult(BaseModel):
    rule_id: str
    system: str
    solar_datetime: str
    lunar_datetime: str
    ganzhi: Dict[str, str]
    solar_term: str
    dun_type: str  # 阳遁 / 阴遁
    ju_number: int  # 1 ~ 9 局
    yuan_type: str  # 上元 / 中元 / 下元
    xun_shou: str   # 旬首 (如 甲子戊)
    zhi_fu_star: str  # 值符九星 (如 天蓬星)
    zhi_shi_gate: str # 值使八门 (如 休门)
    zhi_fu_palace: int # 值符落宫
    zhi_shi_palace: int # 值使落宫
    palaces: Dict[int, QimenPalace]
    favorable_directions: List[Dict[str, Any]]
    advisory: Dict[str, str]
