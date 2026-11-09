/**
 * 功能模块单一事实来源：每个术数独立成一级路由页面。
 * 导航栏与首页引导卡片都从这里读取，避免两处各写一份。
 * 图标因是 React 组件，放在消费侧（App 导航 / 首页卡片）映射，这里只放纯数据。
 */
export const MODULE_GROUPS = [
  {
    id: "divination",
    label: "卜筮",
    modules: [
      { id: "zhouyi", label: "周易", to: "/zhouyi", desc: "以所问事项与时间为基准起卦，查看本卦、变卦、互卦、错卦与综卦。" },
      { id: "meihua", label: "梅花易数", to: "/meihua", desc: "时间或数字取数，查看上下卦、动爻与体用五行生克。" },
      { id: "liuyao", label: "六爻", to: "/liuyao", desc: "京房纳甲装卦，查看八宫、世应、六亲、六神与旬空。" },
    ],
  },
  {
    id: "destiny",
    label: "命理",
    modules: [
      { id: "bazi", label: "八字命理", to: "/bazi", desc: "四柱、藏干十神、大运与流年、生平时间轴。" },
      { id: "ziwei", label: "紫微斗数", to: "/ziwei", desc: "十二宫、星曜、四化与命身主星。" },
    ],
  },
  {
    id: "spacetime",
    label: "时空",
    modules: [
      { id: "qimen", label: "奇门遁甲", to: "/qimen", desc: "时家转盘奇门，阴阳遁局、九宫、八门、九星与八神。" },
      { id: "liuren", label: "大六壬", to: "/liuren", desc: "月将、天地盘、四课、三传与十二天将。" },
    ],
  },
  {
    id: "fengshui",
    label: "堪舆",
    modules: [
      { id: "fengshui", label: "阳宅风水", to: "/fengshui", desc: "坐向、二十四山、八宅、玄空与房屋档案。" },
    ],
  },
  {
    id: "workflow",
    label: "通用",
    modules: [
      { id: "workflow", label: "交互推演", to: "/workflow", desc: "七步标准化交互式推演工作流。" },
    ],
  },
];

export const ALL_MODULES = MODULE_GROUPS.flatMap((group) => group.modules);

export const MODULE_BY_PATH = Object.fromEntries(
  ALL_MODULES.map((module) => [module.to, module])
);

/** 浏览器标签标题随路由同步，便于多页面间辨识与分享。 */
export function pageTitleForPath(path) {
  if (!path || path === "/") return "天机演象 · 推演工作台";
  const module = MODULE_BY_PATH[path];
  return module ? `${module.label} · 天机演象` : "页面未找到 · 天机演象";
}

// 首页「最近使用」：只记路径，重排去重，最多保留 4 个。
export const RECENT_MODULES_KEY = "tianji_recent_modules_v1";
export const RECENT_MODULES_LIMIT = 4;

export function readRecentModules(storage = globalThis.localStorage) {
  try {
    const parsed = JSON.parse(storage?.getItem(RECENT_MODULES_KEY) || "[]");
    if (!Array.isArray(parsed)) return [];
    // 过滤掉已下线或手改过的路径，避免首页出现死链
    return parsed.filter((path) => MODULE_BY_PATH[path]).slice(0, RECENT_MODULES_LIMIT);
  } catch {
    return [];
  }
}

export function pushRecentModule(path, storage = globalThis.localStorage) {
  if (!MODULE_BY_PATH[path]) return readRecentModules(storage);
  const next = [
    path,
    ...readRecentModules(storage).filter((item) => item !== path),
  ].slice(0, RECENT_MODULES_LIMIT);
  try {
    storage?.setItem(RECENT_MODULES_KEY, JSON.stringify(next));
  } catch {
    // 隐私模式 / 配额不足时不影响主流程
  }
  return next;
}
