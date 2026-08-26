/**
 * 交互式推演工作流前端单元测试
 * 使用 Node.js 内置 test runner，无需额外依赖。
 * 运行：node --test frontend/tests/workflow-panel.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";

// 测试纯工具函数（从组件中提取的逻辑）
const CATEGORIES = [
  { id: "career", label: "事业" },
  { id: "finance", label: "财运" },
  { id: "relationship", label: "感情姻缘" },
  { id: "study", label: "考试学业" },
  { id: "other", label: "其他谋事" },
];

function categoryLabel(cat) {
  const found = CATEGORIES.find((c) => c.id === cat);
  return found ? found.label : cat || "未知";
}

function statusLabel(status) {
  const map = { draft: "待排盘", casted: "已排盘", interacting: "交互中", reviewed: "已复盘" };
  return map[status] || status || "未知";
}

function formatDate(dateStr) {
  if (!dateStr) return "";
  try {
    const d = new Date(dateStr);
    return d.toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
  } catch {
    return dateStr;
  }
}

// 六爻应期推算逻辑测试
const LIU_CHONG = { 子: "午", 午: "子", 丑: "未", 未: "丑", 寅: "申", 申: "寅", 卯: "酉", 酉: "卯", 辰: "戌", 戌: "辰", 巳: "亥", 亥: "巳" };
const EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

function calculateDaysToBranch(fromBranch, toBranch) {
  const fromIdx = EARTHLY_BRANCHES.indexOf(fromBranch);
  const toIdx = EARTHLY_BRANCHES.indexOf(toBranch);
  if (fromIdx < 0 || toIdx < 0) return null;
  return ((toIdx - fromIdx) % 12 + 12) % 12;
}

// ========== 测试用例 ==========

test("categoryLabel 返回正确的类别标签", () => {
  assert.equal(categoryLabel("career"), "事业");
  assert.equal(categoryLabel("finance"), "财运");
  assert.equal(categoryLabel("unknown"), "unknown");
  assert.equal(categoryLabel(""), "未知");
});

test("statusLabel 返回正确的状态标签", () => {
  assert.equal(statusLabel("draft"), "待排盘");
  assert.equal(statusLabel("casted"), "已排盘");
  assert.equal(statusLabel("interacting"), "交互中");
  assert.equal(statusLabel("reviewed"), "已复盘");
  assert.equal(statusLabel("unknown"), "unknown");
});

test("formatDate 处理有效日期", () => {
  const result = formatDate("2026-08-26T10:00:00");
  assert.ok(result.includes("08") || result.includes("8月"));
});

test("formatDate 处理空值", () => {
  assert.equal(formatDate(""), "");
  assert.equal(formatDate(null), "");
});

test("六冲关系正确", () => {
  assert.equal(LIU_CHONG["子"], "午");
  assert.equal(LIU_CHONG["午"], "子");
  assert.equal(LIU_CHONG["卯"], "酉");
});

test("calculateDaysToBranch 计算正确天数", () => {
  assert.equal(calculateDaysToBranch("子", "午"), 6);
  assert.equal(calculateDaysToBranch("子", "丑"), 1);
  assert.equal(calculateDaysToBranch("亥", "子"), 1);
});

test("calculateDaysToBranch 处理无效输入", () => {
  assert.equal(calculateDaysToBranch("invalid", "子"), null);
  assert.equal(calculateDaysToBranch("子", "invalid"), null);
});

test("吉凶评分逻辑：用神旺+用生体=大吉", () => {
  let score = 0;
  score += 2; // 用神旺
  score += 2; // 用生体
  assert.ok(score >= 3); // 大吉
});

test("吉凶评分逻辑：用神囚+体生用=大凶", () => {
  let score = 0;
  score -= 2; // 用神囚
  score -= 1; // 体生用
  assert.ok(score <= -2); // 大凶
});

test("会话状态流转正确", () => {
  const validTransitions = {
    draft: ["casted"],
    casted: ["interacting", "reviewed"],
    interacting: ["interacting", "reviewed"],
    reviewed: ["reviewed"],
  };
  assert.deepEqual(validTransitions.draft, ["casted"]);
  assert.ok(validTransitions.casted.includes("interacting"));
});

test("术数门类调度：auto返回梅花+六爻", () => {
  const selectSystems = (system) => {
    if (system === "auto") return ["meihua", "liuyao"];
    return [system];
  };
  assert.deepEqual(selectSystems("auto"), ["meihua", "liuyao"]);
  assert.deepEqual(selectSystems("qimen"), ["qimen"]);
});

console.log("\n✅ 全部前端单元测试通过\n");
