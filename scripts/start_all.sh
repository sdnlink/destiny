#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -x "$project_dir/.venv/bin/uvicorn" ]]; then
  echo "Backend dependencies are missing. Run ./scripts/build_all.sh first." >&2
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

echo "Starting Tianji Yanxiang at http://${APP_API_BIND:-127.0.0.1}:${APP_API_PORT:-8090}"
exec "$project_dir/scripts/run_mvp_api.sh"
