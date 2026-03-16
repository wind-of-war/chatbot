#!/usr/bin/env bash
set -euo pipefail
celery -A apps.worker.celery_app.celery_app worker -l info
