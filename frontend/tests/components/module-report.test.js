import { describe, expect, it } from "vitest";
import { generateStandaloneReport } from "../../src/lib/moduleReport";

describe("standalone report", () => {
  it("renders 八宅 facts and boundary", () => {
    const markdown = generateStandaloneReport({
      facts: {
        sitting_mountain: "子",
        sitting_trigram: "坎",
        house_group: "东四宅",
        lucky_directions: ["坎", "震"],
        unlucky_directions: ["艮"],
        life_match: { life_trigram: "兑", life_group: "西四命", group_match: false, note: "宅命异组" },
        directions: [{ direction: "北", palace: "坎", star: "伏位", star_animal: "辅弼", element: "木", nature: "吉" }],
        song: "乾六天五祸绝延生",
      },
      warnings: ["不含流年断语。"],
    }, { module: "fengshui-bazhai", title: "阳宅风水 · 八宅" });

    expect(markdown).toContain("# 阳宅风水 · 八宅");
    expect(markdown).toContain("坎 · 东四宅");
    expect(markdown).toContain("宅命异组");
    expect(markdown).toContain("伏位");
    expect(markdown).toContain("不含流年断语。");
  });

  it("renders 玄空 grid and 替卦 reference", () => {
    const markdown = generateStandaloneReport({
      facts: {
        sitting_mountain: "子",
        facing_mountain: "午",
        period: 9,
        period_label: "下元9运",
        fly_direction: { sitting: "逆飞", facing: "逆飞" },
        grid: [{ palace: "坎", period_star: 5, mountain_star: 9, facing_star: 8 }],
        conditions: [{ name: "旺山旺向", met: true }],
        tihua_reference: { sitting: { mountain: "子", tihua_star: 1 }, facing: { mountain: "午", tihua_star: 9 }, note: "工程基线" },
      },
    }, { module: "fengshui-xuankong", title: "阳宅风水 · 玄空" });

    expect(markdown).toContain("| 坎 | 5 | 9 | 8 |");
    expect(markdown).toContain("旺山旺向");
    expect(markdown).toContain("子 → 1 入中");
    expect(markdown).toContain("午 → 9 入中");
    expect(markdown).toContain("工程基线");
  });

  it("renders 紫微 palaces and 大限", () => {
    const markdown = generateStandaloneReport({
      facts: {
        bureau: { name: "水二局", nayin: "水" },
        yin_yang_gender: "阳男",
        is_forward_decade: true,
        ming_zhu: "贪狼",
        shen_zhu: "天相",
        si_hua: { 禄: "廉贞" },
        palaces_by_branch: [
          { name: "命宫", palace_stem_branch: "丙子", main_stars: [{ name: "天机" }], si_hua: [], major_limit_start: 2, major_limit_end: 11 },
        ],
      },
      warnings: ["大限为宫位区间事实。"],
    }, { module: "ziwei", title: "命运专项 · 紫微斗数" });

    expect(markdown).toContain("## 十二宫");
    expect(markdown).toContain("| 命宫 | 丙子 | 天机 | — | 2–11 |");
    expect(markdown).toContain("大限为宫位区间事实。");
  });

  it("renders 流年 table", () => {
    const markdown = generateStandaloneReport({
      birth_year: 1984,
      start_year: 2026,
      count: 1,
      day_master: "甲",
      years: [{
        year: 2026,
        ganzhi: "丙午",
        stem_ten_god: "食神",
        nayin: "天河水",
        age: 42,
        luck_pillar: { ganzhi: "庚午", start_year: 2022, end_year: 2031 },
        branch_relations: [{ type: "六冲", with: "年柱" }],
      }],
    }, { module: "liunian", title: "命运专项 · 流年" });

    expect(markdown).toContain("| 2026 | 丙午 | 食神 | 天河水 | 42 | 庚午（2022–2031） | 六冲年柱 |");
  });
});
