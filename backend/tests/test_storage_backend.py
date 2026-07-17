"""Storage abstraction tests: the JsonBackend and the StorageService facade
behave exactly like the original file engine, and a backend can be injected."""

import json
import threading
import time

from app.services.storage_service import StorageService
from app.storage.json_backend import JsonBackend
from app.storage.backend import StorageBackend


def test_json_backend_roundtrip(tmp_path):
    b = JsonBackend(str(tmp_path))
    assert b.read_list("things.json") == []          # ensures + empty
    b.append("things.json", {"id": 1})
    b.append("things.json", {"id": 2})
    assert b.read_list("things.json") == [{"id": 1}, {"id": 2}]
    b.write_list("things.json", [{"id": 9}])
    assert b.read_list("things.json") == [{"id": 9}]
    # written atomically as pretty JSON on disk
    on_disk = json.load(open(tmp_path / "things.json"))
    assert on_disk == [{"id": 9}]


def test_json_backend_tolerates_corrupt_file(tmp_path):
    (tmp_path / "bad.json").write_text("{ not json")
    b = JsonBackend(str(tmp_path))
    assert b.read_list("bad.json") == []             # corrupt -> empty, no crash


def test_storage_service_delegates_to_backend(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    assert isinstance(s.backend, JsonBackend)
    assert isinstance(s.backend, StorageBackend)     # satisfies the protocol
    s.append("x.json", {"a": 1})
    assert s.read_list("x.json") == [{"a": 1}]
    s.write_list("x.json", [])
    assert s.read_list("x.json") == []
    assert s.data_dir == str(tmp_path)               # kept for backward compat


def test_backend_is_injectable(tmp_path):
    class CountingBackend(JsonBackend):
        reads = 0
        def read_list(self, filename):
            type(self).reads += 1
            return super().read_list(filename)

    injected = CountingBackend(str(tmp_path))
    s = StorageService(data_dir=str(tmp_path), backend=injected)
    s.read_list("y.json")
    assert injected.reads >= 1                        # facade used the injected backend


def test_storage_service_still_ensures_known_files(tmp_path):
    StorageService(data_dir=str(tmp_path))
    # a well-known collection is created on init (as before)
    assert (tmp_path / "tasks.json").exists()


def test_default_backend_is_json_and_status(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    assert s.backend_kind() == "json"
    s.append("a.json", {"x": 1})
    st = s.status()
    assert st["backend"] == "json"
    assert st["collections"] >= 1 and st["total_documents"] >= 1
    assert st["postgres_ready"] is False and st["redis_ready"] is False  # secret-safe booleans
    assert any(item["filename"] == "a.json" for item in st["largest_collections"])


def test_json_backend_stats(tmp_path):
    b = JsonBackend(str(tmp_path))
    b.write_list("c1.json", [{"a": 1}, {"a": 2}])
    b.write_list("c2.json", [{"b": 1}])
    stats = b.stats()
    assert stats["kind"] == "json"
    assert stats["collections"] == 2
    assert stats["total_documents"] == 3
    assert stats["largest_collections"][0]["filename"] == "c1.json"  # more data -> larger file
    assert stats["largest_collections"][0]["size_bytes"] > stats["largest_collections"][1]["size_bytes"]


def test_json_backend_stats_surfaces_largest_collections_for_unbounded_growth(tmp_path):
    """Resource-exhaustion lens: instead of a bespoke size field per
    service (governance_log.json, compute_workers.json), every collection's
    real on-disk size is now surfaced in one place via stats() ->
    StorageService.status() -> /api/system/storage-status, sorted
    largest-first and capped to 10 entries."""
    b = JsonBackend(str(tmp_path))
    for i in range(15):
        b.write_list(f"c{i}.json", [{"n": i}] * (i + 1))  # varying real sizes
    stats = b.stats()
    assert len(stats["largest_collections"]) == 10  # capped, not all 15
    sizes = [item["size_bytes"] for item in stats["largest_collections"]]
    assert sizes == sorted(sizes, reverse=True)  # largest first
    assert stats["largest_collections"][0]["filename"] == "c14.json"  # most items -> largest file


# ------------------------------------------------------------------
# update_list(): atomic find-mutate-persist -- closes the lost-update race a
# plain read_list() + write_list() pair has (round 25's finding, confirmed
# concretely reachable in KaggleWorkerService.poll_job() vs submit_job()).
# ------------------------------------------------------------------
def test_update_list_mutates_and_persists(tmp_path):
    b = JsonBackend(str(tmp_path))
    b.write_list("things.json", [{"id": 1}, {"id": 2}])

    def _bump(items):
        target = next(i for i in items if i["id"] == 1)
        target["bumped"] = True
        return dict(target)

    result = b.update_list("things.json", _bump)
    assert result == {"id": 1, "bumped": True}
    assert b.read_list("things.json") == [{"id": 1, "bumped": True}, {"id": 2}]


def test_update_list_does_not_lose_a_concurrent_append(tmp_path):
    """The exact race round 25 found: a slow find-mutate-persist sequence
    (update_list) must not silently drop a concurrent append() that lands
    while the mutator is "thinking" (simulated via a sleep inside it)."""
    b = JsonBackend(str(tmp_path))
    b.write_list("jobs.json", [{"job_id": "A", "status": "running"}])

    entered_mutator = threading.Event()

    def _slow_mutate(items):
        entered_mutator.set()
        time.sleep(0.2)  # simulate the real external call happening before this point in production code
        target = next(i for i in items if i["job_id"] == "A")
        target["status"] = "complete"
        return dict(target)

    def _poll():
        b.update_list("jobs.json", _slow_mutate)

    poll_thread = threading.Thread(target=_poll)
    poll_thread.start()
    entered_mutator.wait(timeout=2)
    b.append("jobs.json", {"job_id": "B", "status": "submitted"})  # concurrent submit
    poll_thread.join(timeout=2)

    final = b.read_list("jobs.json")
    ids = {item["job_id"] for item in final}
    assert ids == {"A", "B"}  # B must survive -- this failed before the fix
    job_a = next(i for i in final if i["job_id"] == "A")
    assert job_a["status"] == "complete"


def test_storage_service_update_list_delegates(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    s.append("z.json", {"id": 1, "n": 0})

    def _inc(items):
        items[0]["n"] += 1
        return items[0]["n"]

    assert s.update_list("z.json", _inc) == 1
    assert s.read_list("z.json") == [{"id": 1, "n": 1}]


def test_storage_status_endpoint():
    from fastapi.testclient import TestClient
    from app.main import app
    r = TestClient(app).get("/api/system/storage-status").json()
    assert r["backend"] in ("json", "postgres")
    assert set(["backend", "collections", "total_documents", "postgres_ready", "redis_ready", "configured_backend"]) <= set(r)
