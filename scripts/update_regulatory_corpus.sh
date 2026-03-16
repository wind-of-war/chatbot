#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-}"
FULL_REBUILD="${FULL_REBUILD:-true}"
MANIFEST="${MANIFEST:-data/sources/regulatory_docs_sources.json}"
RAW_ROOT="${RAW_ROOT:-data/raw}"

if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x ".venv/bin/python" ]]; then
    PYTHON_BIN=".venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi

echo "[1/4] Download regulatory sources..."
"$PYTHON_BIN" scripts/download_regulatory_sources.py --manifest "$MANIFEST" --raw-root "$RAW_ROOT"

if [[ "$FULL_REBUILD" == "true" ]]; then
  echo "[2/4] Full rebuild enabled: clean processed/embeddings..."
  rm -f data/processed/*.txt || true
  rm -f data/embeddings/*.vec || true
else
  echo "[2/4] Full rebuild disabled: keep existing processed/embeddings..."
fi

echo "[3/4] Ingest PDF documents..."
"$PYTHON_BIN" -m pipelines.ingestion.ingest_documents --raw-dir "$RAW_ROOT"

echo "[4/4] Build vector index..."
"$PYTHON_BIN" -m pipelines.indexing.build_vector_index

echo "Regulatory corpus update completed."
