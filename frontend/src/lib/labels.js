/**
 * 标签与历法小工具的唯一实现（前端）。
 *
 * 这里的事项分类必须与后端 `app/common/categories.py` 的 CATEGORIES 一致：
 * 后端 `tests/test_frontend_labels.py` 会读取本文件并逐项比对，改一边漏另一边会直接测试失败。
 * 之前在 InputPanel 写死 <option>、在 WorkflowPanel 再写一份、在测试里又抄一份，
 * 三处各自漂移，用户看到的中文标签和实际提交的 category 键经常对不上。
 */

export const CATEGORIES = [
  { id: "career", label: "事业" },
  { id: "finance", label: "财运" },
  { id: "relationship", label: "感情姻缘" },
  { id: "study", label: "考试学业" },
  { id: "lawsuit", label: "官司是非" },
  { id: "travel", label: "出行" },
  { id: "missing_person", label: "寻人" },
  { id: "lost_item", label: "失物" },
  { id: "health", label: "健康" },
  { id: "decision", label: "抉择" },
  { id: "other", label: "其他谋事" },
];

export const LEGACY_CATEGORY_ALIASES = {
  wealth: "finance",
  money: "finance",
  marriage: "relationship",
  love: "relationship",
  academics: "study",
  exam: "study",
  work: "career",
  career_change: "career",
  job: "career",
  litigation: "lawsuit",
  trip: "travel",
  missing: "missing_person",
  lost: "lost_item",
};

export const STATUS_LABELS = {
  draft: "待排盘",
  casted: "已排盘",
  interacting: "交互中",
  reviewed: "已复盘",
};

/**
 * 交互推演的术数门类选项。
 * id 必须与后端 `SessionCreateRequest.system` 的取值域
 * （auto/meihua/liuyao/qimen/daliuren/bazi/ziwei）一致。
 */
export const SYSTEMS = [
  { id: "auto", label: "默认（梅花+六爻）" },
  { id: "meihua", label: "梅花易数" },
  { id: "liuyao", label: "六爻纳甲" },
  { id: "qimen", label: "奇门遁甲" },
  { id: "daliuren", label: "大六壬" },
  { id: "bazi", label: "八字命理" },
  { id: "ziwei", label: "紫微斗数" },
];

/** 起盘方式选项，取值域对应后端 casting_method（auto/time/numbers/manual）。 */
export const CASTING_METHODS = [
  { id: "auto", label: "自动起卦" },
  { id: "time", label: "时间起卦" },
  { id: "numbers", label: "报数起卦" },
  { id: "manual", label: "手工起卦" },
];

export const FORTUNE_COLORS = {
  大吉: "#297267",
  小吉: "#3a8a7d",
  平: "#a66d1e",
  小凶: "#b85c3a",
  大凶: "#a53e2d",
  未评级: "#5b6470",
};

export const EARTHLY_BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

export const BRANCH_CLASH = {
  子: "午", 午: "子",
  丑: "未", 未: "丑",
  寅: "申", 申: "寅",
  卯: "酉", 酉: "卯",
  辰: "戌", 戌: "辰",
  巳: "亥", 亥: "巳",
};

export function normalizeCategory(value) {
  if (!value) return "other";
  const trimmed = String(value).trim().toLowerCase();
  const mapped = LEGACY_CATEGORY_ALIASES[trimmed] || trimmed;
  return CATEGORIES.some((item) => item.id === mapped) ? mapped : "other";
}

export function categoryLabel(cat) {
  const normalized = normalizeCategory(cat);
  const found = CATEGORIES.find((item) => item.id === normalized);
  return found ? found.label : "其他谋事";
}

export function statusLabel(status) {
  return STATUS_LABELS[status] || status || "未知";
}

export function formatDate(dateStr) {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  if (Number.isNaN(date.getTime())) return dateStr;
  return date.toLocaleDateString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export function daysToBranch(fromBranch, toBranch) {
  const fromIndex = EARTHLY_BRANCHES.indexOf(fromBranch);
  const toIndex = EARTHLY_BRANCHES.indexOf(toBranch);
  if (fromIndex < 0 || toIndex < 0) return null;
  return ((toIndex - fromIndex) % 12 + 12) % 12;
}
