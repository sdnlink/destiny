/**
 * Local storage manager for deduction history and saved cases.
 *
 * 浏览器 localStorage 通常只有 5MB，而单次推演结果（module_results + 解释 + 文献）
 * 就有 200~400KB。此前固定存 50 条完整结果，写到第 20 条左右就会抛
 * QuotaExceededError，而错误只进了 console，用户看到的是「存档突然不再增长」。
 *
 * 现在的策略：
 * 1. 按字节预算而不是条数淘汰：始终保留最近的结果，超预算从最旧的开始丢；
 * 2. 单条超过 ITEM_BUDGET 时丢弃可重算的重字段（只保留展示必需部分），并打标记；
 * 3. 写入失败（配额或隐私模式）明确返回 false，调用方可以提示用户。
 */

const STORAGE_KEY = "tianji_deduction_history_v1";
const MAX_HISTORY_ITEMS = 50;
const TOTAL_BUDGET_BYTES = 3.5 * 1024 * 1024;
const ITEM_BUDGET_BYTES = 900 * 1024;

// 结果里体积大、且可以由服务端重新计算得到的字段，超预算时优先丢弃
const DROPPABLE_RESULT_KEYS = [
  "workflow_result",
  "interpretation",
  "literature",
  "targeted_deduction",
  "imagery",
  "yuan_hui_yun_shi",
  "explanation",
];

function byteLength(value) {
  try {
    return new Blob([value]).size;
  } catch (err) {
    // 环境没有 Blob（如某些测试桩）时退回 UCS-2 近似估算
    return value.length * 2;
  }
}

function compactResult(result) {
  const serialized = JSON.stringify(result);
  if (byteLength(serialized) <= ITEM_BUDGET_BYTES) {
    return { result, trimmed: false };
  }
  const compact = { ...result };
  for (const key of DROPPABLE_RESULT_KEYS) {
    delete compact[key];
    if (byteLength(JSON.stringify(compact)) <= ITEM_BUDGET_BYTES) break;
  }
  return { result: compact, trimmed: true };
}

function readRaw() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { items: [], corrupted: false };
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return { items: [], corrupted: true };
    return { items: parsed, corrupted: false };
  } catch (err) {
    console.warn("Failed to load history from localStorage:", err);
    return { items: [], corrupted: true };
  }
}

function persist(items) {
  let candidate = items;
  for (let attempt = 0; attempt < 6; attempt += 1) {
    try {
      const payload = JSON.stringify(candidate);
      localStorage.setItem(STORAGE_KEY, payload);
      return true;
    } catch (err) {
      if (!candidate.length) {
        console.warn("Failed to save deduction history:", err);
        return false;
      }
      // 配额不足：丢掉最旧的一半再试，最多退让 6 次
      candidate = candidate.slice(0, Math.max(1, Math.floor(candidate.length / 2)));
    }
  }
  return false;
}

function enforceBudget(items) {
  const kept = [];
  let used = 0;
  for (const item of items) {
    const size = byteLength(JSON.stringify(item));
    if (kept.length && used + size > TOTAL_BUDGET_BYTES) break;
    kept.push(item);
    used += size;
    if (kept.length >= MAX_HISTORY_ITEMS) break;
  }
  return kept;
}

export function getDeductionHistory() {
  const { items } = readRaw();
  return items;
}

/**
 * 取某个场景最近一次「可展示」的推演结果，用于模块页刷新后恢复。
 * 只认 ConsultPanel 提交的比对结果（含 module_results），避免误把八字/紫微的
 * 单体系结果、或被配额裁剪掉的残缺存档恢复成盘面。
 */
export function getLatestHistoryByScene(scene) {
  if (!scene) return null;
  const { items } = readRaw();
  return items.find((item) =>
    item.scene === scene
    && item.result
    && Array.isArray(item.result.module_results)
    && item.result.module_results.length > 0
  ) || null;
}

export function saveDeductionHistory(task_id, context, result) {
  if (!result || !task_id) return false;
  const { result: storedResult, trimmed } = compactResult(result);
  const item = {
    id: task_id,
    timestamp: Date.now(),
    question: context?.question || "事项推演",
    category: context?.category || "career",
    scene: context?.scene || "combined",
    calculated_at: result.calculated_at || new Date().toISOString(),
    summary: result.advisory?.conclusion?.headline || "推演完成",
    result: storedResult,
    result_trimmed: trimmed,
    context,
  };

  const { items } = readRaw();
  const filtered = items.filter((entry) => entry.id !== task_id);
  filtered.unshift(item);
  return persist(enforceBudget(filtered));
}

export function deleteDeductionHistory(id) {
  const { items } = readRaw();
  const filtered = items.filter((entry) => entry.id !== id);
  const ok = persist(filtered);
  return ok ? filtered : items;
}

export function clearDeductionHistory() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (err) {
    console.warn("Failed to clear history:", err);
  }
  return [];
}

export function exportAllHistoryJSON() {
  try {
    const history = getDeductionHistory();
    const payload = {
      version: "1.0",
      app: "tianji-yanxiang",
      exported_at: new Date().toISOString(),
      count: history.length,
      records: history,
    };
    const jsonStr = JSON.stringify(payload, null, 2);
    const blob = new Blob([jsonStr], { type: "application/json;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `tianji_cases_backup_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    return true;
  } catch (err) {
    console.warn("Failed to export history JSON:", err);
    return false;
  }
}

export function importHistoryJSON(jsonStr) {
  try {
    const parsed = JSON.parse(jsonStr);
    const incoming = Array.isArray(parsed) ? parsed : parsed.records;
    if (!Array.isArray(incoming)) {
      throw new Error("Invalid format: expected array of records");
    }
    const current = getDeductionHistory();
    const map = new Map();
    incoming.forEach((item) => {
      if (item && item.id) map.set(item.id, item);
    });
    current.forEach((item) => {
      if (item && item.id && !map.has(item.id)) map.set(item.id, item);
    });
    const merged = Array.from(map.values())
      .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
      .slice(0, MAX_HISTORY_ITEMS);
    const kept = enforceBudget(merged);
    const ok = persist(kept);
    return {
      success: ok,
      count: incoming.length,
      total: kept.length,
      merged: kept,
      dropped: merged.length - kept.length,
    };
  } catch (err) {
    console.warn("Failed to import history JSON:", err);
    return { success: false, error: err.message };
  }
}
