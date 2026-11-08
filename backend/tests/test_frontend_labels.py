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
from app.workflow.scheduler import DEFAULT_METHOD, REQUEST_BUILDERS, SUPPORTED_SYSTEMS, SYSTEM_LABELS


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

    def test_system_ids_and_labels_match_backend(self):
        block = self.source.split("export const SYSTEMS = [", 1)[1].split("];", 1)[0]
        entries = ENTRY_PATTERN.findall(block)
        self.assertEqual([entry[0] for entry in entries], list(SUPPORTED_SYSTEMS))
        for system_id, label in entries:
            if system_id in SYSTEM_LABELS:
                self.assertEqual(label, SYSTEM_LABELS[system_id], system_id)

    def test_frontend_casting_methods_are_supported_by_backend(self):
        # 前端下拉允许的每种「体系 × 起盘方式」都必须有后端构造器；
        # 否则用户选中的方法会被 scheduler 静默退到 default，界面与实际盘面不符。
        block = self.source.split("const CASTING_METHOD_IDS_BY_SYSTEM = {", 1)[1].split("};", 1)[0]
        entries = dict(re.findall(r"([a-z_]+):\s*\[([^\]]*)\]", block))
        for system_id, raw_ids in entries.items():
            ids = re.findall(r'"([a-z_]+)"', raw_ids)
            if system_id == "auto":
                continue  # auto 是跨体系默认盘，不绑定单一构造器
            self.assertIn(system_id, REQUEST_BUILDERS, system_id)
            for method in ids:
                if method == DEFAULT_METHOD:
                    continue
                self.assertIn(method, REQUEST_BUILDERS[system_id], f"{system_id}/{method}")


if __name__ == "__main__":
    unittest.main()
