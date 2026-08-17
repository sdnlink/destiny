#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$project_dir/scripts/env_python.sh"

bind="${APP_API_BIND:-127.0.0.1}"
port="${APP_API_PORT:-8090}"

if [[ "$bind" != "127.0.0.1" && "$bind" != "localhost" && "$bind" != "::1" && -z "${APP_API_TOKEN:-}" ]]; then
  echo "APP_API_TOKEN is required when binding beyond loopback" >&2
  exit 2
fi

exec "$PYTHON_BIN" -m uvicorn app.main:app \
  --app-dir "$project_dir/backend" \
  --host "$bind" \
  --port "$port"
