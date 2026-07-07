"""Redis read-through cache tests — use a fake in-memory Redis client so they run
everywhere (no Redis needed). Fail-open behavior is asserted explicitly."""

import json
import time

from app.storage.cached_backend import CachedBackend, maybe_wrap_with_redis
from app.storage.json_backend import JsonBackend


class FakeRedis:
    def __init__(self):
        self.store: dict[str, tuple[float, str]] = {}
        self.gets = 0
        self.sets = 0

    def get(self, k):
        self.gets += 1
        v = self.store.get(k)
        if v is None or v[0] < time.time():
            return None
        return v[1]

    def setex(self, k, ttl, val):
        self.sets += 1
        self.store[k] = (time.time() + ttl, val)

    def delete(self, k):
        self.store.pop(k, None)


class BrokenRedis:
    def get(self, k): raise ConnectionError("down")
    def setex(self, k, ttl, val): raise ConnectionError("down")
    def delete(self, k): raise ConnectionError("down")


def test_read_through_and_cache_hit(tmp_path):
    inner = JsonBackend(str(tmp_path))
    fake = FakeRedis()
    b = CachedBackend(inner, fake, ttl_seconds=30)
    b.write_list("a.json", [{"x": 1}])
    first = b.read_list("a.json")     # miss -> fills cache
    second = b.read_list("a.json")    # hit -> served from cache
    assert first == second == [{"x": 1}]
    assert fake.sets >= 1
    assert json.loads(fake.store[CachedBackend.key("a.json")][1]) == [{"x": 1}]


def test_writes_invalidate(tmp_path):
    inner = JsonBackend(str(tmp_path))
    fake = FakeRedis()
    b = CachedBackend(inner, fake, ttl_seconds=300)
    b.write_list("a.json", [{"x": 1}])
    assert b.read_list("a.json") == [{"x": 1}]      # cached
    b.append("a.json", {"x": 2})                     # invalidates
    assert b.read_list("a.json") == [{"x": 1}, {"x": 2}]  # fresh, not stale
    b.write_list("a.json", [])                       # invalidates again
    assert b.read_list("a.json") == []


def test_fail_open_on_broken_redis(tmp_path):
    inner = JsonBackend(str(tmp_path))
    b = CachedBackend(inner, BrokenRedis())
    b.write_list("a.json", [{"ok": True}])           # write survives redis errors
    assert b.read_list("a.json") == [{"ok": True}]   # read falls through


def test_stats_reports_cache(tmp_path):
    b = CachedBackend(JsonBackend(str(tmp_path)), FakeRedis())
    b.write_list("a.json", [{"x": 1}])
    st = b.stats()
    assert st["kind"] == "json" and st["cache"] == "redis"


def test_maybe_wrap_returns_inner_without_url(tmp_path):
    inner = JsonBackend(str(tmp_path))
    assert maybe_wrap_with_redis(inner, None) is inner
    # unreachable redis -> inner unchanged (never raises)
    assert maybe_wrap_with_redis(inner, "redis://127.0.0.1:1/0") is inner


def test_storage_service_unwraps_cache_for_kind(tmp_path):
    from app.services.storage_service import StorageService
    inner = JsonBackend(str(tmp_path))
    s = StorageService(data_dir=str(tmp_path), backend=CachedBackend(inner, FakeRedis()))
    assert s.backend_kind() == "json"
    st = s.status()
    assert st["cache"] == "redis"
