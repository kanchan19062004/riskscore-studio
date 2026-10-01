"""Score cache. Redis in production; an in-memory backend in tests.

If Redis is down, get/set become no-ops (fail open): scoring still works, just
without a cache. A 500 because the cache is sad would be worse than a slower score.
"""

from typing import Protocol

from app.core.config import settings


class CacheBackend(Protocol):
    def get(self, key: str) -> str | None: ...
    def setex(self, key: str, seconds: int, value: str) -> None: ...
    def ping(self) -> bool: ...


class MemoryCache:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.store.get(key)

    def setex(self, key: str, seconds: int, value: str) -> None:
        self.store[key] = value

    def ping(self) -> bool:
        return True


class RedisCache:
    def __init__(self, url: str) -> None:
        self._url = url
        self._client = None

    def _conn(self):
        if self._client is None:
            from redis import Redis

            self._client = Redis.from_url(
                self._url, decode_responses=True, socket_connect_timeout=0.4
            )
        return self._client

    def get(self, key: str) -> str | None:
        try:
            return self._conn().get(key)
        except Exception:
            self._client = None
            return None

    def setex(self, key: str, seconds: int, value: str) -> None:
        try:
            self._conn().setex(key, seconds, value)
        except Exception:
            self._client = None

    def ping(self) -> bool:
        try:
            return bool(self._conn().ping())
        except Exception:
            self._client = None
            return False


_backend: CacheBackend | None = None


def get_cache() -> CacheBackend:
    global _backend
    if _backend is None:
        _backend = RedisCache(settings.REDIS_URL)
    return _backend


def set_cache(backend: CacheBackend | None) -> None:
    global _backend
    _backend = backend
