"""大六壬三传发传「规则结构不变式」测试。

与 test_daliuren_special_transmissions.py 互补（不重复）：
- 既有测试断言若干经典卦例的**精确三传数值**，以及 720 组合的 status/长度/课体集合；
- 本测试对**全部 720 组合**（60 甲子 × 12 天盘偏移）断言各课体的**结构性规则**：
  克系中末传按天盘顺数、昴星初传取酉、八专/别责中末传取日上神、
  返吟中末传取辰/日上神、伏吟三传合法。不依赖记忆中的卦例数值，
  锁定的是《九宗门》排盘逻辑本身。

另含轻量端到端冒烟：真实 time_cast（走 lunar_python 历法）也不产生 pending。
"""
import unittest

from app.common.ganzhi import EARTHLY_BRANCHES, polarity
from app.daliuren.engine import _four_lessons, _three_transmissions, time_cast


_STEMS = "甲乙丙丁戊己庚辛壬癸"
_BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
_SEXAGENARY_CYCLE = [_STEMS[i % 10] + _BRANCHES[i % 12] for i in range(60)]

PENDING_WARNING = "未生成三传猜测值"


def _plate(offset):
    return {
        ground: EARTHLY_BRANCHES[(index + offset) % 12]
        for index, ground in enumerate(EARTHLY_BRANCHES)
    }


def _all_cases():
    for day_pillar in _SEXAGENARY_CYCLE:
        for offset in range(12):
            plate = _plate(offset)
            lessons = _four_lessons(day_pillar, plate)
            result = _three_transmissions(day_pillar, plate, lessons)
            yield day_pillar, plate, lessons, result


class DaLiuRenTransmissionInvariantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = list(_all_cases())

    def _by_type(self, lesson_type):
        return [(dp, plate, lessons, r) for dp, plate, lessons, r in self.cases
                if r["lesson_type"] == lesson_type]

    def test_all_combinations_have_three_valid_branches(self):
        # 前置：720 组合三传必然可算（与既有穷举互证，本测试关注结构）
        self.assertEqual(len(self.cases), 720)
        for dp, _, _, r in self.cases:
            ch = r["transmissions"]
            self.assertEqual(r["status"], "completed", (dp, r.get("lesson_type")))
            self.assertEqual(len(ch), 3, (dp, r.get("lesson_type")))
            for b in ch:
                self.assertIn(b, EARTHLY_BRANCHES, (dp, r.get("lesson_type"), b))

    def test_ke_chain_schools_follow_heaven_plate(self):
        # 贼克/克/比用/涉害/遥克：中传=初传上神，末传=中传上神（天盘顺数）
        checked = 0
        for dp, plate, _, r in self.cases:
            if r["lesson_type"] not in ("贼克", "克", "比用", "涉害", "遥克"):
                continue
            ch = r["transmissions"]
            self.assertEqual(ch[1], plate[ch[0]], (dp, r["lesson_type"], ch))
            self.assertEqual(ch[2], plate[ch[1]], (dp, r["lesson_type"], ch))
            checked += 1
        self.assertGreater(checked, 0)

    def test_bazhuan_bieze_middle_final_equal_day_upper(self):
        # 八专、别责：中末传均取日上神（四课第一课之上神）
        checked = 0
        for dp, _, lessons, r in self.cases:
            if r["lesson_type"] not in ("八专", "别责"):
                continue
            day_upper = lessons[0]["upper"]
            ch = r["transmissions"]
            self.assertEqual(ch[1], day_upper, (dp, r["lesson_type"]))
            self.assertEqual(ch[2], day_upper, (dp, r["lesson_type"]))
            checked += 1
        self.assertGreater(checked, 0)

    def test_fanyin_middle_final_structure(self):
        # 返吟：中传取辰上神（第三课之上神），末传取日上神（第一课之上神）
        checked = 0
        for dp, _, lessons, r in self.cases:
            if r["lesson_type"] != "返吟":
                continue
            ch = r["transmissions"]
            self.assertEqual(ch[1], lessons[2]["upper"], (dp, ch))
            self.assertEqual(ch[2], lessons[0]["upper"], (dp, ch))
            checked += 1
        self.assertGreater(checked, 0)

    def test_xingxing_initial_is_you(self):
        # 昴星：阳日初传=天盘酉上神；阴日初传=天盘酉所临地盘
        checked = 0
        for dp, plate, _, r in self.cases:
            if r["lesson_type"] != "昴星":
                continue
            ch = r["transmissions"]
            if polarity(dp[0]) == "阳":
                expected = plate["酉"]
            else:
                expected = next(g for g, h in plate.items() if h == "酉")
            self.assertEqual(ch[0], expected, (dp, plate, ch))
            checked += 1
        self.assertGreater(checked, 0)

    def test_fuyin_transmissions_are_valid_branches(self):
        # 伏吟：初传取克/日/支，中末传按刑/冲；断言三传为合法地支且结构自洽
        checked = 0
        for dp, _, _, r in self.cases:
            if r["lesson_type"] != "伏吟":
                continue
            ch = r["transmissions"]
            self.assertEqual(len(ch), 3, (dp, ch))
            for b in ch:
                self.assertIn(b, EARTHLY_BRANCHES, (dp, ch))
            checked += 1
        self.assertGreater(checked, 0)

    def test_all_ten_schools_present(self):
        schools = {r["lesson_type"] for _, _, _, r in self.cases}
        self.assertEqual(schools, {
            "贼克", "克", "比用", "涉害", "遥克",
            "昴星", "伏吟", "八专", "返吟", "别责",
        })

    def test_time_cast_end_to_end_never_pending(self):
        # 真实历法链路（lunar_python 月将/天盘/四课）也不产生 pending 或遗留警告
        samples = [
            "2024-02-14 10:00", "2024-05-06 03:00", "2023-11-22 22:00",
            "2025-08-09 07:00", "2020-01-30 16:00", "2019-06-15 12:00",
        ]
        for local in samples:
            res = time_cast(local, "Asia/Shanghai")
            t = res["facts"]["three_transmissions"]
            self.assertEqual(t["status"], "completed", (local, t))
            self.assertFalse(any(PENDING_WARNING in w for w in res.get("warnings", [])), local)


if __name__ == "__main__":
    unittest.main()
