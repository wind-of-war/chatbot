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
from core.services.vector_store.qdrant_service import QdrantService


router = APIRouter(prefix="/management", tags=["management"], dependencies=[Depends(require_admin)])


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
