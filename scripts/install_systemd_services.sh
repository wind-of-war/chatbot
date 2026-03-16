#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/4] Copy systemd unit files..."
sudo cp "$REPO_ROOT/infra/systemd/gxp-api.service" /etc/systemd/system/gxp-api.service
sudo cp "$REPO_ROOT/infra/systemd/gxp-telegram-bot.service" /etc/systemd/system/gxp-telegram-bot.service

echo "[2/4] Reload systemd daemon..."
sudo systemctl daemon-reload

echo "[3/4] Enable services..."
sudo systemctl enable gxp-api
sudo systemctl enable gxp-telegram-bot

echo "[4/4] Start/restart services..."
sudo systemctl restart gxp-api
sudo systemctl restart gxp-telegram-bot

echo ""
echo "Done. Check status with:"
echo "  sudo systemctl status gxp-api --no-pager"
echo "  sudo systemctl status gxp-telegram-bot --no-pager"
echo ""
echo "Follow logs:"
echo "  sudo journalctl -u gxp-api -f"
echo "  sudo journalctl -u gxp-telegram-bot -f"
