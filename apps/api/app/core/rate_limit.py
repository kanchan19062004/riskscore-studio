"""Fixed-window rate limiter.

Auth endpoints fail closed: if Redis is down we reject, rather than opening a
brute-force window. Scoring fails open: a limiter outage must not freeze
decisions (same reason the score cache fails open).
"""

from dataclasses import dataclass
from time import monotonic
from typing import Protocol

from app.core.config import settings


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after: int


class RateLimiter(Protocol):
    def hit(self, key: str, *, limit: int, window_seconds: int) -> RateLimitResult: ...


class MemoryRateLimiter:
    """In-memory fixed window. Used in tests; one process only."""

    def __init__(self) -> None:
        self._windows: dict[str, tuple[int, float]] = {}

    def hit(self, key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
        now = monotonic()
        count, expires_at = self._windows.get(key, (0, now + window_seconds))
        if now >= expires_at:
            count, expires_at = 0, now + window_seconds
        count += 1
        self._windows[key] = (count, expires_at)
        retry_after = max(1, int(expires_at - now) + 1)
        remaining = max(0, limit - count)
        return RateLimitResult(
            allowed=count <= limit,
            limit=limit,
            remaining=remaining,
            retry_after=retry_after,
        )


class RedisRateLimiter:
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

    def hit(self, key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
        conn = self._conn()
        pipe = conn.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds, nx=True)
        pipe.ttl(key)
        count, _, ttl = pipe.execute()
        if ttl < 0:
            conn.expire(key, window_seconds)
            ttl = window_seconds
        remaining = max(0, limit - int(count))
        return RateLimitResult(
            allowed=int(count) <= limit,
            limit=limit,
            remaining=remaining,
            retry_after=max(1, int(ttl)),
        )


class BrokenRateLimiter:
    """Test double: every hit raises, so fail-open / fail-closed can be asserted."""

    def hit(self, key: str, *, limit: int, window_seconds: int) -> RateLimitResult:
        raise ConnectionError("rate limiter backend unavailable")


_backend: RateLimiter | None = None


def get_rate_limiter() -> RateLimiter:
    global _backend
    if _backend is None:
        _backend = RedisRateLimiter(settings.REDIS_URL)
    return _backend


def set_rate_limiter(backend: RateLimiter | None) -> None:
    global _backend
    _backend = backend


def hit_limit(
    key: str,
    *,
    limit: int,
    window_seconds: int,
    fail_closed: bool,
) -> RateLimitResult:
    try:
        return get_rate_limiter().hit(key, limit=limit, window_seconds=window_seconds)
    except Exception:
        if fail_closed:
            return RateLimitResult(allowed=False, limit=limit, remaining=0, retry_after=window_seconds)
        return RateLimitResult(allowed=True, limit=limit, remaining=limit, retry_after=0)
