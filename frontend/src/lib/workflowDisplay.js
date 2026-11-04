/**
 * 工作流展示层的纯格式化逻辑。
 *
 * 抽到 lib 是为了可单测：这些判断（干支是对象还是字符串、缺字段怎么兜底）
 * 一旦写错，界面上只会出现「[object Object]年」或整行空白，不会报错。
 */

/**
 * 历法基线的干支文本。
 * 后端旧结构把 ganzhi 存成 {text, stem, branch...} 对象，直接插值会渲染成
 * 「[object Object]年」；这里优先用 pillars（已是「丙午」这样的字符串），
 * 再退回 ganzhi 的 text / stem+branch。
 */
export function calendarGanzhiText(calendar) {
  const pillars = calendar?.pillars || {};
  const ganzhi = calendar?.ganzhi || {};
  const pick = (key) => {
    const fromPillars = pillars[key];
    if (typeof fromPillars === "string" && fromPillars) return fromPillars;
    const raw = ganzhi[key];
    if (typeof raw === "string") return raw;
    if (raw && typeof raw === "object") return raw.text || `${raw.stem || ""}${raw.branch || ""}`;
    return "";
  };
  const year = pick("year");
  const month = pick("month");
  const day = pick("day");
  const hour = pick("hour");
  if (!year && !month && !day) return "历法数据缺失";
  return [year && `${year}年`, month && `${month}月`, day && `${day}日`, hour && `${hour}时`]
    .filter(Boolean)
    .join(" ");
}

/**
 * 节气解析。后端 solar_term 是 {previous/current/next/...} 结构，且不在节气当天时
 * current 为 null，直接插值会渲染成「[object Object]」。这里按
 * current → next → previous 取最近的一个，并带回相对关系。
 */
function resolveSolarTerm(solarTerm) {
  if (typeof solarTerm === "string") return { name: solarTerm, note: "" };
  if (!solarTerm || typeof solarTerm !== "object") return { name: "", note: "" };
  const candidates = [
    ["current", "当前节气"],
    ["next", "下一节气"],
    ["previous", "上一节气"],
  ];
  for (const [key, note] of candidates) {
    const item = solarTerm[key];
    const name = typeof item === "string" ? item : item?.name;
    if (name) return { name: String(name), note };
  }
  if (solarTerm.name) return { name: String(solarTerm.name), note: "" };
  return { name: "", note: "" };
}

/** 节气名（不含关系标注）。 */
export function solarTermText(solarTerm) {
  return resolveSolarTerm(solarTerm).name;
}

/**
 * 历法行里的节气片段：名字 + 相对关系（当前/下一/上一）。
 * 非节气当天时后端给的是「下一节气」，只写名字会让人误读成今天是该节气。
 * 兼容两种来源：后端压缩过的 {solar_term, solar_term_note}，以及原始节气对象。
 */
export function solarTermLabel(calendar) {
  const raw = calendar?.solar_term;
  const resolved = resolveSolarTerm(raw);
  const note = calendar?.solar_term_note || resolved.note;
  if (!resolved.name) return "";
  if (note && note !== "当前节气") return `${resolved.name}（${note}）`;
  return resolved.name;
}
