"""玄空替卦起星盘（draft_unsigned）回归测试。

依据：库内《沈氏玄空學》「起星图」实例与「二十四山配九星图」吹齑子挨星口诀。
两则原典实例给出确定性排盘事实，用于校验起星盘算法：

- 四运午山子向兼：「九到向，九之天元即午，挨弼星，仍九入中，午阴逆行；
  八到山，八之天元即艮，挨破军，故不用八而以七入中，艮阳顺行。」
- 一运乙山辛向兼：「三到向，三之人元即乙，挨巨门，故不用三而以二入中，乙阴逆行；
  八到山，八之人元即寅，挨弼星，故不用八而以九入中，寅阳顺行。」

替星表存在「工程草稿8/库内原典9」的口径冲突，签署前一律标 draft_unsigned；
本测试锁定冲突被如实标注、起星盘默认关闭、且不覆盖下卦挨星盘。
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
        # 下卦挨星盘逐格完全一致，起星盘只并列附加
        self.assertEqual(plain["facts"]["grid"], with_chart["facts"]["grid"])
        self.assertEqual(plain["facts"]["conditions"], with_chart["facts"]["conditions"])

    def test_discrepancy_and_unsigned_status_are_explicit(self):
        t = self._chart("午", 4)
        self.assertEqual(t["rule_id"], TIHUA_CHART_RULE_ID)
        self.assertEqual(t["star_table_status"], "draft_unsigned")
        d = t["table_discrepancy"]
        self.assertEqual(d["status"], "pending_expert_signoff")
        self.assertEqual(d["engineering_draft"]["star"], 8)
        self.assertEqual(d["library_classic"]["star"], 9)
        self.assertEqual(set(d["mountains"]), {"寅", "午", "庚", "丁"})
        # 两表仅这四山不同（草稿8/原典9），其余二十山完全一致
        excluded = ("寅", "午", "庚", "丁")
        self.assertEqual(
            {k: v for k, v in TIHUA_STAR.items() if k not in excluded},
            {k: v for k, v in TIHUA_STAR_LIBRARY_CLASSIC.items() if k not in excluded},
        )
        self.assertEqual({k: TIHUA_STAR[k] for k in excluded}, {k: 8 for k in excluded})
        self.assertEqual({k: TIHUA_STAR_LIBRARY_CLASSIC[k] for k in excluded},
                         {k: 9 for k in excluded})
        self.assertEqual(TIHUA_TABLE_DISCREPANCY["mountains"], d["mountains"])

    def test_all_mountain_period_combinations_have_valid_charts(self):
        # 24 山 × 9 运：completed 时九宫必为 1..9 全排列且入中=替星；
        # 中宫五等未签署口径必须 unresolved 且不生成猜测值。
        completed = unresolved = 0
        for mountain in MOUNTAINS:
            for period in range(1, 10):
                t = self._chart(mountain.name, period)
                for side in ("sitting", "facing"):
                    e = t[side]
                    if e["status"] == "completed":
                        self.assertEqual(len(e["chart"]), 9)
                        self.assertEqual(set(e["chart"]), set(PALACE_ORDER))
                        self.assertEqual(sorted(e["chart"].values()), list(range(1, 10)))
                        self.assertEqual(e["chart"]["中"], e["tihua_star"])
                        self.assertEqual(e["tihua_star"],
                                         TIHUA_STAR_LIBRARY_CLASSIC[e["substitute_mountain"]])
                        completed += 1
                    else:
                        self.assertEqual(e["status"], "unresolved")
                        self.assertNotIn("chart", e)
                        self.assertIn("reason", e)
                        unresolved += 1
                if t["sitting"]["status"] == t["facing"]["status"] == "completed":
                    self.assertEqual(t["status"], "completed")
                else:
                    self.assertEqual(t["status"], "unresolved")
        self.assertGreater(completed, 0)
        self.assertGreater(unresolved, 0, "应存在中宫五等未签署口径，且被如实标注")

    def test_middle_palace_five_is_never_guessed(self):
        # 到山/到向运星为 5 时，中宫无元龙山可取，必须 unresolved
        found = False
        for mountain in MOUNTAINS:
            for period in range(1, 10):
                t = self._chart(mountain.name, period)
                for side in ("sitting", "facing"):
                    e = t[side]
                    if e.get("arriving_star") == 5:
                        found = True
                        self.assertEqual(e["status"], "unresolved")
                        self.assertNotIn("chart", e)
        self.assertTrue(found, "九运×24山应出现到星为中宫五的组合")

    def test_no_fortune_judgements_in_chart(self):
        # 排盘事实不含吉凶断语：只产出星盘事实/签署状态/口径分歧，不下结论
        t = self._chart("午", 4)
        for key in ("judgements", "verdict", "fortune", "score", "rating"):
            self.assertNotIn(key, t)
        for key in ("judgements", "verdict", "fortune", "score"):
            for side in ("sitting", "facing"):
                self.assertNotIn(key, t[side])
        # note/trace 里不得出现具体断语词（"吉凶断语"作为否定式说明允许）
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
