#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$project_dir/scripts/env_python.sh"

if ! "$PYTHON_BIN" -c "import uvicorn, fastapi, lunar_python, pydantic, pytz" >/dev/null 2>&1; then
  echo "Backend dependencies are missing in Python environment ($PYTHON_BIN). Run ./scripts/build_all.sh first." >&2
  exit 2
fi

if [[ ! -f "$project_dir/frontend/dist/index.html" ]]; then
  echo "Compiled frontend assets are missing. Run ./scripts/build_all.sh first." >&2
  exit 2
fi

if [[ "${START_CLICKHOUSE:-0}" == "1" ]]; then
  if ! command -v docker >/dev/null 2>&1; then
    echo "Docker is required when START_CLICKHOUSE=1" >&2
    exit 2
  fi
  docker compose -f "$project_dir/docker-compose.yml" up -d clickhouse
fi

export SERVE_WEB=1
export WEB_DIST_DIR="$project_dir/frontend/dist"
export ENABLE_LITERATURE="${ENABLE_LITERATURE:-1}"

corpus_pid=""
backend_pid=""

cleanup() {
  trap - EXIT INT TERM
  if [[ -n "$backend_pid" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    kill "$backend_pid" 2>/dev/null || true
  fi
  if [[ -n "$corpus_pid" ]] && kill -0 "$corpus_pid" 2>/dev/null; then
    kill "$corpus_pid" 2>/dev/null || true
  fi
  [[ -z "$backend_pid" ]] || wait "$backend_pid" 2>/dev/null || true
  [[ -z "$corpus_pid" ]] || wait "$corpus_pid" 2>/dev/null || true
}

trap cleanup EXIT INT TERM

if [[ "$ENABLE_LITERATURE" == "1" && "${START_CORPUS_API:-1}" == "1" ]]; then
  corpus_health_url="${CORPUS_API_URL:-http://127.0.0.1:8088}/health"
  if ! curl --fail --silent --max-time 1 "$corpus_health_url" >/dev/null 2>&1; then
    echo "Starting internal corpus service for literature opinions"
    "$project_dir/scripts/run_corpus_api.sh" &
    corpus_pid=$!
    for _ in {1..20}; do
      if curl --fail --silent --max-time 1 "$corpus_health_url" >/dev/null 2>&1; then
        break
      fi
      if ! kill -0 "$corpus_pid" 2>/dev/null; then
        break
      fi
      sleep 0.25
    done
    if ! curl --fail --silent --max-time 1 "$corpus_health_url" >/dev/null 2>&1; then
      echo "Warning: corpus service is unavailable; calculations will continue without book opinions" >&2
    fi
  fi
fi

echo "Starting Tianji Yanxiang at http://${APP_API_BIND:-127.0.0.1}:${APP_API_PORT:-8090}"
"$project_dir/scripts/run_mvp_api.sh" &
backend_pid=$!
wait "$backend_pid"
