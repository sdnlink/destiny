import { describe, expect, it } from "vitest";
import {
  ALL_MODULES,
  MODULE_BY_PATH,
  MODULE_GROUPS,
  RECENT_MODULES_KEY,
  pageTitleForPath,
  pushRecentModule,
  readRecentModules,
} from "../../src/lib/modules";

const EXPECTED_IDS = [
  "zhouyi", "meihua", "liuyao",
  "bazi", "ziwei",
  "qimen", "liuren",
  "fengshui",
  "workflow",
];

function memoryStorage(initial = {}) {
  const store = { ...initial };
  return {
    getItem: (key) => (key in store ? store[key] : null),
    setItem: (key, value) => { store[key] = String(value); },
  };
}

describe("功能模块表（路由单一事实来源）", () => {
  it("每个术数都独立成一级模块，id 与路由唯一且可分享", () => {
    expect(ALL_MODULES.map((module) => module.id)).toEqual(EXPECTED_IDS);
    expect(new Set(ALL_MODULES.map((module) => module.id)).size).toBe(ALL_MODULES.length);
    expect(new Set(ALL_MODULES.map((module) => module.to)).size).toBe(ALL_MODULES.length);
    for (const module of ALL_MODULES) {
      expect(module.to.startsWith("/")).toBe(true);
      expect(module.label).toBeTruthy();
      expect(module.desc).toBeTruthy();
      expect(MODULE_BY_PATH[module.to]).toBe(module);
    }
  });

  it("分组展平后与 ALL_MODULES 完全一致，不重复不遗漏", () => {
    expect(MODULE_GROUPS.flatMap((group) => group.modules)).toEqual(ALL_MODULES);
    expect(MODULE_GROUPS.map((group) => group.id)).toEqual([
      "divination", "destiny", "spacetime", "fengshui", "workflow",
    ]);
  });

  it("浏览器标签标题随路由命名，未知路径标注未找到", () => {
    expect(pageTitleForPath("/")).toBe("天机演象 · 推演工作台");
    expect(pageTitleForPath("/liuyao")).toBe("六爻 · 天机演象");
    expect(pageTitleForPath("/ziwei")).toBe("紫微斗数 · 天机演象");
    expect(pageTitleForPath("/no-such-page")).toBe("页面未找到 · 天机演象");
  });
});

describe("最近使用模块", () => {
  it("置顶去重、最多 4 个，不记录未知路径", () => {
    const storage = memoryStorage();
    expect(pushRecentModule("/zhouyi", storage)).toEqual(["/zhouyi"]);
    expect(pushRecentModule("/bazi", storage)).toEqual(["/bazi", "/zhouyi"]);
    expect(pushRecentModule("/zhouyi", storage)).toEqual(["/zhouyi", "/bazi"]);
    pushRecentModule("/qimen", storage);
    pushRecentModule("/liuren", storage);
    expect(pushRecentModule("/ziwei", storage)).toEqual(["/ziwei", "/liuren", "/qimen", "/zhouyi"]);
    // 未知路径不写入
    expect(pushRecentModule("/unknown", storage)).toEqual(["/ziwei", "/liuren", "/qimen", "/zhouyi"]);
  });

  it("读取时过滤失效路径，坏数据不抛错", () => {
    expect(readRecentModules(memoryStorage())).toEqual([]);
    expect(readRecentModules(memoryStorage({ [RECENT_MODULES_KEY]: "not-json" }))).toEqual([]);
    expect(readRecentModules(memoryStorage({
      [RECENT_MODULES_KEY]: JSON.stringify(["/ziwei", "/retired-page", "/bazi"]),
    }))).toEqual(["/ziwei", "/bazi"]);
  });
});
