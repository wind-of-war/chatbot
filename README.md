# gxp-ai-platform

Monorepo scaffold for a GxP AI platform using agent orchestration + multilingual RAG.

## Monorepo layout

- `apps/api`: FastAPI app (auth/chat/usage/health/jobs/admin/management/telegram)
- `apps/api/services`: business services (`auth_service`, `usage_service`, `chat_service`, `telegram_service`)
- `apps/worker`: Celery worker and task definitions
- `apps/bot`: Telegram polling bot process
- `core/agents`: language/query/retrieval/compliance/response agents + orchestrator graph
- `core/rag`: embeddings/retrieval/reranker/prompt
- `core/services`: vector store/cache/document store/embedding services
- `pipelines`: ingestion/indexing/faq generation jobs
- `infra`: dockerfiles, compose, nginx gateway
- `tests`: rag, agents, api tests
- `configs`: app settings + logging
- `data`: raw/processed/embeddings artifacts

## Multilingual RAG architecture

Pipeline:
- User query (VI/EN)
- `LanguageAgent`
- `QueryAgent` (VI stopword removal + synonym expansion)
- Multilingual embedding (`BAAI/bge-m3`)
- Vector search in Qdrant (auto fallback to local `data/qdrant_local` if Qdrant URL is unavailable)
- Reranker + compliance check
- Response in same language as user, citations preserved from source docs

## Production hardening included

1. Service boundaries in API
- Route layer only handles request/response.
- Auth/usage/chat/telegram logic in service layer.

2. Real Celery + Redis worker
- `apps/worker/celery_app.py`
- `apps/worker/tasks.py`
- `infra/docker-compose.yml` includes `worker` and `celery-beat`.

3. Multilingual cache
- `core/services/cache/redis_cache.py`
- Cache key normalized from multilingual query semantics.

4. Admin RBAC + user ID management
- `users` has `role` and `status`.
- `/management/*` requires admin token.
- Admin user APIs by ID: `/admin/users/*`.

5. Telegram integration
- Webhook endpoint for Telegram updates.
- Admin endpoints to set/delete/get webhook info.
- Optional polling bot process for VPS setups.

6. Retrieval and answer quality improvements
- Query expansion keeps the original VI/EN question and adds domain-aware variants.
- Hybrid retrieval and reranking score phrase match, term coverage, and cleanroom/regulatory keywords.
- Citations can include `page_start/page_end` so Telegram replies can show page-aware sources.

7. Subscription and quota controls
- Free plan can be limited per day (`FREE_PLAN_DAILY_LIMIT`, current deployment uses `5`).
- Pro plan supports Telegram Stars billing (`/plan`, `/upgrade`).
- Admin Telegram IDs can bypass quota and rate limits.

## Development workflow

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start stack:

```bash
docker compose -f infra/docker-compose.yml up --build
```

3. Run API locally:

```bash
uvicorn apps.api.main:app --reload
```

4. Start worker locally:

```bash
celery -A apps.worker.celery_app.celery_app worker -l info
```

Windows PowerShell quick start:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_api.ps1
powershell -ExecutionPolicy Bypass -File scripts/start_worker.ps1
powershell -ExecutionPolicy Bypass -File scripts/start_telegram_bot.ps1
```

Windows PowerShell health check:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/health_check.ps1 -AdminEmail "hiencdt2011@gmail.com" -AdminPassword "Admin@123456"
```

5. Run tests:

```bash
pytest -q
```

6. Preload embedding model cache (recommended before first run):

```bash
python scripts/preload_embedding_model.py --model BAAI/bge-m3
```

7. Update EU Pharmacopoeia knowledge base (licensed PDFs):

- Put European Pharmacopoeia PDFs into `data/raw/eu_pharmacopoeia` (supports nested folders).
- Run update:

```bash
bash scripts/update_eu_pharmacopoeia.sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/update_eu_pharmacopoeia.ps1
```

8. Update multi-source regulatory corpus (EU/UK + pharma/food standards):

- Source manifest: `data/sources/regulatory_docs_sources.json`
- Auto-download targets are stored under `data/raw/<category>/...`
- Manual upload targets (licensed/private docs):
  - `data/raw/uk_pharmacopoeia_manual`
  - `data/raw/vn_pharmacopoeia_manual`

Linux/VPS:

```bash
bash scripts/update_regulatory_corpus.sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/update_regulatory_corpus.ps1
```

Notes:
- The updater defaults to `FULL_REBUILD=true` for consistency (rebuild processed chunks + embeddings).
- For licensed content (e.g. full British Pharmacopoeia, full Dược điển Việt Nam), upload only legally obtained files.

