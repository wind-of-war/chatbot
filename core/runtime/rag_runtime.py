from threading import Lock


class RAGRuntimeConfig:
    def __init__(self) -> None:
        self._lock = Lock()
        self._config = {
            "retrieval_top_k": 8,
            "rerank_top_k": 4,
            "cache_ttl_seconds": 300,
        }

    def get(self) -> dict:
        with self._lock:
            return dict(self._config)

    def update(self, updates: dict) -> dict:
        with self._lock:
            for key, value in updates.items():
                if value is not None:
                    self._config[key] = int(value)
            return dict(self._config)


rag_runtime_config = RAGRuntimeConfig()
