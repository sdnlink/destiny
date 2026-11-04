#!/usr/bin/env bash
# 部署脚本（Linux / macOS）。与 deploy.ps1、deploy.bat 行为对齐：
# 默认先构建再启动，可用 DEPLOY_SKIP_BUILD=1 / DEPLOY_START=0 拆分两步。
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${DEPLOY_SKIP_BUILD:-0}" != "1" ]]; then
  "$project_dir/scripts/build_all.sh"
fi

if [[ "${DEPLOY_START:-1}" == "0" ]]; then
  echo "Deployment assets are ready. DEPLOY_START=0, service was not started."
  exit 0
fi

exec "$project_dir/scripts/start_all.sh"
