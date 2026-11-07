"""入参校验契约测试（pydantic v1 → v2 迁移后的守卫）。

v2 改变了校验失败的文案与 type 码，但**对外的响应结构**必须保持：
HTTP 422 + `detail` 数组，每项至少有 `loc` / `msg` / `type`，且 `loc` 的层级路径不变。
前端 `frontend/src/lib/api.js` 读的是 `detail[0].msg`，所以这条结构不能变。
"""

import unittest

from fastapi.testclient import TestClient

from app.main import app


class ValidationErrorContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def assert_error_detail(self, response, expected_loc):
        self.assertEqual(response.status_code, 422)
        detail = response.json()["detail"]
        self.assertIsInstance(detail, list)
        self.assertTrue(detail)
        first = detail[0]
        for key in ("loc", "msg", "type"):
            self.assertIn(key, first, "校验错误项缺少 {}：{}".format(key, first))
        self.assertEqual(first["loc"], expected_loc)
        self.assertIsInstance(first["msg"], str)
        self.assertTrue(first["msg"])

    def test_out_of_range_line_points_at_index(self):
        response = self.client.post("/v1/zhouyi/manual", json={"lines": [5, 6, 7, 8, 9, 10]})
        self.assert_error_detail(response, ["body", "lines", 0])

    def test_short_line_list_points_at_field(self):
        response = self.client.post("/v1/zhouyi/manual", json={"lines": [6, 7, 8]})
        self.assert_error_detail(response, ["body", "lines"])

    def test_cast_nonce_too_short(self):
        response = self.client.post(
            "/v1/zhouyi/auto",
            json={
                "local_datetime": "2026-08-15T16:00:00",
                "timezone": "Asia/Shanghai",
                "cast_nonce": "short",
            },
        )
        self.assert_error_detail(response, ["body", "cast_nonce"])

    def test_custom_validator_still_rejects_bool(self):
        response = self.client.post("/v1/fengshui/direction", json={"facing_degree": True})
        self.assert_error_detail(response, ["body", "facing_degree"])

    def test_nested_context_error_keeps_path(self):
        response = self.client.post(
            "/v1/calculations/compare",
            json={
                "calculations": [{"module": "zhouyi", "method": "auto", "input": {}}],
                "context": {"category": "unknown-category", "question_summary": "x"},
            },
        )
        self.assert_error_detail(response, ["body", "context", "category"])

    def test_missing_required_field(self):
        response = self.client.post("/v1/sessions", json={})
        self.assert_error_detail(response, ["body", "question"])

    def test_valid_payload_still_succeeds(self):
        response = self.client.post("/v1/zhouyi/manual", json={"lines": [6, 7, 6, 9, 8, 7]})
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.json())


if __name__ == "__main__":
    unittest.main()
