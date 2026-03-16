import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from apps.api import models  # noqa: F401
from apps.api.database import Base, engine
from apps.api.database_migrations import ensure_subscription_table, ensure_telegram_link_table, ensure_user_schema_columns
from apps.api.routes.admin_users import router as admin_users_router
from apps.api.routes.auth import router as auth_router
from apps.api.routes.chat import router as chat_router
from apps.api.routes.health import router as health_router
from apps.api.routes.jobs import router as jobs_router
from apps.api.routes.management import router as management_router
from apps.api.routes.telegram_integration import admin_router as telegram_admin_router
from apps.api.routes.telegram_integration import router as telegram_router
from apps.api.routes.usage import router as usage_router


app = FastAPI(title="GxP AI Platform API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    started = time.time()
    response = await call_next(request)
    ms = round((time.time() - started) * 1000, 2)
    print(f"[{request.method}] {request.url.path} -> {response.status_code} ({ms} ms)")
    return response


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_user_schema_columns(engine)
    ensure_telegram_link_table(engine)
    ensure_subscription_table(engine)


app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(usage_router)
app.include_router(jobs_router)
app.include_router(management_router)
app.include_router(admin_users_router)
app.include_router(telegram_router)
app.include_router(telegram_admin_router)
