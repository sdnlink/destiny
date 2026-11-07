/**
 * 本地推演存档 → 后端推演会话（审计 14 的反向通道）。
 *
 * 两套持久化不是同一个模型：本地存档存的是经典推演的 `compare` 应答包
 * （module_results 一次算完），后端会话存的是七步工作流的冻结快照 + 交互记录。
 * 所以「写回」不是把旧 JSON 塞进后端，而是**用存档里的事由与起盘时刻在后端重建一次**：
 * - 事由、分类、起盘时刻（local_datetime/timezone）从存档里取，尽量还原；
 * - `cast_nonce`（自动起卦的随机种子）当时没有落盘，只能重新生成，
 *   因此重建出来的盘面**可能与存档盘面不同**，界面上必须把这一点说明白；
 * - 存档原件保留，不清除。
 */

import { localDateTimeValue, newCastNonce } from "./castingInput.js";
import { CATEGORIES, normalizeCategory } from "./labels.js";
import { castSession, createSession } from "./sessionApi.js";

const BACKEND_CATEGORIES = new Set(CATEGORIES.map((entry) => entry.id));

function pickString(value) {
  return typeof value === "string" && value.trim() ? value.trim() : "";
}

function calendarResultOf(item) {
  const modules = item?.result?.module_results;
  if (!Array.isArray(modules)) return null;
  const calendar = modules.find((entry) => entry?.module === "calendar");
  return calendar?.result || null;
}

/** 存档里可用的起盘时刻：优先新存档显式保存的 input，其次历法结果回显，最后退回存档时间。 */
export function resolveCastingSource(item) {
  const calendar = calendarResultOf(item);
  const saved = item?.input || item?.context?.input || null;
  const localDatetime =
    pickString(saved?.local_datetime) ||
    pickString(calendar?.input?.local_datetime) ||
    pickString(item?.calculated_at) ||
    localDateTimeValue();
  const timezone =
    pickString(saved?.timezone) ||
    pickString(calendar?.input?.timezone) ||
    Intl.DateTimeFormat().resolvedOptions().timeZone ||
    "Asia/Shanghai";
  const useTrueSolarTime = Boolean(saved?.use_true_solar_time ?? calendar?.input?.use_true_solar_time);
  // 真太阳时必须有经度才谈得上还原。新存档存在 input.longitude，老存档可从
  // 历法结果的 input 回显里取；都没有就不能假装还原（后端缺经度会拒绝起盘）。
  const rawLongitude = saved?.longitude ?? calendar?.input?.longitude;
  const longitude = Number.isFinite(Number(rawLongitude)) && rawLongitude !== null && rawLongitude !== ""
    ? Number(rawLongitude)
    : null;
  return { local_datetime: localDatetime, timezone, use_true_solar_time: useTrueSolarTime, longitude };
}

/** 存档分类可能是旧别名（wealth/job/…），后端只认 11 个规范键。 */
export function resolveCategory(item) {
  const raw = pickString(item?.category) || "other";
  const normalized = normalizeCategory(raw);
  return BACKEND_CATEGORIES.has(normalized) ? normalized : "other";
}

/**
 * 组装 `POST /v1/sessions` 的请求体。
 * 起盘方式固定用 `time`：存档里有明确的起盘时刻，用时间起盘才谈得上还原。
 */
export function buildMigrationPayload(item, { nonceFactory = newCastNonce } = {}) {
  const question = pickString(item?.question);
  if (!question) throw new Error("存档缺少求测事由，无法重建会话");
  const source = resolveCastingSource(item);
  if (source.use_true_solar_time && source.longitude === null) {
    // 不静默降级成标准时：那会重建出另一张盘，而界面上看不出差别
    throw new Error("存档使用了真太阳时但缺少经度，无法重建；请重新起盘");
  }
  return {
    question,
    category: resolveCategory(item),
    system: "auto",
    casting_method: "time",
    casting_source: {
      ...source,
      cast_nonce: nonceFactory(),
    },
    user_profile: {},
  };
}

/**
 * 真正写回：建会话 → 排盘。返回可用于「在交互推演中打开」的 session_id。
 * 任一步失败都抛错，由调用方提示；不会半途静默。
 */
export async function migrateHistoryItem(item, { nonceFactory = newCastNonce } = {}) {
  const payload = buildMigrationPayload(item, { nonceFactory });
  const created = await createSession(payload);
  const sessionId = created?.session_id;
  if (!sessionId) throw new Error("后端未返回 session_id");
  const casted = await castSession(sessionId);
  return {
    sessionId,
    snapshotId: casted?.snapshot_id || null,
    fidelity: "沿用存档起盘时刻重建；随机种子已重新生成，盘面可能与存档不同",
  };
}
