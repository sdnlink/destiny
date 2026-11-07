"""玄空替卦起星盘回归测试（据库内《沈氏玄空學》起星图 216 局）。

原典依据：
- 吹齑子简易挨星口诀：「子癸甲申贪狼寻，坤壬乙卯未巨门。乾巽六位皆武曲，
  艮丙辛酉丑破军。若向寅午庚丁上，一律挨来是弼星。」
- 蒋大鸿授姜汝皋挨星口诀：「…寅午庚丁上，右弼四星临。」
- 起星图实例：「四运午山子向兼…九到向，九之天元即午，挨弼星，仍九入中，
  午阴逆行；八到山，八之天元即艮，挨破军，故不用八而以七入中，艮阳顺行。」
- 「一运乙山辛向兼…三到向，三之人元即乙，挨巨门，故不用三而以二入中，
  乙阴逆行；八到山，八之人元即寅，挨弼星，故不用八而以九入中，寅阳顺行。」
- 中宫五：「五到向，无替可寻，四正逆行」「五到山，无替可寻」；
  「若中宫五数戊阳己阴，此阴阳视山向为准」。

替星表寅午庚丁由两套口诀 + 422 条起星图实例逆行计算裁定为弼星 9，
原工程草稿 8（左辅）已废弃；中宫五不替、仍 5 入中，顺逆视山向阴阳。
产物仍为工程基线，不含吉凶断语。
"""
import unittest

from fastapi.testclient import TestClient

from app.fengshui.rules import MOUNTAINS
from app.fengshui.xuankong import (
    PALACE_ORDER, TIHUA_CHART_RULE_ID, TIHUA_STAR,
    TIHUA_STAR_LIBRARY_CLASSIC, TIHUA_TABLE_DISCREPANCY,
    calculate_xuankong,
)
from app.main import app


