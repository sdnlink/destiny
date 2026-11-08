/**
 * 表单 → 计算请求映射的单元测试（测真实模块 src/lib/calculationPlan.js）。
 * 运行：node --test frontend/tests/calculation-plan.test.mjs
 */
import { test } from "node:test";
import assert from "node:assert/strict";

import { buildCalculations, calendarPayload } from "../src/lib/calculationPlan.js";

function baseForm(overrides = {}) {
  return {
    scene: "combined",
    localDatetime: "2026-11-04T10:31",
    timezone: "Asia/Shanghai",
    trueSolar: false,
    longitude: "",
    castNonce: "test-nonce-0123456789",
    yiMethod: "auto",
    lines: [7, 8, 7, 8, 7, 8],
    yiLower: "8",
    yiUpper: "8",
    yiNumbers: ["1", "2", "3"],
    meihuaMethod: "auto",
    mhUpper: "8",
    mhLower: "8",
    mhNumbers: ["1", "2", "3"],
    liuyaoMethod: "auto",
    lyLower: "8",
    lyUpper: "8",
    lyLines: [7, 8, 7, 8, 7, 8],
    lyCoins: [[2, 2, 3], [2, 3, 3], [3, 2, 2], [2, 2, 2], [3, 3, 2], [2, 3, 2]],
    liurenMethod: "auto",
    lrNumber: "8",
    qimenMethod: "time",
    baziMethod: "time",
    baziGender: "男",
    ziweiMethod: "time",
    ziweiGender: "男",
    fsFacing: "180",
    fsMode: "single",
    fsMeasurements: ["179", "180", "181"],
    fsReference: "magnetic",
    fsDeclination: "0",
    fsError: "1",
    ...overrides,
  };
}

test("calendarPayload 不带经度时不输出该项", () => {
  assert.deepEqual(calendarPayload(baseForm()), {
    local_datetime: "2026-11-04T10:31",
    timezone: "Asia/Shanghai",
    use_true_solar_time: false,
  });
});

test("启用真太阳时后才输出数值型经度", () => {
  const payload = calendarPayload(baseForm({ trueSolar: true, longitude: "116.4074" }));
  assert.equal(payload.use_true_solar_time, true);
  assert.equal(payload.longitude, 116.4074);
});

test("综合推演固定先出历法，再覆盖八类体系", () => {
  const calculations = buildCalculations(baseForm());
  assert.equal(calculations[0].module, "calendar");
  assert.equal(calculations[0].method, "analyze");
  const modules = calculations.map((item) => item.module);
  for (const module of ["zhouyi", "meihua", "liuyao", "liuren", "qimen", "bazi", "ziwei"]) {
    assert.ok(modules.includes(module), module);
  }
  assert.equal(calculations.length, 8);
});

test("单一体系场景只产出历法 + 该体系", () => {
  const calculations = buildCalculations(baseForm({ scene: "liuyao" }));
  assert.equal(calculations.length, 2);
  assert.equal(calculations[1].module, "liuyao");
});

test("报数起卦会把历法参数与两个数字一起带上", () => {
  const calculations = buildCalculations(
    baseForm({ scene: "liuyao", liuyaoMethod: "numbers", lyLower: "3", lyUpper: "5" }),
  );
  const request = calculations[1];
  assert.equal(request.method, "numbers");
  assert.equal(request.input.lower_number, 3);
  assert.equal(request.input.upper_number, 5);
  assert.equal(request.input.timezone, "Asia/Shanghai");
});

test("手工起卦只传六爻爻值，不夹带历法参数", () => {
  const calculations = buildCalculations(baseForm({ scene: "zhouyi", yiMethod: "manual" }));
  const request = calculations[1];
  assert.equal(request.method, "manual");
  assert.deepEqual(request.input, { lines: [7, 8, 7, 8, 7, 8] });
});

test("周易三数起卦传三个整数", () => {
  const request = buildCalculations(
    baseForm({ scene: "zhouyi", yiMethod: "three_numbers", yiNumbers: ["4", "5", "6"] }),
  )[1];
  assert.equal(request.method, "three_numbers");
  assert.deepEqual(request.input, { numbers: [4, 5, 6] });
});

test("梅花三数起卦传三个整数", () => {
  const request = buildCalculations(
    baseForm({ scene: "meihua", meihuaMethod: "three_numbers", mhNumbers: ["1", "7", "9"] }),
  )[1];
  assert.equal(request.method, "three_numbers");
  assert.deepEqual(request.input, { numbers: [1, 7, 9] });
});

test("六爻手工爻与铜钱分别映射 lines 与 coins，并带历法参数", () => {
  const lines = buildCalculations(
    baseForm({ scene: "liuyao", liuyaoMethod: "lines", lyLines: [6, 7, 8, 9, 7, 8] }),
  )[1];
  assert.equal(lines.method, "lines");
  assert.deepEqual(lines.input.lines, [6, 7, 8, 9, 7, 8]);
  assert.equal(lines.input.timezone, "Asia/Shanghai");

  const coins = buildCalculations(
    baseForm({ scene: "liuyao", liuyaoMethod: "coins" }),
  )[1];
  assert.equal(coins.method, "coins");
  assert.deepEqual(coins.input.coins, [[2, 2, 3], [2, 3, 3], [3, 2, 2], [2, 2, 2], [3, 3, 2], [2, 3, 2]]);
});

test("八字自动起盘需要 gender 与 cast_nonce", () => {
  const calculations = buildCalculations(
    baseForm({ scene: "bazi", baziMethod: "auto", baziGender: "女" }),
  );
  const request = calculations[1];
  assert.equal(request.method, "auto");
  assert.equal(request.input.gender, "女");
  assert.equal(request.input.cast_nonce, "test-nonce-0123456789");
});

test("风水单选与多次测量走不同 method 与入参结构", () => {
  const single = buildCalculations(baseForm({ scene: "fengshui" }))[1];
  assert.equal(single.method, "direction");
  assert.equal(single.input.facing_degree, 180);
  assert.equal(single.input.measurement_method, "web_manual_entry");

  const multiple = buildCalculations(baseForm({ scene: "fengshui", fsMode: "multiple" }))[1];
  assert.equal(multiple.method, "measurements");
  assert.equal(multiple.input.measurements.length, 3);
  assert.equal(multiple.input.measurements[0].measurement_method, "web_multi_entry");
});
