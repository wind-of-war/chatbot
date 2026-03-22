from collections import Counter

from fastapi import APIRouter, Depends

from apps.api.dependencies.container import container
from apps.api.schemas import (
    AgentsRunRequest,
    DependencyStatus,
    JobPolicyResponse,
    ManagementOverview,
    RAGConfigResponse,
    RAGConfigUpdateRequest,
)
from apps.api.services.auth_service import require_admin
from apps.worker.tasks import RETRY_POLICY
from configs.settings import settings
from core.runtime.rag_runtime import rag_runtime_config
from core.services.intent.intent_router import IntentRouter
from core.services.monitoring.answer_review_log import load_answer_review_events
from core.services.monitoring.training_report import load_mini_training_report
from core.services.vector_store.qdrant_service import QdrantService


router = APIRouter(prefix="/management", tags=["management"], dependencies=[Depends(require_admin)])
intent_router = IntentRouter()


@router.get("/overview", response_model=ManagementOverview)
def management_overview():
    return ManagementOverview(
        app_env=settings.app_env,
        embedding_model=settings.embedding_model,
        embedding_local_files_only=settings.embedding_local_files_only,
        qdrant_collection=settings.qdrant_collection,
        rate_limit_per_minute=settings.default_rate_limit_per_minute,
        free_plan_daily_limit=settings.free_plan_daily_limit,
    )


@router.get("/dependencies", response_model=list[DependencyStatus])
def dependency_status():
    statuses: list[DependencyStatus] = []

    try:
        redis_ok = bool(container.cache.client and container.cache.client.ping())
        statuses.append(DependencyStatus(name="redis", ok=redis_ok, detail=None if redis_ok else "ping failed"))
    except Exception as exc:
        statuses.append(DependencyStatus(name="redis", ok=False, detail=str(exc)))

    try:
        collections = QdrantService().client.get_collections()
        count = len(collections.collections)
        statuses.append(DependencyStatus(name="qdrant", ok=True, detail=f"collections={count}"))
    except Exception as exc:
        statuses.append(DependencyStatus(name="qdrant", ok=False, detail=str(exc)))

    return statuses


@router.get("/rag/config", response_model=RAGConfigResponse)
def get_rag_config():
    return RAGConfigResponse(**rag_runtime_config.get())


@router.patch("/rag/config", response_model=RAGConfigResponse)
def update_rag_config(payload: RAGConfigUpdateRequest):
    updates = payload.model_dump(exclude_none=True)
    updated = rag_runtime_config.update(updates)
    return RAGConfigResponse(**updated)


@router.get("/agents")
def get_agents_info():
    return {
        "entrypoint": "language_agent",
        "nodes": [
            "language_agent",
            "query_agent",
            "retrieval_agent",
            "compliance_agent",
            "response_agent",
        ],
    }


@router.post("/agents/run")
def run_agents(payload: AgentsRunRequest):
    state = container.agent_graph.run(payload.question)
    return {
        "language": state.get("language"),
        "question": state.get("question"),
        "retrieval_queries": state.get("retrieval_queries"),
        "retrieved_docs_count": len(state.get("retrieved_docs", [])),
        "validated_docs_count": len(state.get("validated_docs", [])),
        "compliance_flag": state.get("compliance_flag"),
        "answer": state.get("answer"),
        "citations": state.get("citations", []),
    }


@router.get("/jobs/policy", response_model=JobPolicyResponse)
def get_jobs_policy():
    retry_kwargs = RETRY_POLICY.get("retry_kwargs", {})
    return JobPolicyResponse(
        autoretry_for=[exc.__name__ for exc in RETRY_POLICY.get("autoretry_for", ())],
        retry_backoff=bool(RETRY_POLICY.get("retry_backoff", False)),
        retry_backoff_max=int(RETRY_POLICY.get("retry_backoff_max", 0)),
        retry_jitter=bool(RETRY_POLICY.get("retry_jitter", False)),
        max_retries=int(retry_kwargs.get("max_retries", 0)),
    )


@router.get("/answers/review")
def get_answer_review_feed(limit: int = 50):
    safe_limit = max(1, min(limit, 200))
    return {
        "items": load_answer_review_events(limit=safe_limit),
        "slow_threshold_seconds": settings.answer_review_slow_seconds,
        "low_confidence_threshold": settings.answer_review_low_confidence,
    }


@router.get("/answers/review/summary")
def get_answer_review_summary(limit: int = 500):
    safe_limit = max(1, min(limit, 2000))
    items = load_answer_review_events(limit=safe_limit)
    intent_counts: Counter[str] = Counter()
    mode_counts: Counter[str] = Counter()
    slow = 0
    low_conf = 0
    web_fallback = 0

    for item in items:
        question = item.get("question", "")
        intent_counts[intent_router.classify(question)] += 1
        mode_counts[item.get("answer_mode", "unknown")] += 1
        if float(item.get("elapsed_seconds", 0.0)) >= settings.answer_review_slow_seconds:
            slow += 1
        if float(item.get("confidence", 1.0)) < settings.answer_review_low_confidence:
            low_conf += 1
        if bool(item.get("web_fallback_used", False)):
            web_fallback += 1

    return {
        "total_items": len(items),
        "slow_items": slow,
        "low_confidence_items": low_conf,
        "web_fallback_items": web_fallback,
        "top_intents": intent_counts.most_common(10),
        "answer_modes": mode_counts.most_common(10),
        "slow_threshold_seconds": settings.answer_review_slow_seconds,
        "low_confidence_threshold": settings.answer_review_low_confidence,
    }


@router.get("/answers/training-report")
def get_mini_training_report(limit: int = 50):
    safe_limit = max(1, min(limit, 500))
    payload = load_mini_training_report()
    return {
        "summary": payload.get("summary"),
        "items": (payload.get("items") or [])[:safe_limit],
    }
