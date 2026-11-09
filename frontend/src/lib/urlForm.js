import { CATEGORIES } from "./labels";

const DATETIME_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/;
const TIMEZONE_RE = /^[A-Za-z0-9_/+-]{1,64}$/;
const CATEGORY_IDS = new Set(CATEGORIES.map((item) => item.id));
const MAX_QUESTION = 120;

/**
 * 从 URL 查询参数预填起卦表单，让链接可直接分享。
 * 只接受白名单 / 格式合法的值，避免把任意 query 原样灌进表单再提交给后端。
 */
export function applyUrlOverrides(form, params) {
  const next = { ...form };
  const question = params.get("q");
  if (question) next.question = question.slice(0, MAX_QUESTION);
  const at = params.get("at");
  if (at && DATETIME_RE.test(at)) next.localDatetime = at;
  const tz = params.get("tz");
  if (tz && TIMEZONE_RE.test(tz)) next.timezone = tz;
  const cat = params.get("cat");
  if (cat && CATEGORY_IDS.has(cat)) next.category = cat;
  return next;
}

/**
 * 起卦成功后把关键输入写回 URL（调用方用 replace，不新增历史记录）。
 * 这样地址栏本身就是可复制的完整推演链接。
 */
export function syncFormToSearchParams(params, form) {
  const next = new URLSearchParams(params);
  const values = {
    q: (form.question || "").slice(0, MAX_QUESTION),
    at: form.localDatetime || "",
    tz: form.timezone || "",
    cat: form.category || "",
  };
  for (const [key, value] of Object.entries(values)) {
    if (value) next.set(key, value);
    else next.delete(key);
  }
  return next;
}
