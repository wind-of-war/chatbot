import hashlib
import json
import time

import redis

from configs.settings import settings
from core.utils.language_detection import detect_language
from core.utils.query_translation import normalize_query_for_retrieval


class ResponseCache:
    _memory_store: dict[str, tuple[float, dict]] = {}

    def __init__(self) -> None:
        self.client = None
        try:
            self.client = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=0.3,
                socket_timeout=0.3,
                retry_on_timeout=False,
            )
        except Exception:
            self.client = None

    def _key(self, user_id: int, query: str) -> str:
        language = detect_language(query)
        normalized = normalize_query_for_retrieval(query, language)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"answer:{user_id}:{digest}"

    def get(self, user_id: int, query: str) -> dict | None:
        key = self._key(user_id=user_id, query=query)
        def _get_memory() -> dict | None:
            item = self._memory_store.get(key)
            if not item:
                return None
            expires_at, payload = item
            if expires_at < time.time():
                self._memory_store.pop(key, None)
                return None
            return payload

        if not self.client:
            return _get_memory()
        try:
            raw = self.client.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            return _get_memory()

    def set(self, user_id: int, query: str, value: dict) -> bool:
        key = self._key(user_id=user_id, query=query)
        def _set_memory() -> bool:
            self._memory_store[key] = (time.time() + settings.answer_cache_ttl_seconds, value)
            return True

        if not self.client:
            return _set_memory()
        try:
            self.client.setex(
                key,
                settings.answer_cache_ttl_seconds,
                json.dumps(value),
            )
            return True
        except Exception:
            return _set_memory()
