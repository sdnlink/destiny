#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$project_dir/scripts/env_python.sh"

cd "$project_dir/backend"
exec "$PYTHON_BIN" -m app.corpus_api "$@"
