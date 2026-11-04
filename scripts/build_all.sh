#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$project_dir/scripts/env_python.sh"

frontend_dir="$project_dir/frontend"
install_dependencies="${BUILD_INSTALL_DEPENDENCIES:-1}"
run_tests="${BUILD_RUN_TESTS:-1}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Required command is missing: $1" >&2
    exit 2
  fi
}

require_command npm

if [[ ! -x "$PYTHON_BIN" ]]; then
  echo "Python binary not found or not executable: $PYTHON_BIN" >&2
  exit 2
fi

echo "[build] using Python environment: $PYTHON_BIN"
"$PYTHON_BIN" --version

if [[ "$install_dependencies" == "1" ]]; then
  echo "[build] installing backend dependencies into Python environment"
  "$PYTHON_BIN" -m pip install -r "$project_dir/backend/requirements.txt"
  "$PYTHON_BIN" -m pip install -r "$project_dir/backend/requirements-dev.txt"

  echo "[build] installing frontend dependencies"
  npm --prefix "$frontend_dir" install
elif [[ ! -d "$frontend_dir/node_modules" ]]; then
  echo "Frontend dependencies are missing and BUILD_INSTALL_DEPENDENCIES=0" >&2
  exit 2
fi

echo "[build] compiling backend Python sources"
"$PYTHON_BIN" -m compileall -q "$project_dir/backend/app" "$project_dir/backend/tests"

# 典籍语料（cache/ 与 data/generated/ 均不入库）：缓存齐全时离线重建，无需联网；
# 干净 clone 无缓存时跳过，依赖真实语料的测试会明确 skip（见 test_review_hardening.py）。
cache_ok=1
for catalog in wikisource/catalog.json open-sources/catalog.json web-classics/catalog.json; do
  if [[ ! -f "$project_dir/cache/$catalog" ]]; then
    cache_ok=0
  fi
done
if [[ "$cache_ok" == "1" ]]; then
  echo "[build] rebuilding local classics corpus from cached sources"
  "$PYTHON_BIN" "$project_dir/scripts/build_classics_corpus.py" --repo-root "$project_dir"
else
  echo "[build] classics cache missing; skipping corpus rebuild (see docs/sources/wikisource.md)"
fi

if [[ "$run_tests" == "1" ]]; then
  echo "[build] running backend tests"
  "$PYTHON_BIN" -m pytest "$project_dir/backend/tests"
fi

echo "[build] building same-origin frontend assets"
VITE_API_ROOT="" npm --prefix "$frontend_dir" run build

if [[ ! -f "$frontend_dir/dist/index.html" ]]; then
  echo "Frontend build did not produce dist/index.html" >&2
  exit 1
fi

echo "[build] complete"
echo "  python:   $PYTHON_BIN"
echo "  backend:  $project_dir/backend/app"
echo "  frontend: $frontend_dir/dist"
