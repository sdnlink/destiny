// 结果工作区共用的展示层映射常量（原 ResultWorkspace.jsx 顶部常量）
//
// 事项分类标签必须与输入面板同一份真源：这里原本手写 6 项，
// 官司/寻人/失物/健康/抉择 五类在结果页会渲染成 "undefined"，
// 另外四项的中文也和下拉不一致（财运/财务、考试学业/学业…）。
import { CATEGORIES } from "../../lib/labels.js";

export const PILLAR_LABELS = { year: "年柱", month: "月柱", day: "日柱", time: "时柱" };

export const CATEGORY_LABELS = Object.fromEntries(
  CATEGORIES.map(({ id, label }) => [id, label]),
);

export const SCENE_LABELS = {
  combined: "综合推演",
  zhouyi: "周易",
  meihua: "梅花易数",
  liuyao: "六爻",
  liuren: "大六壬",
  qimen: "奇门遁甲",
  bazi: "八字命理",
  ziwei: "紫微斗数",
  fengshui: "阳宅风水",
};

export const IMAGERY_MODULE_LABELS = {
  zhouyi: "周易",
  meihua: "梅花",
  liuyao: "六爻",
  liuren: "六壬",
  qimen: "奇门",
  bazi: "八字",
  ziwei: "紫微",
};

export const IMAGERY_STAGE_LABELS = { original: "本盘", changed: "变盘" };

export const CAST_METHOD_LABELS = {
  personalized_three_coin: "个体三枚铜钱",
  personalized_lunar_time: "个体时间取数",
  personalized_report_number: "个体报数",
  three_coins: "三枚铜钱",
  six_lines: "六爻手排",
  lunar_time: "传统时间",
  time: "传统时间",
  number_hour: "数字排盘",
  two_numbers: "数字排盘",
  three_numbers: "三数起卦",
  numbers: "报数起卦",
  eight_palace_pure_hexagram: "八纯卦起局",
};

export const IMAGERY_ROLE_LABELS = {
  upper_trigram: "上卦",
  lower_trigram: "下卦",
  body: "体卦",
  use: "用卦",
  changed_use: "变卦之用",
  palace: "卦宫",
  month_general: "月将",
  initial_transmission: "初传",
  middle_transmission: "中传",
  final_transmission: "末传",
};

export const ELEMENT_COLORS = {
  木: "#2e7d32",
  火: "#c62828",
  土: "#d87a16",
  金: "#b78103",
  水: "#1565c0",
};
