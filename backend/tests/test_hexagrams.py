"""文王卦序矩阵（KING_WEN_MATRIX）回归测试。

该矩阵被六爻 / 梅花 / 周易等模块共用，用于由上下卦反查卦名与卦序。
历史上曾出现「屯/解」「咸/损」两对格子互换的错误，导致卦名张冠李戴。
本测试以权威文王卦序 + 卦象（上/下卦）为 oracle，锁定全部 64 卦，
防止此类矩阵错位再次回归。
"""
import unittest

from app.common.hexagrams import (
    KING_WEN_MATRIX,
    HEXAGRAM_NAMES,
    trigram_to_bits,
    get_hexagram_by_lines,
)
from app.common.trigrams import TRIGRAM_CATALOG
from app.liuyao.engine import number_cast

TG = {t.name: t for t in TRIGRAM_CATALOG}
# 三爻名 -> 数字 乾1 兑2 离3 震4 巽5 坎6 艮7 坤8
TNUM = {"乾": 1, "兑": 2, "离": 3, "震": 4, "巽": 5, "坎": 6, "艮": 7, "坤": 8}

# 权威 (卦序: (下卦名, 上卦名)) -- 据文王卦序 + 卦象(上/下卦)
ORACLE = [
    (1, ("乾", "乾")), (2, ("坤", "坤")), (3, ("坎", "震")), (4, ("坎", "艮")),
    (5, ("乾", "坎")), (6, ("坎", "乾")), (7, ("坎", "坤")), (8, ("坤", "坎")),
    (9, ("乾", "巽")), (10, ("兑", "乾")), (11, ("乾", "坤")), (12, ("坤", "乾")),
    (13, ("离", "乾")), (14, ("乾", "离")), (15, ("艮", "坤")), (16, ("坤", "震")),
    (17, ("震", "兑")), (18, ("巽", "艮")), (19, ("兑", "坤")), (20, ("坤", "巽")),
    (21, ("震", "离")), (22, ("离", "艮")), (23, ("坤", "艮")), (24, ("震", "坤")),
    (25, ("震", "乾")), (26, ("乾", "艮")), (27, ("震", "艮")), (28, ("巽", "兑")),
    (29, ("坎", "坎")), (30, ("离", "离")), (31, ("兑", "艮")), (32, ("巽", "震")),
    (33, ("艮", "乾")), (34, ("乾", "震")), (35, ("坤", "离")), (36, ("离", "坤")),
    (37, ("离", "巽")), (38, ("兑", "离")), (39, ("艮", "坎")), (40, ("震", "坎")),
    (41, ("艮", "兑")), (42, ("震", "巽")), (43, ("乾", "兑")), (44, ("巽", "乾")),
    (45, ("坤", "兑")), (46, ("巽", "坤")), (47, ("坎", "兑")), (48, ("巽", "坎")),
    (49, ("离", "兑")), (50, ("巽", "离")), (51, ("震", "震")), (52, ("艮", "艮")),
    (53, ("艮", "巽")), (54, ("兑", "震")), (55, ("离", "震")), (56, ("艮", "离")),
    (57, ("巽", "巽")), (58, ("兑", "兑")), (59, ("坎", "巽")), (60, ("兑", "坎")),
    (61, ("兑", "巽")), (62, ("艮", "震")), (63, ("离", "坎")), (64, ("坎", "离")),
]


class TestKingWenMatrix(unittest.TestCase):
    def test_matrix_covers_all_64(self):
        seen = sorted({v for row in KING_WEN_MATRIX for v in row})
        self.assertEqual(seen, list(range(1, 65)))

    def test_matrix_matches_oracle(self):
        for ordn, (low, up) in ORACLE:
            ui, li = TNUM[up], TNUM[low]
            self.assertEqual(
                KING_WEN_MATRIX[ui - 1][li - 1], ordn,
                msg="matrix cell upper=%d lower=%d" % (ui, li),
            )

    def test_get_hexagram_by_lines_matches_oracle(self):
        for ordn, (low, up) in ORACLE:
            lines = tuple(
                list(trigram_to_bits(TG[low])) + list(trigram_to_bits(TG[up]))
            )
            h = get_hexagram_by_lines(lines)
            self.assertEqual(h.ordinal, ordn)
            self.assertEqual(h.name, HEXAGRAM_NAMES[ordn - 1])

    def test_number_cast_matches_oracle(self):
        for ordn, (low, up) in ORACLE:
            r = number_cast(TNUM[low], TNUM[up], "2026-08-15T16:00:00", "Asia/Shanghai")
            self.assertEqual(
                r["facts"]["original"]["name"], HEXAGRAM_NAMES[ordn - 1],
                msg="ordinal %d" % ordn,
            )


if __name__ == "__main__":
    unittest.main()
