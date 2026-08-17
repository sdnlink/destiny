#!/usr/bin/env bash
set -u

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$project_dir/scripts/env_python.sh"

cooldown_seconds="${CACHE_RETRY_COOLDOWN:-60}"
attempt=0

while true; do
  attempt=$((attempt + 1))
  echo "starting cache attempt $attempt at $(date -Iseconds)"

  if "$PYTHON_BIN" "$project_dir/scripts/cache_daorenjia_texts.py" \
    --output "$project_dir/cache/daorenjia" \
    --reuse-catalog \
    --source mobile-api \
    --incomplete-only \
    --delay 1.0 \
    --timeout 60 \
    --retries 3; then
    echo "cache completed at $(date -Iseconds)"
    exit 0
  fi

  if [[ -f "$project_dir/cache/daorenjia/summary.json" ]]; then
    jq '{cached_books,text_unavailable_books,failed_books,pending_books,interrupted}' \
      "$project_dir/cache/daorenjia/summary.json"
  fi
  echo "source unavailable or cache incomplete; retrying in ${cooldown_seconds}s"
  sleep "$cooldown_seconds"
done
