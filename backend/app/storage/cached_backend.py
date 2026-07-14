"""Read-through cache decorator for any StorageBackend (v100, optional Redis).

Wraps an inner backend: ``read_list`` is served from Redis when warm (short TTL),
and every write (``append`` / ``write_list``) invalidates that collection's key.
**Fail-open by design** — any Redis error falls straight through to the inner
backend, so the cache can never break reads or writes. If Redis is unreachable at
startup, the app simply runs uncached.
"""

from __future__ import annotations

import json
from typing import Any, Callable

_PREFIX = "evolveagent:coll:"


class CachedBackend:
    def __init__(self, inner, redis_client, ttl_seconds: int = 30):
        self.inner = inner
        self.redis = redis_client
        self.ttl = ttl_seconds

    @staticmethod
    def key(filename: str) -> str:
        return f"{_PREFIX}{filename}"

    def ensure(self, filename: str) -> None:
        self.inner.ensure(filename)

    def read_list(self, filename: str) -> list[dict[str, Any]]:
        k = self.key(filename)
        try:
            cached = self.redis.get(k)
            if cached is not None:
                data = json.loads(cached)
                if isinstance(data, list):
                    return data
        except Exception:
            pass  # fail-open: treat as cache miss
        data = self.inner.read_list(filename)
        try:
            self.redis.setex(k, self.ttl, json.dumps(data))
        except Exception:
            pass
        return data

    def _invalidate(self, filename: str) -> None:
        try:
            self.redis.delete(self.key(filename))
        except Exception:
            pass

    def append(self, filename: str, item: dict[str, Any]) -> None:
        self.inner.append(filename, item)
        self._invalidate(filename)

    def write_list(self, filename: str, items: list[dict[str, Any]]) -> None:
        self.inner.write_list(filename, items)
        self._invalidate(filename)

    def update_list(self, filename: str, mutator: Callable[[list[dict[str, Any]]], Any]) -> Any:
        result = self.inner.update_list(filename, mutator)
        self._invalidate(filename)
        return result

    def stats(self) -> dict[str, Any]:
        stats = self.inner.stats()
        stats["cache"] = "redis"
        return stats


def maybe_wrap_with_redis(inner, redis_url: str | None, ttl_seconds: int = 30):
    """Wrap ``inner`` with a Redis cache if the URL is set AND Redis responds to
    a ping. Otherwise return ``inner`` unchanged. Never raises."""
    if not redis_url:
        return inner
    try:
        import redis as _redis
        client = _redis.Redis.from_url(redis_url, socket_connect_timeout=1, socket_timeout=1)
        client.ping()
        return CachedBackend(inner, client, ttl_seconds)
    except Exception:
        return inner
