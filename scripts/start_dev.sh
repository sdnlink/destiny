#!/usr/bin/env bash
# 开发模式启动（Linux / macOS）。与 start_dev.bat、start_dev.ps1 行为对齐：
# 后端热重载 + 前端 Vite dev server，两者都在前台，Ctrl+C 退出。
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$project_dir/scripts/env_python.sh"

frontend_dir="$project_dir/frontend"
if [[ ! -d "$frontend_dir/node_modules" ]]; then
  echo "Frontend dependencies are missing. Run: cd frontend && npm install (or ./scripts/build_all.sh)" >&2
  exit 2
fi

if ! "$PYTHON_BIN" -c "import uvicorn, fastapi, lunar_python, pydantic, pytz" >/dev/null 2>&1; then
  echo "Backend dependencies are missing in Python environment ($PYTHON_BIN). Run ./scripts/build_all.sh first." >&2
  exit 2
fi

bind="${APP_API_BIND:-127.0.0.1}"
port="${APP_API_PORT:-8090}"

backend_pid=""
frontend_pid=""

cleanup() {
  trap - EXIT INT TERM
  [[ -z "$backend_pid" ]] || kill "$backend_pid" 2>/dev/null || true
  [[ -z "$frontend_pid" ]] || kill "$frontend_pid" 2>/dev/null || true
  [[ -z "$backend_pid" ]] || wait "$backend_pid" 2>/dev/null || true
  [[ -z "$frontend_pid" ]] || wait "$frontend_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "======================================================="
echo " 天机演象 开发模式启动"
echo " 后端 API (热重载): http://$bind:$port"
echo " 前端 Web (Vite):   http://127.0.0.1:5173"
echo "======================================================="

"$PYTHON_BIN" -m uvicorn app.main:app \
  --app-dir "$project_dir/backend" \
  --host "$bind" \
  --port "$port" \
  --reload &
backend_pid=$!

(cd "$frontend_dir" && exec npm run dev) &
frontend_pid=$!

wait "$backend_pid" "$frontend_pid"
