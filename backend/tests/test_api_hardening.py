"""API 加固回归：错误封套统一、速率限制、玄空替卦参考（draft）。"""
import unittest

from fastapi.testclient import TestClient

from app import main as main_module
from app.main import app


class ApiHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_http_exception_uses_error_envelope(self):
        # 不存在的房屋档案触发 HTTPException(404)，应被统一为 {error:{code, message}}
        resp = self.client.get("/v1/fengshui/buildings/b-missing-x", params={"tenant_id": "t1"})
        self.assertEqual(resp.status_code, 404)
        body = resp.json()
        self.assertIn("error", body)
        self.assertEqual(body["error"]["code"], "HTTP_404")
        self.assertIn("message", body["error"])

    def test_xuankong_tihua_reference_off_by_default(self):
        resp = self.client.get(
            "/v1/fengshui/xuankong", params={"sitting_mountain": "午", "year": 2026}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()["data"]
        self.assertNotIn("tihua_reference", data["facts"])

    def test_xuankong_tihua_reference_on_when_requested(self):
        resp = self.client.get(
            "/v1/fengshui/xuankong",
            params={"sitting_mountain": "午", "year": 2026, "include_tihua_reference": "true"},
        )
        self.assertEqual(resp.status_code, 200)
        ref = resp.json()["data"]["facts"]["tihua_reference"]
        self.assertEqual(ref["rule_id"], "FS-XUANKONG-TIHUA-001")
        self.assertEqual(ref["status"], "resolved_by_library_classics")
        self.assertIs(ref["signed"], False)
        self.assertEqual(ref["signature_status"], "unsigned")
        self.assertIs(ref["requires_expert_signoff"], True)
        self.assertEqual(ref["sitting"]["mountain"], "午")
        self.assertIsNotNone(ref["sitting"]["tihua_star"])

    def test_xuankong_degree_range_consistent_for_get_and_post(self):
        for degree in (-1, 361):
            get_resp = self.client.get(
                "/v1/fengshui/xuankong",
                params={"sitting_mountain": "午", "sitting_degree": degree},
            )
            self.assertEqual(get_resp.status_code, 422)
            post_resp = self.client.post(
                "/v1/fengshui/xuankong",
                json={"sitting_mountain": "午", "sitting_degree": degree},
            )
            self.assertEqual(post_resp.status_code, 422)

    def test_unsupported_system_is_rejected_at_create(self):
        # zhouyi/fengshui 不在七步排盘链路里，不能静默落成「梅花+六爻」默认盘
        resp = self.client.post(
            "/v1/sessions",
            json={"question": "未知体系校验", "system": "zhouyi"},
            headers={"X-Client-Id": "unsupported-system-" + "a" * 32},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "INVALID_SYSTEM")


class RateLimitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_rate_limit_returns_429(self):
        original = main_module.RATE_LIMIT_PER_MINUTE
        main_module.RATE_LIMIT_PER_MINUTE = 2  # 仅本测试临时启用
        try:
            headers = {"X-Client-Id": "ratelimit-probe-" + "a" * 32}
            codes = []
            for _ in range(5):
                resp = self.client.post(
                    "/v1/fengshui/xuankong",
                    json={"sitting_mountain": "午", "year": 2026},
                    headers=headers,
                )
                codes.append(resp.status_code)
            self.assertIn(429, codes)
        finally:
            main_module.RATE_LIMIT_PER_MINUTE = original


if __name__ == "__main__":
    unittest.main()