class XuankongTihuaChartTests(unittest.TestCase):
    def _chart(self, mountain, period):
        return calculate_xuankong(
            mountain, period=period, include_tihua_chart=True
        )["facts"]["tihua_chart"]

    def test_classic_example_4_yun_wu_shan_zi_xiang(self):
        # 四运午山子向兼：到山8→艮(天元)→破军7→阳顺；到向9→午(天元)→弼9→阴逆
        t = self._chart("午", 4)
        self.assertEqual(t["status"], "completed")
        self.assertEqual(t["signed"], False)
        s, f = t["sitting"], t["facing"]
        self.assertEqual((s["arriving_star"], s["yuan_dragon"], s["substitute_mountain"],
                          s["tihua_star"], s["fly_direction"]), (8, "天", "艮", 7, "顺飞"))
        self.assertEqual((f["arriving_star"], f["yuan_dragon"], f["substitute_mountain"],
                          f["tihua_star"], f["fly_direction"]), (9, "天", "午", 9, "逆飞"))
        self.assertEqual(s["chart"]["中"], 7)
        self.assertEqual(f["chart"]["中"], 9)

    def test_classic_example_1_yun_yi_shan_xin_xiang(self):
        # 一运乙山辛向兼：到山8→寅(人元)→弼9→阳顺；到向3→乙(人元)→巨门2→阴逆
        t = self._chart("乙", 1)
        self.assertEqual(t["status"], "completed")
        s, f = t["sitting"], t["facing"]
        self.assertEqual((s["arriving_star"], s["yuan_dragon"], s["substitute_mountain"],
                          s["tihua_star"], s["fly_direction"]), (8, "人", "寅", 9, "顺飞"))
        self.assertEqual((f["arriving_star"], f["yuan_dragon"], f["substitute_mountain"],
                          f["tihua_star"], f["fly_direction"]), (3, "人", "乙", 2, "逆飞"))

    def test_default_off_and_no_contamination_of_xiagua(self):
        plain = calculate_xuankong("午", period=4)
        self.assertNotIn("tihua_chart", plain["facts"])
        with_chart = calculate_xuankong("午", period=4, include_tihua_chart=True)
        self.assertEqual(plain["facts"]["grid"], with_chart["facts"]["grid"])
        self.assertEqual(plain["facts"]["conditions"], with_chart["facts"]["conditions"])

    def test_star_table_resolved_by_classics(self):
        t = self._chart("午", 4)
        self.assertEqual(t["rule_id"], TIHUA_CHART_RULE_ID)
        self.assertEqual(t["star_table_status"], "resolved_by_library_classics")
        d = t["resolution_record"]
        self.assertEqual(d["status"], "resolved_by_library_classics")
        self.assertEqual(d["resolved_value"]["star"], 9)
        self.assertEqual(d["superseded_value"]["star"], 8)
        self.assertEqual(set(d["mountains"]), {"寅", "午", "庚", "丁"})
        # 两表已统一，寅午庚丁均为弼星 9
        self.assertIs(TIHUA_STAR_LIBRARY_CLASSIC, TIHUA_STAR)
        for name in ("寅", "午", "庚", "丁"):
            self.assertEqual(TIHUA_STAR[name], 9)
        self.assertEqual(len(TIHUA_STAR), 24)
        self.assertEqual(TIHUA_TABLE_DISCREPANCY["mountains"], d["mountains"])

    def test_all_mountain_period_combinations_have_valid_charts(self):
        # 24 山 × 9 运：起星盘恒 completed（含中宫五），九宫必为 1..9 全排列
        completed = no_substitute = 0
        for mountain in MOUNTAINS:
            for period in range(1, 10):
                t = self._chart(mountain.name, period)
                self.assertEqual(t["status"], "completed")
                for side in ("sitting", "facing"):
                    e = t[side]
                    self.assertEqual(e["status"], "completed")
                    self.assertEqual(len(e["chart"]), 9)
                    self.assertEqual(set(e["chart"]), set(PALACE_ORDER))
                    self.assertEqual(sorted(e["chart"].values()), list(range(1, 10)))
                    self.assertEqual(e["chart"]["中"], e["tihua_star"])
                    if e.get("no_substitute"):
                        no_substitute += 1
                    else:
                        self.assertEqual(e["tihua_star"],
                                         TIHUA_STAR[e["substitute_mountain"]])
                    completed += 1
        self.assertEqual(completed, 24 * 9 * 2)
        self.assertEqual(no_substitute, 48)

    def test_middle_palace_five_no_substitute(self):
        # 原典「五到向，无替可寻」：不替、仍 5 入中，顺逆视山向阴阳
        found = 0
        for mountain in MOUNTAINS:
            for period in range(1, 10):
                t = self._chart(mountain.name, period)
                for side in ("sitting", "facing"):
                    e = t[side]
                    if e.get("arriving_star") != 5:
                        continue
                    found += 1
                    self.assertTrue(e["no_substitute"])
                    self.assertEqual(e["tihua_star"], 5)
                    self.assertIsNone(e["substitute_mountain"])
                    self.assertEqual(e["chart"]["中"], 5)
                    self.assertIn(e["fly_reference_mountain"],
                                  (mountain.name, t["facing"].get("fly_reference_mountain"),
                                   "子", "午", "卯", "酉", "乾", "巽", "艮", "坤"))
                    self.assertIn(e["fly_direction"], ("顺飞", "逆飞"))
        self.assertEqual(found, 48)

    def test_four_positive_mountains_five_fly_backward(self):
        # 「五到向，无替可寻，四正逆行」：四正子午卯酉为阴 → 逆飞
        for name in ("子", "午", "卯", "酉"):
            for period in range(1, 10):
                t = self._chart(name, period)
                for side in ("sitting", "facing"):
                    e = t[side]
                    if e.get("no_substitute") and e["fly_reference_mountain"] in (
                            "子", "午", "卯", "酉"):
                        self.assertEqual(e["fly_direction"], "逆飞")

    def test_no_fortune_judgements_in_chart(self):
        t = self._chart("午", 4)
        for key in ("judgements", "verdict", "fortune", "score", "rating"):
            self.assertNotIn(key, t)
        blob = str(t)
        for word in ("大吉", "大凶", "准确率", "总分", "宜忌"):
            self.assertNotIn(word, blob)

    def test_api_get_and_post_passthrough(self):
        client = TestClient(app)
        off = client.get("/v1/fengshui/xuankong",
                         params={"sitting_mountain": "午", "year": 2026})
        self.assertNotIn("tihua_chart", off.json()["data"]["facts"])

        get = client.get("/v1/fengshui/xuankong",
                         params={"sitting_mountain": "午", "period": 4,
                                 "include_tihua_chart": "true"})
        self.assertEqual(get.status_code, 200)
        self.assertEqual(get.json()["data"]["facts"]["tihua_chart"]["sitting"]["tihua_star"], 7)

        post = client.post("/v1/fengshui/xuankong",
                           json={"sitting_mountain": "乙", "period": 1,
                                 "include_tihua_chart": True})
        self.assertEqual(post.status_code, 200)
        self.assertEqual(post.json()["data"]["facts"]["tihua_chart"]["facing"]["tihua_star"], 2)


if __name__ == "__main__":
    unittest.main()
