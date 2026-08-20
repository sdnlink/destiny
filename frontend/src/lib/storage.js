/**
 * Local storage manager for deduction history and saved cases.
 */

const STORAGE_KEY = "tianji_deduction_history_v1";
const MAX_HISTORY_ITEMS = 50;

export function getDeductionHistory() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw);
  } catch (err) {
    console.error("Failed to load history from localStorage:", err);
    return [];
  }
}

export function saveDeductionHistory(task_id, context, result) {
  if (!result || !task_id) return;
  try {
    const history = getDeductionHistory();
    const item = {
      id: task_id,
      timestamp: Date.now(),
      question: context?.question || "事项推演",
      category: context?.category || "career",
      scene: context?.scene || "combined",
      calculated_at: result.calculated_at || new Date().toISOString(),
      summary: result.advisory?.conclusion?.headline || "推演完成",
      result,
      context,
    };

    // Remove if already exists, then add to the front
    const filtered = history.filter((h) => h.id !== task_id);
    filtered.unshift(item);

    const trimmed = filtered.slice(0, MAX_HISTORY_ITEMS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch (err) {
    console.error("Failed to save deduction history:", err);
  }
}

export function deleteDeductionHistory(id) {
  try {
    const history = getDeductionHistory();
    const filtered = history.filter((h) => h.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    return filtered;
  } catch (err) {
    console.error("Failed to delete history item:", err);
    return [];
  }
}

export function clearDeductionHistory() {
  try {
    localStorage.removeItem(STORAGE_KEY);
    return [];
  } catch (err) {
    console.error("Failed to clear history:", err);
    return [];
  }
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
    console.error("Failed to export history JSON:", err);
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
    localStorage.setItem(STORAGE_KEY, JSON.stringify(merged));
    return { success: true, count: incoming.length, total: merged.length, merged };
  } catch (err) {
    console.error("Failed to import history JSON:", err);
    return { success: false, error: err.message };
  }
}
