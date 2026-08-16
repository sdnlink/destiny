#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$project_dir/backend"
exec "$project_dir/.venv/bin/python" -m app.corpus_api "$@"
