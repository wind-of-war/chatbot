#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$REPO_ROOT/logs"
mkdir -p "$LOG_DIR"

cd "$REPO_ROOT"

/usr/bin/flock -n /tmp/gxp-faq-review.lock \
  "$REPO_ROOT/.venv/bin/python" "$REPO_ROOT/scripts/build_faq_proposals.py" \
  --append-review-queue \
  --top-k 10 \
  >> "$LOG_DIR/faq_review_daily.log" 2>&1 || true
