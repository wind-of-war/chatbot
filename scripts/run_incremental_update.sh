#!/usr/bin/env bash
set -euo pipefail

LOCK_FILE="/tmp/gxp-docs-update.lock"
REPO_ROOT="/opt/gxp-ai-platform"
FULL_REBUILD="${FULL_REBUILD:-false}"

mkdir -p "$REPO_ROOT/logs"

(
  flock -n 9 || {
    echo "[SKIP] update already running"
    exit 0
  }

  cd "$REPO_ROOT"
  echo "[START] $(date -u +%F_%T) update full_rebuild=$FULL_REBUILD"
  FULL_REBUILD="$FULL_REBUILD" bash scripts/update_regulatory_corpus.sh
  echo "[DONE] $(date -u +%F_%T) update full_rebuild=$FULL_REBUILD"
) 9>"$LOCK_FILE" >> "$REPO_ROOT/logs/docs_update_watcher.log" 2>&1
