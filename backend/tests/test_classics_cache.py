"""典籍库缓存行为测试：懒加载/缓存复用/强制重建/开发期 mtime 热失效。

默认路径（CLASSICS_AUTO_RELOAD 关闭）与生产一致：首次构建后缓存复用，无额外开销。
开启热失效后，语料 mtime 变化即重建，免去开发期重启。
"""
import unittest
from unittest import mock

import app.common.classics as classics


class ClassicsCacheTests(unittest.TestCase):
    def tearDown(self):
        classics.reset_library_cache()

    def test_lazy_load_and_cache_reuse(self):
        lib1 = classics.get_library()
        self.assertIsNotNone(lib1)
        lib2 = classics.get_library()
        # 默认关闭热失效：应复用同一实例（同一对象，非仅等价）
        self.assertIs(lib1, lib2)

    def test_reload_forces_new_instance(self):
        lib1 = classics.get_library()
        lib2 = classics.reload_library()
        self.assertIsNot(lib1, lib2)
        # 重建后再次取库应复用新实例
        self.assertIs(lib2, classics.get_library())

    def test_auto_reload_rebuilds_on_mtime_change(self):
        # 模拟开启热失效且 mtime 变化 -> 重建
        # 调用顺序：首次构建设 mtime(100) -> 二次检测(200)触发重建 -> 重建后再设 mtime(200)
        with mock.patch.object(classics, "CLASSICS_AUTO_RELOAD", True), \
             mock.patch.object(classics, "_corpus_mtime", side_effect=[100.0, 200.0, 200.0]):
            classics.reset_library_cache()
            first = classics.get_library()
            second = classics.get_library()  # mtime 变化触发重建
            self.assertIsNot(first, second)

    def test_auto_reload_keeps_same_instance_when_mtime_unchanged(self):
        with mock.patch.object(classics, "CLASSICS_AUTO_RELOAD", True), \
             mock.patch.object(classics, "_corpus_mtime", return_value=123.0):
            classics.reset_library_cache()
            first = classics.get_library()
            second = classics.get_library()  # mtime 不变 -> 复用
            self.assertIs(first, second)


if __name__ == "__main__":
    unittest.main()
