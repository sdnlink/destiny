/**
 * 选项表与起盘输入的契约测试。
 *
 * 这些常量被组件直接引用，一旦被重构删掉，`npm run build` 依然会成功
 * （打包阶段不检查未定义标识符），只有真正点到对应界面才抛 ReferenceError。
 * 之前 WorkflowPanel 的 SYSTEMS / CASTING_METHODS / localDateTimeValue 就是这样丢的。
 */

import { test } from "node:test";
import assert from "node:assert/strict";

import { CASTING_METHODS, CATEGORIES, SYSTEMS } from "../src/lib/labels.js";
import { localDateTimeValue, newCastNonce } from "../src/lib/castingInput.js";

const BACKEND_SYSTEMS = ["auto", "meihua", "liuyao", "qimen", "daliuren", "bazi", "ziwei"];
const BACKEND_CASTING_METHODS = ["auto", "time", "numbers", "manual"];

test("术数门类选项覆盖后端全部 system 取值", () => {
  assert.deepEqual(
    SYSTEMS.map((item) => item.id),
    BACKEND_SYSTEMS,
  );
  for (const item of SYSTEMS) {
    assert.ok(item.label && item.label.length > 0, `${item.id} 缺少中文标签`);
  }
});

test("起盘方式选项覆盖后端全部 casting_method 取值", () => {
  assert.deepEqual(
    CASTING_METHODS.map((item) => item.id),
    BACKEND_CASTING_METHODS,
  );
});

test("事项分类仍是 11 项且 id 唯一", () => {
  assert.equal(CATEGORIES.length, 11);
  assert.equal(new Set(CATEGORIES.map((item) => item.id)).size, CATEGORIES.length);
});

test("localDateTimeValue 输出 datetime-local 需要的格式", () => {
  const value = localDateTimeValue(new Date("2026-11-04T10:31:00+08:00"));
  assert.match(value, /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/);
});

test("newCastNonce 满足后端 16–128 位 ASCII 字母数字约束", () => {
  for (let i = 0; i < 5; i += 1) {
    const nonce = newCastNonce();
    assert.match(nonce, /^[A-Za-z0-9_-]{16,128}$/, nonce);
  }
});
