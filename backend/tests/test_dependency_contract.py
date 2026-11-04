"""依赖契约测试。

干净机器上跑 `scripts/build_all.sh` 曾因为缺 httpx 直接失败（FastAPI TestClient 依赖它），
也曾因为 httpx 0.28 与 starlette 0.27 不兼容而 13 个用例全红却看不出原因。
这里把「测试基线必须满足的依赖事实」写成断言，环境漂移时先在 CI 报错，
而不是让使用者自己猜。
"""

import unittest
from pathlib import Path

import httpx
import pydantic
import starlette


BACKEND_ROOT = Path(__file__).resolve().parents[1]


class DependencyContractTests(unittest.TestCase):
    def test_httpx_is_below_028(self):
        # starlette 0.27 的 TestClient 用了 httpx 0.28 已移除的 app= 简写
        version = tuple(int(part) for part in httpx.__version__.split(".")[:2])
        self.assertLess(version, (0, 28), "httpx {} 与 starlette 不兼容".format(httpx.__version__))

    def test_pydantic_stays_on_v1_until_migration(self):
        # 迁移计划见 docs/design/decisions/016-pydantic-v1-boundary.md
        self.assertEqual(pydantic.VERSION.split(".")[0], "1", pydantic.VERSION)

    def test_requirements_dev_pulls_runtime_requirements(self):
        text = (BACKEND_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        self.assertIn("-r requirements.txt", text)
        self.assertIn("httpx", text)

    def test_requirements_pins_pydantic_upper_bound(self):
        text = (BACKEND_ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("<2", text, "requirements.txt 必须把 pydantic 上界锁在 2 之前")

    def test_starlette_version_matches_fastapi_pin(self):
        self.assertEqual(starlette.__version__, "0.27.0")


if __name__ == "__main__":
    unittest.main()
