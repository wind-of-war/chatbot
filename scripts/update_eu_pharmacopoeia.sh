#!/usr/bin/env bash
set -euo pipefail

RAW_DIR="${1:-data/raw/eu_pharmacopoeia}"
PYTHON_BIN="${PYTHON_BIN:-}"

if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi

mkdir -p "$RAW_DIR"
"$PYTHON_BIN" -m pipelines.ingestion.ingest_documents --raw-dir "$RAW_DIR"
"$PYTHON_BIN" -m pipelines.indexing.build_vector_index

echo "EU Pharmacopoeia update completed from: $RAW_DIR"
