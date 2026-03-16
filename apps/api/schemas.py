from datetime import datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    status: str


class ChatRequest(BaseModel):
    question: str


class Citation(BaseModel):
    source: str
    section: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    snippet: str | None = None


class ChatResponse(BaseModel):
    answer: str
    tokens_used: int
    citations: list[Citation]
    confidence: float | None = None
    cached: bool = False


class UsageItem(BaseModel):
    query: str
    tokens: int
    cost: float
    timestamp: datetime


class UsageResponse(BaseModel):
    total_queries: int
    total_tokens: int
    total_cost: float
    items: list[UsageItem]


class DependencyStatus(BaseModel):
    name: str
    ok: bool
    detail: str | None = None


class ManagementOverview(BaseModel):
    app_env: str
    embedding_model: str
    embedding_local_files_only: bool
    qdrant_collection: str
    rate_limit_per_minute: int
    free_plan_daily_limit: int


class RAGConfigResponse(BaseModel):
    retrieval_top_k: int
    rerank_top_k: int
    cache_ttl_seconds: int


class RAGConfigUpdateRequest(BaseModel):
    retrieval_top_k: int | None = None
    rerank_top_k: int | None = None
    cache_ttl_seconds: int | None = None


class AgentsRunRequest(BaseModel):
    question: str


class JobPolicyResponse(BaseModel):
    autoretry_for: list[str]
    retry_backoff: bool
    retry_backoff_max: int
    retry_jitter: bool
    max_retries: int


class UserSummary(BaseModel):
    id: int
    email: str
    plan: str
    role: str
    status: str
    created_at: datetime


class UserUpdateRequest(BaseModel):
    plan: str | None = None
    role: str | None = None
    status: str | None = None


class UserPlanUpdateRequest(BaseModel):
    plan: str


class UserStatusUpdateRequest(BaseModel):
    status: str
