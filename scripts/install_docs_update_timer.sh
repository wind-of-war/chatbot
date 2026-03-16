#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/4] Copy docs update unit files..."
sudo cp "$REPO_ROOT/infra/systemd/gxp-docs-monthly.service" /etc/systemd/system/gxp-docs-monthly.service
sudo cp "$REPO_ROOT/infra/systemd/gxp-docs-monthly.timer" /etc/systemd/system/gxp-docs-monthly.timer
sudo cp "$REPO_ROOT/infra/systemd/gxp-docs-watch.service" /etc/systemd/system/gxp-docs-watch.service
sudo cp "$REPO_ROOT/infra/systemd/gxp-docs-watch.path" /etc/systemd/system/gxp-docs-watch.path

echo "[2/4] Reload systemd daemon..."
sudo systemctl daemon-reload

echo "[3/4] Enable/start timers and watcher..."
sudo systemctl enable gxp-docs-monthly.timer
sudo systemctl restart gxp-docs-monthly.timer
sudo systemctl enable gxp-docs-watch.path
sudo systemctl restart gxp-docs-watch.path

echo "[4/4] Trigger one immediate run (optional but recommended)..."
sudo systemctl start gxp-docs-monthly.service

echo ""
echo "Done. Check status with:"
echo "  sudo systemctl status gxp-docs-monthly.timer --no-pager"
echo "  sudo systemctl list-timers --all | grep gxp-docs-monthly"
echo "  sudo systemctl status gxp-docs-watch.path --no-pager"
echo "  sudo systemctl status gxp-docs-watch.service --no-pager"
echo "  sudo journalctl -u gxp-docs-monthly.service -f"
echo "  sudo journalctl -u gxp-docs-watch.service -f"
echo "  tail -f /opt/gxp-ai-platform/logs/docs_update_watcher.log"
