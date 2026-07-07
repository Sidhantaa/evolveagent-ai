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


def test_to_sync_url_normalizes_driver():
    from app.storage.postgres_backend import to_sync_url
    assert to_sync_url("postgresql+asyncpg://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert to_sync_url("postgresql://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
    assert to_sync_url("postgresql+psycopg://u:p@h/db") == "postgresql+psycopg://u:p@h/db"
