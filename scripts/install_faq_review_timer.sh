#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[1/4] Copy FAQ review timer unit files..."
sudo cp "$REPO_ROOT/infra/systemd/gxp-faq-review-daily.service" /etc/systemd/system/gxp-faq-review-daily.service
sudo cp "$REPO_ROOT/infra/systemd/gxp-faq-review-daily.timer" /etc/systemd/system/gxp-faq-review-daily.timer

echo "[2/4] Reload systemd daemon..."
sudo systemctl daemon-reload

echo "[3/4] Enable and start timer..."
sudo systemctl enable gxp-faq-review-daily.timer
sudo systemctl restart gxp-faq-review-daily.timer

echo "[4/4] Trigger one immediate run (optional)..."
sudo systemctl start gxp-faq-review-daily.service

echo ""
echo "Done. Check status with:"
echo "  sudo systemctl status gxp-faq-review-daily.timer --no-pager"
echo "  sudo systemctl list-timers --all | grep gxp-faq-review-daily"
echo "  sudo journalctl -u gxp-faq-review-daily.service -f"
echo "  tail -f /opt/gxp-ai-platform/logs/faq_review_daily.log"
