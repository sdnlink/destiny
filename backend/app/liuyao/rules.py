from dataclasses import asdict, dataclass
from types import MappingProxyType

from app.common.trigrams import TRIGRAM_CATALOG, trigram_to_bits


NAJIA = MappingProxyType({
    "乾": ("甲", "壬", ("子", "寅", "辰"), ("午", "申", "戌")),
    "坤": ("乙", "癸", ("未", "巳", "卯"), ("丑", "亥", "酉")),
    "震": ("庚", "庚", ("子", "寅", "辰"), ("午", "申", "戌")),
    "巽": ("辛", "辛", ("丑", "亥", "酉"), ("未", "巳", "卯")),
    "坎": ("戊", "戊", ("寅", "辰", "午"), ("申", "戌", "子")),
    "离": ("己", "己", ("卯", "丑", "亥"), ("酉", "未", "巳")),
    "艮": ("丙", "丙", ("辰", "午", "申"), ("戌", "子", "寅")),
    "兑": ("丁", "丁", ("巳", "卯", "丑"), ("亥", "酉", "未")),
})
SIX_SPIRITS = ("青龙", "朱雀", "勾陈", "螣蛇", "白虎", "玄武")
SIX_SPIRIT_START = MappingProxyType({
    "甲": 0, "乙": 0, "丙": 1, "丁": 1, "戊": 2,
    "己": 3, "庚": 4, "辛": 4, "壬": 5, "癸": 5,
})
PALACE_STAGES = (
    ("本宫", (), 6), ("一世", (1,), 1), ("二世", (1, 2), 2),
    ("三世", (1, 2, 3), 3), ("四世", (1, 2, 3, 4), 4),
    ("五世", (1, 2, 3, 4, 5), 5), ("游魂", (1, 2, 3, 5), 4),
    ("归魂", (5,), 3),
)


@dataclass(frozen=True)
class Palace:
    name: str
    element: str
    stage: str
    host_line: int
    response_line: int

    def to_dict(self):
        return asdict(self)


def _build_palace_index():
    result = {}
    for trigram in TRIGRAM_CATALOG:
        pure = trigram_to_bits(trigram) + trigram_to_bits(trigram)
        for stage, changes, host_line in PALACE_STAGES:
            bits = tuple(1 - bit if position in changes else bit for position, bit in enumerate(pure, 1))
            result[bits] = Palace(
                name=trigram.name,
                element=trigram.element,
                stage=stage,
                host_line=host_line,
                response_line=((host_line + 2) % 6) + 1,
            )
    if len(result) != 64:
        raise RuntimeError("eight-palace index must contain 64 unique hexagrams")
    return MappingProxyType(result)


PALACE_BY_LINES = _build_palace_index()
