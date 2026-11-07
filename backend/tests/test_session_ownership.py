"""会话归属校验（审计 22）。

此前 `/v1/sessions/*` 只按 session_id 直取：任何能访问这套服务的客户端
都能读、排盘、交互、删除别人的会话。这组用例锁住现在的规则：

1. 没有 `X-Client-Id` 的会话请求一律 400，不是「默默放行」；
2. 会话创建时把客户端 id 的哈希写进 `owner_hash`，其他 id 读写一律 403；
3. 列表只返回自己的会话（以及迁移前没有 owner 的老会话），且不回传 owner_hash；
4. 迁移前的老会话由首个带合法 id 的访问者认领，之后他人 403。
"""

import unittest

from fastapi.testclient import TestClient
from app.main import app
from app.session import create_session, get_store

CLIENT_A = "a" * 32
CLIENT_B = "b" * 32
HEADERS_A = {"X-Client-Id": CLIENT_A}
HEADERS_B = {"X-Client-Id": CLIENT_B}

CASTING_SOURCE = {
    "local_datetime": "2026-08-15T16:00",
    "timezone": "Asia/Shanghai",
    "cast_nonce": "c" * 32,
}


class SessionOwnershipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def create(self, question, headers=HEADERS_A):
        response = self.client.post(
            "/v1/sessions",
            json={"question": question, "category": "career", "casting_method": "time", "casting_source": CASTING_SOURCE},
            headers=headers,
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["data"]["session_id"]

    def test_create_without_client_id_is_rejected(self):
        response = self.client.post("/v1/sessions", json={"question": "缺少客户端标识"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "CLIENT_ID_REQUIRED")

    def test_invalid_client_id_is_rejected(self):
        for bad in ("short", "x" * 32 + "!", "  ", "b" * 200):
            response = self.client.get("/v1/sessions", headers={"X-Client-Id": bad})
            self.assertEqual(response.status_code, 400, bad)

    def test_owner_can_read_and_other_client_cannot(self):
        session_id = self.create("归属校验-读取")
        own = self.client.get("/v1/sessions/{}".format(session_id), headers=HEADERS_A)
        self.assertEqual(own.status_code, 200)
        self.assertEqual(own.json()["data"]["question"], "归属校验-读取")
        self.assertNotIn("owner_hash", own.json()["data"], "归属哈希不应回传给客户端")
        foreign = self.client.get("/v1/sessions/{}".format(session_id), headers=HEADERS_B)
        self.assertEqual(foreign.status_code, 403)
        self.assertEqual(foreign.json()["error"]["code"], "SESSION_FORBIDDEN")

    def test_list_only_returns_own_sessions(self):
        mine = self.create("归属校验-我的会话", HEADERS_A)
        theirs = self.create("归属校验-别人的会话", HEADERS_B)
        rows_a = self.client.get("/v1/sessions?limit=200", headers=HEADERS_A).json()["data"]
        ids_a = {row["session_id"] for row in rows_a}
        self.assertIn(mine, ids_a)
        self.assertNotIn(theirs, ids_a)
        for row in rows_a:
            self.assertNotIn("owner_hash", row)

        rows_b = self.client.get("/v1/sessions?limit=200", headers=HEADERS_B).json()["data"]
        ids_b = {row["session_id"] for row in rows_b}
        self.assertIn(theirs, ids_b)
        self.assertNotIn(mine, ids_b)

    def test_cross_owner_delete_is_blocked(self):
        session_id = self.create("归属校验-删除")
        blocked = self.client.delete("/v1/sessions/{}".format(session_id), headers=HEADERS_B)
        self.assertEqual(blocked.status_code, 403)
        still_there = self.client.get("/v1/sessions/{}".format(session_id), headers=HEADERS_A)
        self.assertEqual(still_there.status_code, 200)
        allowed = self.client.delete("/v1/sessions/{}".format(session_id), headers=HEADERS_A)
        self.assertEqual(allowed.status_code, 200)
        self.assertTrue(allowed.json()["data"]["deleted"])

    def test_cross_owner_cast_is_blocked(self):
        session_id = self.create("归属校验-排盘")
        blocked = self.client.post("/v1/sessions/{}/cast".format(session_id), json={}, headers=HEADERS_B)
        self.assertEqual(blocked.status_code, 403)
        # 被拒绝的排盘不应产生冻结快照
        detail = self.client.get("/v1/sessions/{}".format(session_id), headers=HEADERS_A).json()["data"]
        self.assertEqual(detail["status"], "draft")
        self.assertIsNone(detail["snapshot"])

    def test_cross_owner_interact_is_blocked(self):
        session_id = self.create("归属校验-交互")
        casted = self.client.post("/v1/sessions/{}/cast".format(session_id), json={}, headers=HEADERS_A)
        self.assertEqual(casted.status_code, 200, casted.text)
        blocked = self.client.post(
            "/v1/sessions/{}/interact".format(session_id),
            json={"interaction_type": "reality_check", "payload": {"response": "符合"}},
            headers=HEADERS_B,
        )
        self.assertEqual(blocked.status_code, 403)
        detail = self.client.get("/v1/sessions/{}".format(session_id), headers=HEADERS_A).json()["data"]
        self.assertEqual(detail["interactions"], [], "被拒绝的交互不应写进会话")

    def test_legacy_session_is_claimed_by_first_client(self):
        legacy = create_session(question="归属校验-老会话")
        store = get_store()
        store.save(legacy)
        self.assertEqual(legacy.owner_hash, "")

        first = self.client.get("/v1/sessions/{}".format(legacy.session_id), headers=HEADERS_A)
        self.assertEqual(first.status_code, 200)
        reloaded = store.load(legacy.session_id)
        self.assertTrue(reloaded.owner_hash, "认领后应把 owner_hash 落盘")

        second = self.client.get("/v1/sessions/{}".format(legacy.session_id), headers=HEADERS_B)
        self.assertEqual(second.status_code, 403)
        store.delete(legacy.session_id)

    def test_legacy_session_still_appears_in_list(self):
        legacy = create_session(question="归属校验-老会话列表可见")
        get_store().save(legacy)
        rows = self.client.get("/v1/sessions?limit=200", headers=HEADERS_A).json()["data"]
        self.assertIn(legacy.session_id, {row["session_id"] for row in rows})
        get_store().delete(legacy.session_id)


if __name__ == "__main__":
    unittest.main()
