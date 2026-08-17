#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
frontend_dir="$project_dir/frontend"

if [[ ! -d "$frontend_dir/node_modules" ]]; then
  echo "Frontend dependencies are missing. Run: cd frontend && npm install" >&2
  exit 2
fi

cd "$frontend_dir"
exec npm run dev
