"""端到端集成冒烟测试：跨越中间件栈、会话归属隔离、计算端点与错误封套。

CI 无 ClickHouse，本测试仅走无需数据库的 HTTP 层（会话为文件存储、计算为纯函数），
用于捕获跨子系统的回归，而非替代单测。
"""
import unittest

from fastapi.testclient import TestClient

from app.main import app

OWNER_A = "integration-owner-a-" + "a" * 32
OWNER_B = "integration-owner-b-" + "b" * 32


class IntegrationSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def _headers(self, owner):
        return {"X-Client-Id": owner}

    def test_session_ownership_isolation_end_to_end(self):
        # 1) owner-A 创建会话
        create = self.client.post(
            "/v1/sessions",
            headers=self._headers(OWNER_A),
            json={"question": "今年事业如何", "category": "career", "system": "auto"},
        )
        self.assertEqual(create.status_code, 200)
        session_id = create.json()["data"]["session_id"]

        # 2) owner-A 能列出该会话
        listing = self.client.get("/v1/sessions", headers=self._headers(OWNER_A))
        self.assertEqual(listing.status_code, 200)
        ids = [row["session_id"] for row in listing.json()["data"]]
        self.assertIn(session_id, ids)

        # 3) owner-B 访问 owner-A 的会话被拒（跨越归属校验 + HTTPException 封套路径）
        forbidden = self.client.get(
            "/v1/sessions/{}".format(session_id), headers=self._headers(OWNER_B)
        )
        self.assertEqual(forbidden.status_code, 403)
        self.assertEqual(forbidden.json()["error"]["code"], "SESSION_FORBIDDEN")

        # 4) 不存在的会话返回 404 结构化错误（不泄漏 owner_hash）
        missing = self.client.get(
            "/v1/sessions/does-not-exist", headers=self._headers(OWNER_A)
        )
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"]["code"], "SESSION_NOT_FOUND")

    def test_calculation_endpoint_through_middleware_stack(self):
        # 计算端点走完整中间件（审计/错误封套/安全头），返回结构化 data
        resp = self.client.get(
            "/v1/fengshui/xuankong",
            params={"sitting_mountain": "午", "year": 2026},
            headers=self._headers(OWNER_A),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("data", resp.json())
        self.assertIn("facts", resp.json()["data"])
        # 安全响应头加固（部署层 TLS 之外的基础防护）
        self.assertEqual(resp.headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(resp.headers.get("X-Frame-Options"), "DENY")

    def test_missing_resource_uses_http_exception_envelope(self):
        # 不存在的房屋档案触发 HTTPException(404)，应被统一为 {error:{code, message}}
        resp = self.client.get(
            "/v1/fengshui/buildings/b-missing", params={"tenant_id": "t1"}
        )
        self.assertEqual(resp.status_code, 404)
        body = resp.json()
        self.assertEqual(body["error"]["code"], "HTTP_404")
        self.assertIn("message", body["error"])


if __name__ == "__main__":
    unittest.main()
