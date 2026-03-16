import hashlib
import logging
from threading import Lock

from configs.settings import settings


logger = logging.getLogger(__name__)


class Embedder:
    _model = None
    _lock = Lock()

    def __init__(self) -> None:
        self.model_name = settings.embedding_model

    def _load_model(self):
        with self._lock:
            if self.__class__._model is not None:
                return self.__class__._model

            try:
                from sentence_transformers import SentenceTransformer

                model_source = self.model_name
                if settings.embedding_local_files_only:
                    from huggingface_hub import snapshot_download

                    model_source = snapshot_download(repo_id=self.model_name, local_files_only=True)

                self.__class__._model = SentenceTransformer(
                    model_source,
                    local_files_only=settings.embedding_local_files_only,
                )
                logger.info("Loaded embedding model: %s", self.model_name)
            except Exception as exc:
                logger.warning("Falling back to hash embedding, model load failed: %s", exc)
                self.__class__._model = False
            return self.__class__._model

    def _hash_embed(self, text: str, dimensions: int = 1024) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        vector = [b / 255.0 for b in digest]
        return (vector * ((dimensions // len(vector)) + 1))[:dimensions]

    def embed(self, text: str) -> list[float]:
        model = self._load_model()
        if model is False:
            return self._hash_embed(text)

        vector = model.encode(text, normalize_embeddings=True)
        return vector.tolist() if hasattr(vector, "tolist") else list(vector)

    def embed_many(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        if not texts:
            return []
        model = self._load_model()
        if model is False:
            return [self._hash_embed(t) for t in texts]

        vectors = model.encode(texts, normalize_embeddings=True, batch_size=batch_size)
        if hasattr(vectors, "tolist"):
            vectors = vectors.tolist()
        return [list(v) for v in vectors]
