from core.services.embedding_service.embedder import Embedder


def embed_query(text: str) -> list[float]:
    return Embedder().embed(text)
