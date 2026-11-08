"""替星表与中宫五的「逆行计算」回归护栏。

期望数据不再手写在测试里，而是由 ``scripts/build_xuankong_reverse_cases.py``
从库内《沈氏玄空學》「起星图二百一十六局」原文独立解析后落成
``data/validation-cases/xuankong-reverse-cases.json``。原始语料
``data/generated/`` 不入库，CI 读取派生样例；本地有语料时再校验样例未过期。

解析口径（见 ``app.fengshui.classic_reverse``）：
- 216 个起星图局，每局应有山/向两条，共 432 条；
- 实际语料缺 1 行（九运申山寅向兼）、1 行 OCR 多字无法解析，另有 4 个
  单字 OCR 错字按同句源山字义订正；最终可解析 430 条。
"""
import json
import unittest
from collections import defaultdict
from pathlib import Path

from app.fengshui.classic_reverse import parse_classic_reverse_cases
from app.fengshui.rules import MOUNTAINS
from app.fengshui.xuankong import TIHUA_STAR, calculate_xuankong

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "validation-cases"
    / "xuankong-reverse-cases.json"
)


def _load_fixture():
    document = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    return document, document["cases"]


class ReverseComputationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document, cls.cases = _load_fixture()

    def _observed(self):
        observed = defaultdict(lambda: defaultdict(int))
        no_sub = 0
        for mountain in MOUNTAINS:
            for period in range(1, 10):
                t = calculate_xuankong(mountain.name, period=period,
                                       include_tihua_chart=True)["facts"]["tihua_chart"]
                for side in ("sitting", "facing"):
                    e = t[side]
                    self.assertEqual(e["status"], "completed")
                    observed[e["arriving_star"]][e["tihua_star"]] += 1
                    if e.get("no_substitute"):
                        no_sub += 1
        return observed, no_sub

    def test_fixture_has_216_blocks_and_430_parseable_cases(self):
        self.assertEqual(self.document["block_count"], 216)
        self.assertEqual(self.document["case_count"], 430)
        self.assertEqual(self.document["missing_block_count"], 1)
        self.assertEqual(self.document["invalid_line_count"], 1)
        self.assertEqual(self.document["ocr_corrected_count"], 4)
        self.assertEqual(len(self.cases), 430)

    def test_every_implemented_pair_exists_in_classic_cases(self):
        observed, _ = self._observed()
        classic_pairs = {
            (case["arriving_star"], case["entering_star"])
            for case in self.cases
        }
        for arriving, targets in observed.items():
            for entering in targets:
                self.assertIn(
                    (arriving, entering),
                    classic_pairs,
                    "到星%s→入中%s 不在原典实例中" % (arriving, entering),
                )

    def test_every_classic_pair_is_implemented(self):
        observed, _ = self._observed()
        classic_pairs = {
            (case["arriving_star"], case["entering_star"])
            for case in self.cases
        }
        for arriving, entering in classic_pairs:
            self.assertIn(
                entering,
                observed[arriving],
                "原典有到星%s→入中%s，实现没有覆盖" % (arriving, entering),
            )

    def test_source_mountain_mapping_matches_classic_cases(self):
        checked = 0
        for case in self.cases:
            source = case["source_mountain"]
            if not source:
                continue
            self.assertEqual(
                TIHUA_STAR[source],
                case["entering_star"],
                "原典 %s 的源山%s 与替星表不符" % (case["block"], source),
            )
            checked += 1
        self.assertEqual(checked, 381)

    def test_every_classic_pair_set_matches_implementation(self):
        observed, _ = self._observed()
        classic_pairs = {
            (case["arriving_star"], case["entering_star"])
            for case in self.cases
        }
        for arriving, targets in observed.items():
            self.assertEqual(
                set(targets),
                {entering for (a, entering) in classic_pairs if a == arriving},
                "到星%s 的入中星集合与原典不符" % arriving,
            )

    def test_no_left_auxiliary_8_in_entering_results(self):
        # 原典 216 局从未出现「入中8」；工程草稿误值 8 会立刻暴露
        observed, _ = self._observed()
        for arriving, targets in observed.items():
            self.assertNotIn(8, targets, "到星%s 出现原典没有的入中8" % arriving)

    def test_frequency_structure_matches_classic(self):
        # 实现侧是完整 24 山 × 9 运 × 2 路；原典 430 条因缺行/OCR 少 2 条，
        # 故只校验实现频次结构与「无替」总数，不把缺行补成假数据。
        observed, no_sub = self._observed()
        self.assertEqual(no_sub, 48)
        self.assertEqual(sum(1 for c in self.cases if c["entering_star"] == 5), 48)
        for arriving in (4, 5, 6):
            self.assertEqual(len(observed[arriving]), 1)
            self.assertEqual(sum(observed[arriving].values()), 48)
        for arriving in (1, 2, 3, 7, 8, 9):
            counts = sorted(observed[arriving].values())
            self.assertEqual(counts, [16, 32], "到星%s 频次异常" % arriving)

    def test_tihua_star_table_is_classic_bishop_nine(self):
        for name in ("寅", "午", "庚", "丁"):
            self.assertEqual(TIHUA_STAR[name], 9)
        self.assertEqual(set(TIHUA_STAR.values()), {1, 2, 6, 7, 9})
        self.assertNotIn(8, TIHUA_STAR.values())

    def test_fixture_is_current_when_corpus_is_available(self):
        corpus = (
            Path(__file__).resolve().parents[2]
            / "data"
            / "generated"
            / "wikisource-corpus"
            / "corpus_chunks.jsonl"
        )
        if not corpus.exists():
            self.skipTest("本地典籍语料未生成，跳过派生样例新鲜度校验")
        parsed = parse_classic_reverse_cases(corpus)
        self.assertEqual(len(parsed["cases"]), self.document["case_count"])
        self.assertEqual(len(parsed["missing_blocks"]), self.document["missing_block_count"])
        self.assertEqual(len(parsed["invalid_lines"]), self.document["invalid_line_count"])
        self.assertEqual(parsed["cases"], self.cases)


if __name__ == "__main__":
    unittest.main()
