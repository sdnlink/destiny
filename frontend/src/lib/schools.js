/**
 * 术数流派归并口径。
 *
 * 同一流派的功能放在同一菜单组里；「综合」只做跨流派对照，不是独立流派。
 * 这里是前端唯一一份流派归并表，InputPanel 从这里取分组与标签。
 */
export const SCHOOLS = [
  {
    id: "combined",
    label: "综合",
    description: "跨流派对照",
    systems: ["combined"],
  },
  {
    id: "yizhan",
    label: "易占",
    description: "周易 · 梅花 · 六爻",
    systems: ["zhouyi", "meihua", "liuyao"],
  },
  {
    id: "mingli",
    label: "命理",
    description: "八字 · 紫微",
    systems: ["bazi", "ziwei"],
  },
  {
    id: "sanshi",
    label: "三式",
    description: "奇门 · 大六壬",
    systems: ["qimen", "liuren"],
  },
  {
    id: "kanyu",
    label: "堪舆",
    description: "阳宅风水",
    systems: ["fengshui"],
  },
];

export function schoolForSystem(system) {
  return SCHOOLS.find((school) => school.systems.includes(system)) || SCHOOLS[0];
}
