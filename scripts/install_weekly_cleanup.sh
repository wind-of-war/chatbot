#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/4] Copy cleanup unit files..."
sudo cp "$REPO_ROOT/infra/systemd/gxp-cleanup-weekly.service" /etc/systemd/system/gxp-cleanup-weekly.service
sudo cp "$REPO_ROOT/infra/systemd/gxp-cleanup-weekly.timer" /etc/systemd/system/gxp-cleanup-weekly.timer

echo "[2/4] Reload systemd daemon..."
sudo systemctl daemon-reload

echo "[3/4] Enable/start weekly timer..."
sudo systemctl enable gxp-cleanup-weekly.timer
sudo systemctl restart gxp-cleanup-weekly.timer

echo "[4/4] Trigger one cleanup run now..."
sudo systemctl start gxp-cleanup-weekly.service

echo ""
echo "Done. Check status with:"
echo "  sudo systemctl status gxp-cleanup-weekly.timer --no-pager"
echo "  sudo systemctl list-timers --all | grep gxp-cleanup-weekly"
echo "  sudo journalctl -u gxp-cleanup-weekly.service -f"
