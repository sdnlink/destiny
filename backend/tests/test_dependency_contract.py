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

    def test_pydantic_is_on_v2(self):
        # 迁移记录见 docs/design/decisions/016-pydantic-v1-boundary.md
        self.assertEqual(pydantic.VERSION.split(".")[0], "2", pydantic.VERSION)

    def test_requirements_dev_pulls_runtime_requirements(self):
        text = (BACKEND_ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
        self.assertIn("-r requirements.txt", text)
        self.assertIn("httpx", text)

    def test_requirements_pins_pydantic_v2_range(self):
        text = (BACKEND_ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("pydantic>=2", text, "requirements.txt 必须把 pydantic 下界设在 2")
        self.assertIn("<3", text, "requirements.txt 必须把 pydantic 上界锁在 3 之前")

    def test_no_pydantic_v1_only_syntax_remains(self):
        # v1 专有写法在 v2 下不是报错而是语义变化（regex= / min_items= / @validator / .dict()），
        # 因此这里把「不许再出现」写成断言，防止回退。
        app_root = BACKEND_ROOT / "app"
        banned = {
            "regex=": "v1 的 constr(regex=) 在 v2 里必须写 pattern=",
            "min_items=": "v1 的 conlist(min_items=) 在 v2 里必须写 min_length=",
            "max_items=": "v1 的 conlist(max_items=) 在 v2 里必须写 max_length=",
            "@validator(": "v1 的 @validator 在 v2 里必须写 @field_validator",
            ".dict()": "v1 的 .dict() 在 v2 里必须写 .model_dump()",
        }
        offenders = []
        for path in sorted(app_root.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for token, reason in banned.items():
                if token in text:
                    offenders.append("{}: {}".format(path.relative_to(BACKEND_ROOT), reason))
        self.assertEqual(offenders, [], "\n".join(offenders))

    def test_starlette_version_matches_fastapi_pin(self):
        self.assertEqual(starlette.__version__, "0.27.0")


if __name__ == "__main__":
    unittest.main()
