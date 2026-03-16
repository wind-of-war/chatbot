from core.utils.retrieval_scoring import lexical_score


def hybrid_search(query: str, vector_hits: list[dict], top_k: int = 8) -> list[dict]:
    scored = []
    for item in vector_hits:
        score = lexical_score(
            query=query,
            text=item.get("text") or "",
            source=item.get("source") or "",
            section=item.get("section") or "",
        )
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored[:top_k]]
