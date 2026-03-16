from core.rag.embeddings.model import embed_query
from core.rag.retrieval.hybrid_search import hybrid_search
from core.rag.retrieval.vector_search import vector_search
from core.runtime.rag_runtime import rag_runtime_config
from core.services.cache.redis_cache import RedisCache


class RetrievalAgent:
    def __init__(self) -> None:
        self.cache = RedisCache()

    def run(self, state: dict) -> dict:
        runtime = rag_runtime_config.get()
        retrieval_top_k = runtime["retrieval_top_k"]
        cache_ttl_seconds = runtime["cache_ttl_seconds"]

        question = state["question"]
        language = state.get("language", "en")
        retrieval_queries = state.get("retrieval_queries") or [question]

        cached_docs = self.cache.get(question)
        if cached_docs:
            state["retrieved_docs"] = cached_docs
            return state

        merged_hits: list[dict] = []
        seen = set()

        for q in retrieval_queries:
            vector = embed_query(q)
            hits = vector_search(vector, top_k=retrieval_top_k, query_language=language)
            ranked = hybrid_search(q, hits, top_k=retrieval_top_k)

            for item in ranked:
                key = (item.get("source"), item.get("section"), item.get("text"))
                if key in seen:
                    continue
                seen.add(key)
                merged_hits.append(item)

        docs = hybrid_search(question, merged_hits, top_k=retrieval_top_k)
        state["retrieved_docs"] = docs
        self.cache.set(question, docs, ttl_seconds=cache_ttl_seconds)
        return state
