from typing import List, Optional
from pydantic import BaseModel, Field


class StarInfo(BaseModel):
    name: str
    type: str  # "main" (主星), "lucky" (六吉), "bad" (六煞), "helper" (杂曜/其他)
    brightness: Optional[str] = None  # "庙", "旺", "得", "利", "平", "不", "陷"
    element: Optional[str] = None  # 五行
    si_hua: Optional[str] = None  # "化禄", "化权", "化科", "化忌"


class PalaceInfo(BaseModel):
    index: int  # 0 to 11
    earthly_branch: str  # 子, 丑, 寅, 卯, 辰, 巳, 午, 未, 申, 酉, 戌, 亥
    heavenly_stem: str  # 甲, 乙, 丙...
    name: str  # 命宫, 兄弟, 夫妻, 子女, 财帛, 疾厄, 迁移, 仆役, 官禄, 田宅, 福德, 父母
    original_name: str  # 原始宫名
    is_body_palace: bool = False  # 是否为身宫
    major_limit_start: int  # 大限起始年龄
    major_limit_end: int  # 大限结束年龄
    main_stars: List[StarInfo] = Field(default_factory=list)
    auxiliary_stars: List[StarInfo] = Field(default_factory=list)
    minor_stars: List[StarInfo] = Field(default_factory=list)
    si_hua: List[str] = Field(default_factory=list)


class FourPillars(BaseModel):
    year: str
    month: str
    day: str
    hour: str
    year_stem: str
    year_branch: str
    month_stem: str
    month_branch: str
    day_stem: str
    day_branch: str
    hour_stem: str
    hour_branch: str
