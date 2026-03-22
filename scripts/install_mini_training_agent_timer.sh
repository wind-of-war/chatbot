#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/4] Copy mini training agent unit files..."
sudo cp "$REPO_ROOT/infra/systemd/gxp-mini-training-agent.service" /etc/systemd/system/gxp-mini-training-agent.service
sudo cp "$REPO_ROOT/infra/systemd/gxp-mini-training-agent.timer" /etc/systemd/system/gxp-mini-training-agent.timer

echo "[2/4] Reload systemd daemon..."
sudo systemctl daemon-reload

echo "[3/4] Enable and start timer..."
sudo systemctl enable gxp-mini-training-agent.timer
sudo systemctl restart gxp-mini-training-agent.timer

echo "[4/4] Trigger one immediate run (optional)..."
sudo systemctl start gxp-mini-training-agent.service

echo ""
echo "Done. Check status with:"
echo "  sudo systemctl status gxp-mini-training-agent.timer --no-pager"
echo "  sudo systemctl list-timers --all | grep gxp-mini-training-agent"
echo "  sudo journalctl -u gxp-mini-training-agent.service -f"
echo "  tail -f /opt/gxp-ai-platform/logs/mini_training_agent.log"
