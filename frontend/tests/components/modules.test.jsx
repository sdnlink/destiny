import { describe, expect, it } from "vitest";
import { ALL_MODULES, MODULE_GROUPS } from "../../src/lib/modules";

const EXPECTED_IDS = [
  "zhouyi", "meihua", "liuyao",
  "bazi", "ziwei",
  "qimen", "liuren",
  "fengshui",
  "workflow",
];

describe("功能模块表（路由单一事实来源）", () => {
  it("每个术数都独立成一级模块，id 与路由唯一且可分享", () => {
    expect(ALL_MODULES.map((module) => module.id)).toEqual(EXPECTED_IDS);
    expect(new Set(ALL_MODULES.map((module) => module.id)).size).toBe(ALL_MODULES.length);
    expect(new Set(ALL_MODULES.map((module) => module.to)).size).toBe(ALL_MODULES.length);
    for (const module of ALL_MODULES) {
      expect(module.to.startsWith("/")).toBe(true);
      expect(module.label).toBeTruthy();
      expect(module.desc).toBeTruthy();
    }
  });

  it("分组展平后与 ALL_MODULES 完全一致，不重复不遗漏", () => {
    expect(MODULE_GROUPS.flatMap((group) => group.modules)).toEqual(ALL_MODULES);
    expect(MODULE_GROUPS.map((group) => group.id)).toEqual([
      "divination", "destiny", "spacetime", "fengshui", "workflow",
    ]);
  });
});
