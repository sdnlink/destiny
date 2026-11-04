"""前后端分类清单一致性校验。

事项分类的中文标签在两边各有一份：后端 `app/common/categories.py`
（写进解读与建议正文），前端 `src/lib/labels.js`（渲染下拉与历史列表）。
两边文案一旦漂移，用户在下拉里选「财运」，解读正文却写「财务」。
这里读取前端 JS 源文件逐项比对，改一边漏另一边直接测试失败。
"""

import re
import unittest
from pathlib import Path

from app.common.categories import CATEGORIES, CATEGORY_LABELS, LEGACY_CATEGORY_ALIASES, normalize_category


FRONTEND_LABELS = Path(__file__).resolve().parents[2] / "frontend" / "src" / "lib" / "labels.js"
ENTRY_PATTERN = re.compile(r'\{ id: "([a-z_]+)", label: "([^"]+)" \}')


class FrontendLabelConsistencyTests(unittest.TestCase):
    def setUp(self):
        if not FRONTEND_LABELS.is_file():
            self.skipTest("前端 labels.js 不存在（只部署后端的环境跳过）")
        self.source = FRONTEND_LABELS.read_text(encoding="utf-8")
        block = self.source.split("export const CATEGORIES = [", 1)[1].split("];", 1)[0]
        self.entries = ENTRY_PATTERN.findall(block)

    def test_category_ids_match_backend(self):
        frontend_ids = [entry[0] for entry in self.entries]
        self.assertEqual(frontend_ids, list(CATEGORIES))

    def test_category_labels_match_backend(self):
        for category_id, label in self.entries:
            self.assertEqual(label, CATEGORY_LABELS[category_id], category_id)

    def test_frontend_aliases_match_backend(self):
        block = self.source.split("export const LEGACY_CATEGORY_ALIASES = {", 1)[1].split("};", 1)[0]
        aliases = dict(re.findall(r"([a-z_]+): \"([a-z_]+)\"", block))
        for legacy, canonical in LEGACY_CATEGORY_ALIASES.items():
            self.assertEqual(aliases.get(legacy), canonical, legacy)

    def test_frontend_normalize_accepts_all_backend_categories(self):
        # 前端 normalizeCategory 的兜底规则：未知键收敛到 other，与后端宽松模式一致
        for category_id in CATEGORIES:
            self.assertEqual(normalize_category(category_id), category_id)


if __name__ == "__main__":
    unittest.main()
