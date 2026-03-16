import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models

from configs.settings import settings


class QdrantService:
    _client: QdrantClient | None = None
    _enabled: bool | None = None

    def __init__(self) -> None:
        if self.__class__._enabled is None:
            self.__class__._client, self.__class__._enabled = self._build_client()
        self.client = self.__class__._client
        self.enabled = bool(self.__class__._enabled)

    def _build_client(self) -> tuple[QdrantClient | None, bool]:
        try:
            remote = QdrantClient(url=settings.qdrant_url, timeout=2.0)
            remote.get_collections()
            return remote, True
        except Exception:
            return None, False

    def _ensure_collection(self, vector_size: int) -> None:
        if not self.enabled or self.client is None:
            raise RuntimeError("Qdrant is unavailable")
        if self.client.collection_exists(settings.qdrant_collection):
            return
        self.client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=models.VectorParams(size=vector_size, distance=models.Distance.COSINE),
        )

    def upsert_documents(self, items: list[dict]) -> int:
        if not items:
            return 0
        if not self.enabled or self.client is None:
            raise RuntimeError("Qdrant is unavailable")

        vector_size = len(items[0]["vector"])
        self._ensure_collection(vector_size)

        points = []
        for item in items:
            points.append(
                models.PointStruct(
                    id=item.get("id") or str(uuid.uuid4()),
                    vector=item["vector"],
                    payload={
                        "source": item.get("source", "unknown"),
                        "section": item.get("section"),
                        "text": item.get("text", ""),
                        "language": item.get("language", "en"),
                        "page_start": item.get("page_start"),
                        "page_end": item.get("page_end"),
                    },
                )
            )

        self.client.upsert(collection_name=settings.qdrant_collection, points=points)
        return len(points)

    def search(self, query_vector: list[float], top_k: int = 8, query_language: str = "en") -> list[dict]:
        if not self.enabled or self.client is None:
            return []

        try:
            hits = self.client.search(
                collection_name=settings.qdrant_collection,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
            )
        except Exception:
            return []

        docs: list[dict] = []
        for hit in hits:
            payload = hit.payload or {}
            docs.append(
                {
                    "source": payload.get("source", "unknown"),
                    "section": payload.get("section"),
                    "text": payload.get("text", ""),
                    "language": payload.get("language", "en"),
                    "page_start": payload.get("page_start"),
                    "page_end": payload.get("page_end"),
                    "query_language": query_language,
                }
            )
        return docs
