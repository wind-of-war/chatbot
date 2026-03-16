from core.utils.retrieval_scoring import lexical_score


def rerank(query: str, docs: list[dict], top_k: int = 5) -> list[dict]:
    ranked = sorted(
        docs,
        key=lambda d: lexical_score(
            query=query,
            text=d.get("text") or "",
            source=d.get("source") or "",
            section=d.get("section") or "",
        ),
        reverse=True,
    )
    return ranked[:top_k]
