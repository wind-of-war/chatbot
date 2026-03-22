#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$REPO_ROOT/logs"
mkdir -p "$LOG_DIR"

cd "$REPO_ROOT"

/usr/bin/flock -n /tmp/gxp-mini-training-agent.lock \
  "$REPO_ROOT/.venv/bin/python" "$REPO_ROOT/scripts/mini_training_agent.py" \
  --limit 20 \
  >> "$LOG_DIR/mini_training_agent.log" 2>&1 || true
