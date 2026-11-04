/**
 * 工作流 step2 展示层压缩的回归测试。
 * 后端 compact_plate_output 只保留展示字段；前端 HexagramView / 历法基线
 * 依赖这些字段名，任何一端改名都会让盘面静默变成空白。
 */
import { test } from "node:test";
import assert from "node:assert/strict";

import { calendarGanzhiText, solarTermLabel, solarTermText } from "../src/lib/workflowDisplay.js";

test("古历法数据只剩 ganzhi 对象时也能渲染成字符串", () => {
  const calendar = {
    ganzhi: {
      year: { text: "丙午", stem: "丙", branch: "午" },
      month: { stem: "戊", branch: "戌" },
      day: "壬午",
      hour: { text: "乙巳" },
    },
  };
  const text = calendarGanzhiText(calendar);
  assert.ok(text.includes("丙午年"), text);
  assert.ok(text.includes("戊戌月"), text);
  assert.ok(text.includes("壬午日"), text);
  assert.ok(!text.includes("object"), "不能把干支对象直接插值成 [object Object]");
});

test("pillars 优先于 ganzhi", () => {
  const calendar = { pillars: { year: "丙午", month: "戊戌" }, ganzhi: { year: { text: "错误值" } } };
  const text = calendarGanzhiText(calendar);
  assert.ok(text.startsWith("丙午年 戊戌月"), text);
});

test("历法整段缺失时给出兜底文案", () => {
  assert.equal(calendarGanzhiText({}), "历法数据缺失");
  assert.equal(calendarGanzhiText(null), "历法数据缺失");
});

test("节气取 current.name，不把对象插值成 [object Object]", () => {
  const solarTerm = {
    previous: { name: "秋分" },
    current: { name: "寒露", datetime: "2026-10-08 09:00:00" },
    next: { name: "霜降" },
  };
  assert.equal(solarTermText(solarTerm), "寒露");
  assert.equal(solarTermText("霜降"), "霜降");
  assert.equal(solarTermText(undefined), "");
  assert.ok(!solarTermText(solarTerm).includes("object"));
});

test("非节气当天 current 为 null 时退回下一节气", () => {
  const solarTerm = {
    previous: { name: "霜降" },
    current: null,
    next: { name: "立冬", datetime: "2026-11-07 17:52:05" },
  };
  assert.equal(solarTermText(solarTerm), "立冬");
  assert.equal(solarTermLabel({ solar_term: solarTerm }), "立冬（下一节气）");
});

test("非节气当天标注「下一节气」，不让人误读成今天", () => {
  assert.equal(solarTermLabel({ solar_term: "立冬", solar_term_note: "下一节气" }), "立冬（下一节气）");
  assert.equal(solarTermLabel({ solar_term: "寒露", solar_term_note: "当前节气" }), "寒露");
  assert.equal(solarTermLabel({ solar_term: "" }), "");
});
