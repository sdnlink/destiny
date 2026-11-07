// 客户端标识（审计 22）：后端会话归属靠这个 id 的哈希校验，所以它必须稳定且格式合法。
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { CLIENT_ID_STORAGE_KEY, getClientId, resetClientIdCache } from "../src/lib/clientIdentity.js";

describe("客户端标识", () => {
  it("同一进程内多次取值稳定，不每次换新 id", () => {
    resetClientIdCache();
    const first = getClientId();
    const second = getClientId();
    assert.equal(first, second);
  });

  it("生成的 id 满足后端 16–64 位 URL 安全字符约束", () => {
    resetClientIdCache();
    const id = getClientId();
    assert.match(id, /^[A-Za-z0-9_-]{16,64}$/);
  });

  it("把 id 写进约定的 localStorage 键，刷新后仍是同一个", () => {
    const store = new Map();
    globalThis.localStorage = {
      getItem: (key) => (store.has(key) ? store.get(key) : null),
      setItem: (key, value) => store.set(key, value),
    };
    resetClientIdCache();
    const id = getClientId();
    assert.equal(store.get(CLIENT_ID_STORAGE_KEY), id);
    // 模拟刷新：清内存缓存后重新读取
    resetClientIdCache();
    assert.equal(getClientId(), id);
    delete globalThis.localStorage;
  });

  it("localStorage 里是非法值时重新生成，不把坏值发给后端", () => {
    const store = new Map([[CLIENT_ID_STORAGE_KEY, "bad id!"]]);
    globalThis.localStorage = {
      getItem: (key) => (store.has(key) ? store.get(key) : null),
      setItem: (key, value) => store.set(key, value),
    };
    resetClientIdCache();
    const id = getClientId();
    assert.match(id, /^[A-Za-z0-9_-]{16,64}$/);
    assert.equal(store.get(CLIENT_ID_STORAGE_KEY), id);
    delete globalThis.localStorage;
  });
});
