#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/opt/gxp-ai-platform"
LOG_DIR="$REPO_ROOT/logs"
DB_PATH="$REPO_ROOT/gxp_platform.db"
KEEP_USAGE_DAYS="${KEEP_USAGE_DAYS:-90}"

mkdir -p "$LOG_DIR"

echo "[CLEANUP] start $(date -u +%F_%T)"
echo "[CLEANUP] repo=$REPO_ROOT keep_usage_days=$KEEP_USAGE_DAYS"

if [[ -d "$LOG_DIR" ]]; then
  echo "[CLEANUP] logs size before: $(du -sh "$LOG_DIR" | awk '{print $1}')"
  find "$LOG_DIR" -type f -name "*.log" -mtime +7 -print -delete || true
  echo "[CLEANUP] logs size after: $(du -sh "$LOG_DIR" | awk '{print $1}')"
fi

echo "[CLEANUP] remove root *.log older than 7 days"
find "$REPO_ROOT" -maxdepth 1 -type f -name "*.log" -mtime +7 -print -delete || true

echo "[CLEANUP] clean pycache/test cache"
find "$REPO_ROOT" -type d -name "__pycache__" -prune -exec rm -rf {} + || true
find "$REPO_ROOT" -type d -name ".pytest_cache" -prune -exec rm -rf {} + || true

if [[ -f "$DB_PATH" ]]; then
  echo "[CLEANUP] prune usage_logs older than $KEEP_USAGE_DAYS days"
  "$REPO_ROOT/.venv/bin/python" - <<PY
import sqlite3
from datetime import datetime, timedelta
db = sqlite3.connect(r"$DB_PATH")
cur = db.cursor()
cutoff = (datetime.utcnow() - timedelta(days=int("$KEEP_USAGE_DAYS"))).strftime("%Y-%m-%d %H:%M:%S")
cur.execute("DELETE FROM usage_logs WHERE timestamp < ?", (cutoff,))
deleted = cur.rowcount
db.commit()
cur.execute("VACUUM")
db.commit()
db.close()
print(f"[CLEANUP] usage_logs deleted={deleted}")
PY
fi

echo "[CLEANUP] vacuum journal logs older than 14d"
sudo journalctl --vacuum-time=14d || true

echo "[CLEANUP] done $(date -u +%F_%T)"
