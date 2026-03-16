from core.rag.reranker.reranker import rerank
from core.runtime.rag_runtime import rag_runtime_config


class ComplianceAgent:
    def run(self, state: dict) -> dict:
        runtime = rag_runtime_config.get()
        rerank_top_k = runtime["rerank_top_k"]

        question = state["question"]
        docs = state.get("retrieved_docs", [])
        state["validated_docs"] = rerank(question, docs, top_k=rerank_top_k)
        state["compliance_flag"] = "ok" if docs else "insufficient_context"
        return state
