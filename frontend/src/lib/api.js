const configuredApiRoot = import.meta.env.VITE_API_ROOT;
const API_ROOT = configuredApiRoot === undefined ? "/api" : configuredApiRoot;

async function request(path, options = {}) {
  const response = await fetch(`${API_ROOT}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const validation = body?.detail?.[0]?.msg;
    const message = body?.error?.message || validation || `请求失败（${response.status}）`;
    throw new Error(message);
  }
  return body?.data ?? body;
}

export function checkHealth() {
  return request("/health");
}

export function loadRules() {
  return request("/v1/rules");
}

export function analyzeCalendar(payload) {
  return request("/v1/calendar/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function compareCalculations(calculations, context) {
  return request("/v1/calculations/compare", {
    method: "POST",
    body: JSON.stringify({ calculations, context }),
  });
}

export function evaluateCalculation(module, method, input) {
  return request("/v1/calculations/evaluate", {
    method: "POST",
    body: JSON.stringify({ module, method, input }),
  });
}

export function analyzeLiunian(payload) {
  return request("/v1/bazi/liunian", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function analyzeLifeline(payload) {
  return request("/v1/bazi/lifeline", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function analyzeFengshuiDirection(payload) {
  return request("/v1/fengshui/direction", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function analyzeFengshuiMeasurements(payload) {
  return request("/v1/fengshui/measurements", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function analyzeFengshuiBazhai(payload) {
  return request("/v1/fengshui/bazhai", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function analyzeFengshuiXuankong(payload) {
  return request("/v1/fengshui/xuankong", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function listFengshuiBuildings(tenantId = "local") {
  return request(`/v1/fengshui/buildings?tenant_id=${encodeURIComponent(tenantId)}`);
}

export function saveFengshuiBuilding({ tenantId = "local", buildingId, profile }) {
  return request("/v1/fengshui/buildings", {
    method: "POST",
    body: JSON.stringify({
      tenant_id: tenantId,
      building_id: buildingId,
      profile,
    }),
  });
}

export function deleteFengshuiBuilding(buildingId, tenantId = "local") {
  return request(`/v1/fengshui/buildings/${encodeURIComponent(buildingId)}?tenant_id=${encodeURIComponent(tenantId)}`, {
    method: "DELETE",
  });
}

export function loadYuanhuiCycle(year) {
  return request(`/v1/yuanhui/cycle?year=${encodeURIComponent(year)}`);
}

export function loadTiebanStatus() {
  return request("/v1/tieban/status");
}

export function loadClassicsStatus() {
  return request("/v1/classics/status");
}

export function searchClassics(query, limit = 8) {
  return request(`/v1/classics/search?q=${encodeURIComponent(query)}&limit=${encodeURIComponent(limit)}`);
}
