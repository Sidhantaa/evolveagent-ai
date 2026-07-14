"""PostgresBackend tests + JSON/Postgres parity.

These require a real Postgres. They read TEST_DATABASE_URL and **skip** if it is
absent or unreachable (so local/CI runs without a DB stay green). CI provides a
Postgres service, so they run for real there. Each test uses a unique collection
name to stay isolated in a shared database.
"""

import os
import uuid

import pytest

from app.storage.json_backend import JsonBackend

TEST_DB = os.environ.get("TEST_DATABASE_URL")


def _make_backend():
    if not TEST_DB:
        pytest.skip("TEST_DATABASE_URL not set")
    try:
        from app.storage.postgres_backend import PostgresBackend
        return PostgresBackend(TEST_DB)
    except Exception as exc:  # connection/driver problem -> skip, don't fail
        pytest.skip(f"Postgres not reachable: {exc}")


@pytest.fixture()
def pg():
    return _make_backend()


def _coll() -> str:
    return f"test_{uuid.uuid4().hex}.json"


def test_roundtrip(pg):
    c = _coll()
    assert pg.read_list(c) == []
    pg.append(c, {"id": 1})
    pg.append(c, {"id": 2})
    assert pg.read_list(c) == [{"id": 1}, {"id": 2}]      # append order preserved
    pg.write_list(c, [{"id": 9}])
    assert pg.read_list(c) == [{"id": 9}]
    pg.write_list(c, [])
    assert pg.read_list(c) == []


def test_collections_are_isolated(pg):
    a, b = _coll(), _coll()
    pg.append(a, {"k": "a"})
    pg.append(b, {"k": "b"})
    assert pg.read_list(a) == [{"k": "a"}]
    assert pg.read_list(b) == [{"k": "b"}]


def test_parity_with_json_backend(pg, tmp_path):
    """Same sequence of ops yields identical results on JSON and Postgres."""
    js = JsonBackend(str(tmp_path))
    cj = "parity.json"
    cp = _coll()
    ops = [
        ("append", {"a": 1}),
        ("append", {"b": 2}),
        ("write", [{"c": 3}, {"d": 4}]),
        ("append", {"e": 5}),
    ]
    for kind, payload in ops:
        if kind == "append":
            js.append(cj, payload)
            pg.append(cp, payload)
        else:
            js.write_list(cj, payload)
            pg.write_list(cp, payload)
        assert js.read_list(cj) == pg.read_list(cp)


def test_update_list_mutates_and_persists(pg):
    c = _coll()
    pg.write_list(c, [{"id": 1}, {"id": 2}])

    def _bump(items):
        target = next(i for i in items if i["id"] == 1)
        target["bumped"] = True
        return dict(target)

    result = pg.update_list(c, _bump)
    assert result == {"id": 1, "bumped": True}
    assert pg.read_list(c) == [{"id": 1, "bumped": True}, {"id": 2}]


def test_update_list_does_not_lose_a_concurrent_append(pg):
    """Postgres parity of the JsonBackend race test -- the per-collection
    advisory lock (pg_advisory_xact_lock) must serialize update_list against
    a concurrent append() on the same collection, same as JsonBackend's
    process-wide Lock does."""
    import threading
    import time

    c = _coll()
    pg.write_list(c, [{"job_id": "A", "status": "running"}])
    entered = threading.Event()

    def _slow_mutate(items):
        entered.set()
        time.sleep(0.5)
        target = next(i for i in items if i["job_id"] == "A")
        target["status"] = "complete"
        return dict(target)

    def _poll():
        pg.update_list(c, _slow_mutate)

    t = threading.Thread(target=_poll)
    t.start()
    entered.wait(timeout=3)
    pg.append(c, {"job_id": "B", "status": "submitted"})
    t.join(timeout=3)

    final = pg.read_list(c)
    ids = {item["job_id"] for item in final}
    assert ids == {"A", "B"}
    job_a = next(i for i in final if i["job_id"] == "A")
    assert job_a["status"] == "complete"


def test_to_sync_url_normalizes_driver():
    from app.storage.postgres_backend import to_sync_url
    assert to_sync_url("postgresql+asyncpg://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert to_sync_url("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert to_sync_url("postgresql+psycopg://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
