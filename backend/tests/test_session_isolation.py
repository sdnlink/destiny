"""确保测试不会把会话 JSON 写进仓库的 data/sessions。"""
import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.session import get_store


class SessionIsolationTests(unittest.TestCase):
    def test_store_directory_is_not_repository_data_dir(self):
        store_dir = Path(get_store().storage_dir).resolve()
        repo_data_dir = (Path(__file__).resolve().parents[2] / "data" / "sessions").resolve()
        self.assertNotEqual(
            store_dir,
            repo_data_dir,
            "测试会话落到了仓库数据目录，检查 backend/tests/conftest.py 是否生效",
        )
        self.assertTrue(store_dir.is_dir())


if __name__ == "__main__":
    unittest.main()
