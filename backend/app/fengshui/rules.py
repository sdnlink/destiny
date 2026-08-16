from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Mountain:
    ordinal: int
    name: str
    center_degree: float
    category: str
    trigram: str
    element: str
    direction: str

    def to_dict(self):
        value = asdict(self)
        value["start_degree"] = (self.center_degree - 7.5) % 360
        value["end_degree"] = (self.center_degree + 7.5) % 360
        return value


_MOUNTAIN_ROWS = (
    ("子", "地支", "坎", "水", "北"), ("癸", "天干", "坎", "水", "北"),
    ("丑", "地支", "艮", "土", "东北"), ("艮", "八卦", "艮", "土", "东北"),
    ("寅", "地支", "艮", "木", "东北"), ("甲", "天干", "震", "木", "东"),
    ("卯", "地支", "震", "木", "东"), ("乙", "天干", "震", "木", "东"),
    ("辰", "地支", "巽", "土", "东南"), ("巽", "八卦", "巽", "木", "东南"),
    ("巳", "地支", "巽", "火", "东南"), ("丙", "天干", "离", "火", "南"),
    ("午", "地支", "离", "火", "南"), ("丁", "天干", "离", "火", "南"),
    ("未", "地支", "坤", "土", "西南"), ("坤", "八卦", "坤", "土", "西南"),
    ("申", "地支", "坤", "金", "西南"), ("庚", "天干", "兑", "金", "西"),
    ("酉", "地支", "兑", "金", "西"), ("辛", "天干", "兑", "金", "西"),
    ("戌", "地支", "乾", "土", "西北"), ("乾", "八卦", "乾", "金", "西北"),
    ("亥", "地支", "乾", "水", "西北"), ("壬", "天干", "坎", "水", "北"),
)

MOUNTAINS = tuple(
    Mountain(index + 1, name, index * 15.0, category, trigram, element, direction)
    for index, (name, category, trigram, element, direction) in enumerate(_MOUNTAIN_ROWS)
)
