"""APP_API_TOKEN 中间件行为回归测试。

背景：SERVE_WEB=1 时根路径挂载浏览器静态资源，浏览器无法携带 Bearer 头。
中间件改为只保护 /v1、/docs、/openapi.json、/redoc；/health 探活与静态页面保持公开。
此文件钉住该边界，避免再次退化为「设置 Token 后整站 401」或「API 裸奔」。
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.main import app


class TokenMiddlewareTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_api_requires_token_when_configured(self):
        with mock.patch("app.main.API_TOKEN", "secret-token"):
            response = self.client.get("/v1/rules")
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json()["error"]["code"], "UNAUTHORIZED")

            wrong = self.client.get("/v1/rules", headers={"Authorization": "Bearer wrong"})
            self.assertEqual(wrong.status_code, 401)

            ok = self.client.get("/v1/rules", headers={"Authorization": "Bearer secret-token"})
            self.assertEqual(ok.status_code, 200)

    def test_docs_and_openapi_require_token_when_configured(self):
        with mock.patch("app.main.API_TOKEN", "secret-token"):
            for path in ("/docs", "/openapi.json"):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 401, path)

    def test_health_stays_public_with_token(self):
        with mock.patch("app.main.API_TOKEN", "secret-token"):
            response = self.client.get("/health")
            self.assertEqual(response.status_code, 200)
            self.assertIn("ziwei", response.json()["modules"])
            self.assertIn("bazi", response.json()["modules"])
            self.assertIn("qimen", response.json()["modules"])

    def test_non_api_paths_are_not_blocked_by_token(self):
        # SERVE_WEB 未开启时 "/" 由 StaticFiles 兜底为 404，
        # 但绝不能是 401——保证开启 SERVE_WEB 后静态资源仍可被浏览器加载。
        with mock.patch("app.main.API_TOKEN", "secret-token"):
            response = self.client.get("/")
            self.assertNotEqual(response.status_code, 401)

    def test_api_open_when_token_not_configured(self):
        with mock.patch("app.main.API_TOKEN", None):
            response = self.client.get("/v1/rules")
            self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
