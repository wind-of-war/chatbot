from apps.api.dependencies.container import container
from apps.api.models import User
from apps.api.schemas import Citation
from apps.api.services.usage_service import append_usage, estimate_cost, estimate_tokens
from configs.settings import settings
from core.services.cache.response_cache import ResponseCache
from core.services.web_search.internet_search_service import InternetSearchService
from core.utils.language_detection import detect_language


response_cache = ResponseCache()
internet_search = InternetSearchService()


def _append_legal_disclaimer(answer: str, question: str) -> str:
    if not settings.legal_disclaimer_enabled:
        return answer
    language = detect_language(question)
    disclaimer = settings.legal_disclaimer_vi if language == "vi" else settings.legal_disclaimer_en
    suffix = f"\n\n{disclaimer.strip()}"
    return answer if suffix in answer else f"{answer.rstrip()}{suffix}"


def ask_question_for_user(db, user: User, question: str) -> dict:
    cached = response_cache.get(user_id=user.id, query=question)
    if cached:
        answer = cached.get("answer", "")
        citations = cached.get("citations", [])
        confidence = float(cached.get("confidence", 0.0))
    else:
        state = container.agent_graph.run(question)
        state = _maybe_retry_with_internet(question=question, state=state)
        answer = state.get("answer", "")
        citations = [Citation(**c).model_dump() for c in state.get("citations", [])]
        confidence = float(state.get("confidence", 0.0))
        answer = _append_legal_disclaimer(answer=answer, question=question)
        response_cache.set(
            user_id=user.id,
            query=question,
            value={"answer": answer, "citations": citations, "confidence": confidence},
        )
    if cached:
        answer = _append_legal_disclaimer(answer=answer, question=question)

    tokens = estimate_tokens(question, answer)
    cost = estimate_cost(tokens)
    append_usage(db=db, user_id=user.id, query=question, tokens=tokens, cost=cost)

    return {
        "answer": answer,
        "tokens_used": tokens,
        "citations": citations,
        "confidence": confidence,
        "cached": bool(cached),
    }


def _maybe_retry_with_internet(question: str, state: dict) -> dict:
    if not internet_search.enabled():
        return state

    current_confidence = float(state.get("confidence", 0.0))
    current_docs = state.get("validated_docs", []) or []
    if current_docs and current_confidence >= settings.internet_fallback_min_confidence:
        return state

    language = state.get("language", "en")
    web_docs = internet_search.search(question=question, language=language)
    if not web_docs:
        return state

    retried_state = dict(state)
    retried_state["validated_docs"] = (current_docs + web_docs)[: max(4, len(current_docs) + len(web_docs))]
    retried_state["web_fallback_used"] = True
    retried_state = container.agent_graph.response_agent.run(retried_state)

    retried_confidence = float(retried_state.get("confidence", 0.0))
    if not current_docs:
        return retried_state
    return retried_state if retried_confidence >= current_confidence else state
