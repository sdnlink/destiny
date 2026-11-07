// 交互式推演会话 API（工作流引擎 + 交互模块A-G）

import { getClientId } from "./clientIdentity.js";

// 用可选链读取：本模块也会在 Vite 之外的纯 node 测试进程里被 import，
// 那里没有 import.meta.env，直接点取会抛 TypeError 把整个测试文件带崩。
const configuredApiRoot = import.meta.env?.VITE_API_ROOT;
const API_ROOT = configuredApiRoot === undefined ? "/api" : configuredApiRoot;

async function request(path, options = {}) {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      // 会话归属（审计 22）：后端按这个 id 的哈希校验会话属于谁
      "X-Client-Id": getClientId(),
      ...options.headers,
    },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const message = body?.error?.message || `请求失败（${response.status}）`;
    throw new Error(message);
  }
  return body?.data ?? body;
}

// 创建推演会话（模块A：信息补全）
export function createSession(payload) {
  return request("/v1/sessions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

// 列出会话
export function listSessions(limit = 50) {
  return request(`/v1/sessions?limit=${limit}`);
}

// 获取会话完整状态
export function getSession(sessionId) {
  return request(`/v1/sessions/${sessionId}`);
}

// 执行排盘（7步工作流，冻结不可变快照）
export function castSession(sessionId) {
  return request(`/v1/sessions/${sessionId}/cast`, {
    method: "POST",
    body: JSON.stringify({}),
  });
}

// 交互入口（模块B/E/F/G等）
export function interactSession(sessionId, interactionType, payload = {}) {
  return request(`/v1/sessions/${sessionId}/interact`, {
    method: "POST",
    body: JSON.stringify({ interaction_type: interactionType, payload }),
  });
}

// 模块B：现实校验
export function realityCheck(sessionId, response, details = "") {
  return interactSession(sessionId, "reality_check", { response, details });
}

// 模块E：多方人物取象
export function multiPartyAnalysis(sessionId, parties = null, focusParty = null) {
  return interactSession(sessionId, "multi_party", { parties, focus_party: focusParty });
}

// 模块F：多抉择分支推演
export function multiChoiceAnalysis(sessionId, choices) {
  return interactSession(sessionId, "multi_choice", { choices });
}

// 模块G：事后复盘
export function reviewOutcome(sessionId, actualOutcome, outcomeDetails = null) {
  return interactSession(sessionId, "review", { actual_outcome: actualOutcome, outcome_details: outcomeDetails });
}

// 深度追问
export function deepQuestion(sessionId, question) {
  return interactSession(sessionId, "deep_question", { question });
}

// 换角度解读
export function angleShift(sessionId, newAngle) {
  return interactSession(sessionId, "angle_shift", { new_angle: newAngle });
}

// 应用信息补全答案
export function applyCompletion(sessionId, answers) {
  return interactSession(sessionId, "info_completion", { answers });
}

// 删除会话
export function deleteSession(sessionId) {
  return request(`/v1/sessions/${sessionId}`, {
    method: "DELETE",
  });
}
