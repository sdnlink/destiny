const API_ROOT = import.meta.env.VITE_API_ROOT || "/api";

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

export function compareCalculations(calculations) {
  return request("/v1/calculations/compare", {
    method: "POST",
    body: JSON.stringify({ calculations }),
  });
}
