#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
clickhouse_url="${CLICKHOUSE_URL:-http://localhost:18123}"
clickhouse_user="${CLICKHOUSE_USER:-destiny}"
clickhouse_password="${CLICKHOUSE_PASSWORD:-destiny_local}"
generated_dir="$project_dir/data/generated/corpus"

"$project_dir/scripts/build_corpus.py"

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

for table in corpus_chunks corpus_documents corpus_ingestion_runs; do
  echo "truncating $table"
  curl --silent --show-error --fail --user "$clickhouse_user:$clickhouse_password" \
    --data-binary "TRUNCATE TABLE destiny.$table" "$clickhouse_url/"
done

curl --silent --show-error --fail --user "$clickhouse_user:$clickhouse_password" \
  --data-binary @"$generated_dir/corpus_documents.jsonl" \
  "$clickhouse_url/?query=INSERT%20INTO%20destiny.corpus_documents%20FORMAT%20JSONEachRow"
echo "loaded corpus_documents"

curl --silent --show-error --fail --user "$clickhouse_user:$clickhouse_password" \
  --data-binary @"$generated_dir/corpus_chunks.jsonl" \
  "$clickhouse_url/?query=INSERT%20INTO%20destiny.corpus_chunks%20FORMAT%20JSONEachRow"
echo "loaded corpus_chunks"

jq -c '.status = "loaded"' "$generated_dir/corpus_ingestion_runs.jsonl" | \
  curl --silent --show-error --fail --user "$clickhouse_user:$clickhouse_password" \
    --data-binary @- \
    "$clickhouse_url/?query=INSERT%20INTO%20destiny.corpus_ingestion_runs%20FORMAT%20JSONEachRow"
echo "loaded corpus_ingestion_runs"

validation_query="
SELECT
  (SELECT count() FROM destiny.corpus_documents) AS documents,
  (SELECT count() FROM destiny.corpus_chunks) AS chunks,
  (SELECT sum(character_count) FROM destiny.corpus_documents) AS document_characters,
  (SELECT sum(character_count) FROM destiny.corpus_chunks) AS chunk_characters,
  (SELECT uniqExact(document_id) FROM destiny.corpus_chunks) AS chunk_documents,
  (SELECT count() FROM destiny.corpus_documents WHERE cache_status = 'text_unavailable') AS unavailable_documents,
  (SELECT sum(length(unavailable_subcontent_ids)) FROM destiny.corpus_documents) AS unavailable_subcontents
FORMAT JSONEachRow"

result="$(curl --silent --show-error --fail --user "$clickhouse_user:$clickhouse_password" \
  --get --data-urlencode "query=$validation_query" "$clickhouse_url/")"
echo "$result" | jq .

expected_documents="$(jq -r '.documents' "$generated_dir/corpus_analysis.json")"
expected_chunks="$(jq -r '.chunks' "$generated_dir/corpus_analysis.json")"
expected_characters="$(jq -r '.characters' "$generated_dir/corpus_analysis.json")"
actual_documents="$(echo "$result" | jq -r '.documents')"
actual_chunks="$(echo "$result" | jq -r '.chunks')"
document_characters="$(echo "$result" | jq -r '.document_characters')"
chunk_characters="$(echo "$result" | jq -r '.chunk_characters')"
chunk_documents="$(echo "$result" | jq -r '.chunk_documents')"

if [[ "$actual_documents" != "$expected_documents" \
   || "$actual_chunks" != "$expected_chunks" \
   || "$document_characters" != "$expected_characters" \
   || "$chunk_characters" != "$expected_characters" \
   || "$chunk_documents" != "$expected_documents" ]]; then
  echo "ClickHouse corpus validation failed" >&2
  exit 1
fi

echo "ClickHouse corpus validation passed"
