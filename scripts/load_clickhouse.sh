#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$project_dir/scripts/env_python.sh"

clickhouse_url="${CLICKHOUSE_URL:-http://localhost:18123}"
clickhouse_user="${CLICKHOUSE_USER:-destiny}"
: "${CLICKHOUSE_PASSWORD:?CLICKHOUSE_PASSWORD 必须显式注入，脚本不再内置默认口令}"
clickhouse_password="$CLICKHOUSE_PASSWORD"

"$PYTHON_BIN" "$project_dir/scripts/generate_seed.py"

for attempt in $(seq 1 30); do
  if curl --silent --fail --user "$clickhouse_user:$clickhouse_password" "$clickhouse_url/ping" >/dev/null; then
    break
  fi
  if [[ "$attempt" == "30" ]]; then
    echo "ClickHouse did not become ready at $clickhouse_url" >&2
    exit 1
  fi
  sleep 1
done

while IFS= read -r -d ';' statement; do
  if [[ -n "${statement//[[:space:]]/}" ]]; then
    curl --silent --show-error --fail --user "$clickhouse_user:$clickhouse_password" \
      --data-binary "$statement" "$clickhouse_url/"
  fi
done < "$project_dir/clickhouse/init/001_schema.sql"

tables=(data_sources five_elements heavenly_stems earthly_branches branch_imagery trigrams trigram_imagery hexagrams hexagram_explanations solar_terms sexagenary_cycle fengshui_mountains luoshu_palaces)
for table in "${tables[@]}"; do
  curl --silent --show-error --fail --user "$clickhouse_user:$clickhouse_password" \
    --data-binary "TRUNCATE TABLE destiny.$table" "$clickhouse_url/"
  curl --silent --show-error --fail --user "$clickhouse_user:$clickhouse_password" \
    --data-binary @"$project_dir/data/generated/$table.jsonl" \
    "$clickhouse_url/?query=INSERT%20INTO%20destiny.$table%20FORMAT%20JSONEachRow"
  echo "loaded $table"
done

curl --silent --show-error --fail --user "$clickhouse_user:$clickhouse_password" \
  --get \
  --data-urlencode "query=SELECT table, sum(rows) AS rows FROM system.parts WHERE active AND database = 'destiny' GROUP BY table ORDER BY table FORMAT PrettyCompact" \
  "$clickhouse_url/"
