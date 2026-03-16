import hashlib
import json

import redis

from core.utils.language_detection import detect_language
from core.utils.query_translation import normalize_query_for_retrieval


class RedisCache:
    def __init__(self) -> None:
        self.client = None
        try:
            from configs.settings import settings

            self.client = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=0.3,
                socket_timeout=0.3,
                retry_on_timeout=False,
            )
        except Exception:
            self.client = None

    def _key(self, query: str) -> str:
        language = detect_language(query)
        normalized = normalize_query_for_retrieval(query, language)
        digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        return f"rag:{digest}"

    def get(self, query: str):
        if not self.client:
            return None
        key = self._key(query)
        try:
            raw = self.client.get(key)
            return json.loads(raw) if raw else None
        except Exception:
            return None

    def set(self, query: str, value, ttl_seconds: int = 300):
        if not self.client:
            return False
        key = self._key(query)
        try:
            self.client.setex(key, ttl_seconds, json.dumps(value))
            return True
        except Exception:
            return False
