#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_NAME="${REMOTE_NAME:-origin}"
BRANCH_NAME="${BRANCH_NAME:-main}"

cd "$REPO_ROOT"

echo "[1/5] Verifying git repository..."
git rev-parse --is-inside-work-tree >/dev/null

echo "[2/5] Fetching latest code from ${REMOTE_NAME}/${BRANCH_NAME}..."
git fetch "$REMOTE_NAME"

LOCAL_SHA="$(git rev-parse HEAD)"
REMOTE_SHA="$(git rev-parse "${REMOTE_NAME}/${BRANCH_NAME}")"

if [[ "$LOCAL_SHA" == "$REMOTE_SHA" ]]; then
  echo "Already up to date at $LOCAL_SHA"
else
  echo "[3/5] Resetting tracked files to ${REMOTE_NAME}/${BRANCH_NAME}..."
  git reset --hard "${REMOTE_NAME}/${BRANCH_NAME}"
fi

echo "[4/5] Restarting app services..."
sudo systemctl restart gxp-api
sudo systemctl restart gxp-telegram-bot

echo "[5/5] Current status"
git rev-parse HEAD
sudo systemctl --no-pager --full status gxp-api gxp-telegram-bot | sed -n '1,40p'
