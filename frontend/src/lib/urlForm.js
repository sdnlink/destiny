import { CATEGORIES } from "./labels";

const DATETIME_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/;
const TIMEZONE_RE = /^[A-Za-z0-9_/+-]{1,64}$/;
const UINT_RE = /^\d{1,6}$/;
const LINES_RE = /^[6-9](,[6-9]){5}$/;
const COINS_RE = /^[23]{3}(,[23]{3}){5}$/;
const CATEGORY_IDS = new Set(CATEGORIES.map((item) => item.id));
const MAX_QUESTION = 120;

// 各体系起卦方式及其配套输入字段。pair 的顺序与 InputPanel 的 NumberPair 一致
// （梅花是「上卦数、下卦数」，其余是「下卦数、上卦数」），所以这里按字段顺序存取。
// 时空/命理/风水没有起卦方式，直接跳过。
const CAST_SPECS = {
  zhouyi: {
    field: "yiMethod",
    methods: ["auto", "time", "numbers", "three_numbers", "manual"],
    triple: "yiNumbers",
    pair: ["yiLower", "yiUpper"],
    lines: "lines",
  },
  meihua: {
    field: "meihuaMethod",
    methods: ["auto", "time", "numbers", "three_numbers"],
    triple: "mhNumbers",
    pair: ["mhUpper", "mhLower"],
  },
  liuyao: {
    field: "liuyaoMethod",
    methods: ["auto", "time", "numbers", "lines", "coins"],
    pair: ["lyLower", "lyUpper"],
    lines: "lyLines",
    coins: "lyCoins",
  },
};

const CAST_KEYS = ["method", "n1", "n2", "n3", "p1", "p2", "lines", "coins"];

function isUInt(value) {
  return typeof value === "string" && UINT_RE.test(value);
}

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

  const spec = CAST_SPECS[form.scene];
  const method = params.get("method");
  if (spec && method && spec.methods.includes(method)) {
    next[spec.field] = method;

    if (method === "three_numbers" && spec.triple) {
      const triple = [params.get("n1"), params.get("n2"), params.get("n3")];
      if (triple.every(isUInt)) next[spec.triple] = triple;
    }
    if (method === "numbers" && spec.pair) {
      const p1 = params.get("p1");
      const p2 = params.get("p2");
      if (isUInt(p1) && isUInt(p2)) {
        next[spec.pair[0]] = p1;
        next[spec.pair[1]] = p2;
      }
    }
    if ((method === "manual" || method === "lines") && spec.lines) {
      const lines = params.get("lines");
      if (lines && LINES_RE.test(lines)) next[spec.lines] = lines.split(",").map(Number);
    }
    if (method === "coins" && spec.coins) {
      const coins = params.get("coins");
      if (coins && COINS_RE.test(coins)) {
        next[spec.coins] = coins.split(",").map((group) => group.split("").map(Number));
      }
    }
  }
  return next;
}

/**
 * 起卦成功后把关键输入（含起卦方式与配套输入）写回 URL（调用方用 replace，
 * 不新增历史记录）。这样地址栏本身就是一条可复制分享的完整推演链接。
 *
 * 注意：个体自动起卦的 castNonce 每次提交都会重新生成，这是刻意保留的随机性，
 * 不写入 URL；因此 auto 方式分享出去的链接会重新起卦，而非复现同一卦。
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

  // 先清掉上一轮的起卦参数，避免切换方式后残留旧输入
  for (const key of CAST_KEYS) next.delete(key);

  const spec = CAST_SPECS[form.scene];
  if (!spec) return next;
  const method = form[spec.field];
  if (!spec.methods.includes(method)) return next;
  next.set("method", method);

  if (method === "three_numbers" && spec.triple) {
    const triple = form[spec.triple] || [];
    if (triple.length === 3 && triple.every((value) => isUInt(String(value)))) {
      triple.forEach((value, index) => next.set(`n${index + 1}`, String(value)));
    }
  } else if (method === "numbers" && spec.pair) {
    const a = form[spec.pair[0]];
    const b = form[spec.pair[1]];
    if (isUInt(String(a)) && isUInt(String(b))) {
      next.set("p1", String(a));
      next.set("p2", String(b));
    }
  } else if ((method === "manual" || method === "lines") && spec.lines) {
    const lines = form[spec.lines] || [];
    if (lines.length === 6 && lines.every((value) => Number.isInteger(value) && value >= 6 && value <= 9)) {
      next.set("lines", lines.join(","));
    }
  } else if (method === "coins" && spec.coins) {
    const coins = form[spec.coins] || [];
    const encoded = coins.map((group) => (group || []).join("")).join(",");
    if (COINS_RE.test(encoded)) next.set("coins", encoded);
  }
  return next;
}
