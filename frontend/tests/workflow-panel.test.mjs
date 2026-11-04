/**
 * 前端单元测试：只测生产代码，不测测试文件里另抄一份的实现。
 *
 * 之前这个文件把 categoryLabel / statusLabel / LIU_CHONG / 吉凶打分
 * 全部在测试里重新写了一遍再断言，代码改坏了测试照样绿。
 * 现在直接 import src/lib/labels.js，测试失败才代表产品真的坏了。
 * 运行：node --test frontend/tests/workflow-panel.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";

import {
  CATEGORIES,
  BRANCH_CLASH,
  EARTHLY_BRANCHES,
  categoryLabel,
  daysToBranch,
  formatDate,
  normalizeCategory,
  statusLabel,
} from "../src/lib/labels.js";

test("分类清单覆盖 11 个事项类别且 id 不重复", () => {
  assert.equal(CATEGORIES.length, 11);
  const ids = CATEGORIES.map((item) => item.id);
  assert.equal(new Set(ids).size, 11);
});

test("categoryLabel 返回与后端一致的中文标签", () => {
  assert.equal(categoryLabel("career"), "事业");
  assert.equal(categoryLabel("finance"), "财运");
  assert.equal(categoryLabel("relationship"), "感情姻缘");
  assert.equal(categoryLabel("study"), "考试学业");
  assert.equal(categoryLabel("lawsuit"), "官司是非");
});

test("历史遗留分类键会被归一，不再原样透出", () => {
  assert.equal(normalizeCategory("wealth"), "finance");
  assert.equal(normalizeCategory("marriage"), "relationship");
  assert.equal(normalizeCategory("academics"), "study");
  assert.equal(normalizeCategory("unknown"), "other");
  assert.equal(normalizeCategory(""), "other");
  assert.equal(categoryLabel("wealth"), "财运");
});

test("statusLabel 覆盖全部会话状态", () => {
  assert.equal(statusLabel("draft"), "待排盘");
  assert.equal(statusLabel("casted"), "已排盘");
  assert.equal(statusLabel("interacting"), "交互中");
  assert.equal(statusLabel("reviewed"), "已复盘");
  assert.equal(statusLabel("weird"), "weird");
  assert.equal(statusLabel(undefined), "未知");
});

test("formatDate 处理有效日期与空值", () => {
  const rendered = formatDate("2026-08-26T10:00:00");
  assert.ok(rendered.includes("08") || rendered.includes("8月"));
  assert.equal(formatDate(""), "");
  assert.equal(formatDate(null), "");
  assert.equal(formatDate("not-a-date"), "not-a-date");
});

test("六冲表自反且 12 地支全覆盖", () => {
  assert.equal(Object.keys(BRANCH_CLASH).length, 12);
  assert.equal(EARTHLY_BRANCHES.length, 12);
  for (const branch of EARTHLY_BRANCHES) {
    assert.equal(BRANCH_CLASH[BRANCH_CLASH[branch]], branch);
  }
  assert.equal(BRANCH_CLASH["子"], "午");
  assert.equal(BRANCH_CLASH["卯"], "酉");
});

test("daysToBranch 计算地支间距", () => {
  assert.equal(daysToBranch("子", "午"), 6);
  assert.equal(daysToBranch("子", "丑"), 1);
  assert.equal(daysToBranch("亥", "子"), 1);
  assert.equal(daysToBranch("子", "子"), 0);
  assert.equal(daysToBranch("invalid", "子"), null);
  assert.equal(daysToBranch("子", "invalid"), null);
});