## Telegram on VPS

Set these env vars in `.env`:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `TELEGRAM_WEBHOOK_URL` (example: `https://your-domain.com/integrations/telegram/webhook`)
- `OPENAI_API_KEY` (optional, enable natural multilingual answer generation)
- `OPENAI_MODEL` (default: `gpt-4o-mini`)
- `OLLAMA_ENABLED` / `OLLAMA_MODEL` (current VPS deployment uses local Ollama with `qwen2.5:3b`)
- `FREE_PLAN_DAILY_LIMIT`, `PRO_PLAN_DAILY_LIMIT`
- `TELEGRAM_STARS_ENABLED`, `TELEGRAM_PRO_PRICE_STARS`
- `TELEGRAM_ADMIN_USER_IDS`

Then:

1. Register/login as admin (`ADMIN_EMAILS`).
2. Call `POST /integrations/telegram/webhook/set` with admin token.
3. Send message to bot on Telegram.

Optional polling mode:

```bash
docker compose -f infra/docker-compose.yml --profile telegram-polling up telegram-bot
```

## VPS systemd (recommended)

1. Edit unit files for your server user/path:
- `infra/systemd/gxp-api.service`
- `infra/systemd/gxp-telegram-bot.service`

Default values use:
- user/group: `ubuntu`
- app dir: `/opt/gxp-ai-platform`
- venv: `/opt/gxp-ai-platform/.venv`

2. Install and start services:

```bash
chmod +x scripts/install_systemd_services.sh
./scripts/install_systemd_services.sh
```

3. Verify:

```bash
sudo systemctl status gxp-api --no-pager
sudo systemctl status gxp-telegram-bot --no-pager
sudo journalctl -u gxp-api -f
sudo journalctl -u gxp-telegram-bot -f
```

4. Monthly document auto-update (systemd timer):

```bash
chmod +x scripts/install_docs_update_timer.sh
./scripts/install_docs_update_timer.sh
```

Check timer:

```bash
sudo systemctl status gxp-docs-monthly.timer --no-pager
sudo systemctl list-timers --all | grep gxp-docs-monthly
sudo journalctl -u gxp-docs-monthly.service -f
```

5. Auto-update when new/updated files are copied to `data/raw`:

- `gxp-docs-watch.path` listens for changes under `/opt/gxp-ai-platform/data/raw`.
- It triggers `gxp-docs-watch.service`, which runs:
  - `scripts/run_incremental_update.sh`
  - Uses file lock (`flock`) to avoid overlapping jobs.
  - Runs update in incremental mode (`FULL_REBUILD=false`).

Check watcher:

```bash
sudo systemctl status gxp-docs-watch.path --no-pager
sudo systemctl status gxp-docs-watch.service --no-pager
sudo journalctl -u gxp-docs-watch.service -f
tail -f /opt/gxp-ai-platform/logs/docs_update_watcher.log
```

6. Weekly safe cleanup (logs/cache/old usage logs):

```bash
chmod +x scripts/install_weekly_cleanup.sh
./scripts/install_weekly_cleanup.sh
```

Check status:

```bash
sudo systemctl status gxp-cleanup-weekly.timer --no-pager
sudo systemctl list-timers --all | grep gxp-cleanup-weekly
sudo journalctl -u gxp-cleanup-weekly.service -f
```

Default retention:
- `usage_logs`: keep 90 days (`KEEP_USAGE_DAYS=90` in service file)
- `*.log` files: remove older than 7 days
- systemd journal: vacuum older than 14 days

## Endpoints

Core:
- `GET /health`
- `POST /auth/register`
- `POST /auth/login`
- `POST /chat`
- `GET /usage`

Jobs:
- `POST /jobs/{job_type}` (`ingestion`, `indexing`, `faq`)
- `GET /jobs/{task_id}`

Management (admin only):
- `GET /management/overview`
- `GET /management/dependencies`
- `GET /management/rag/config`
- `PATCH /management/rag/config`
- `GET /management/agents`
- `POST /management/agents/run`
- `GET /management/jobs/policy`

Admin users (admin only):
- `GET /admin/users`
- `GET /admin/users/{user_id}`
- `PATCH /admin/users/{user_id}`
- `PATCH /admin/users/{user_id}/plan`
- `PATCH /admin/users/{user_id}/status`

Telegram integration:
- `POST /integrations/telegram/webhook` (Telegram -> API)
- `GET /integrations/telegram/webhook/info` (admin)
- `POST /integrations/telegram/webhook/set` (admin)
- `POST /integrations/telegram/webhook/delete` (admin)
