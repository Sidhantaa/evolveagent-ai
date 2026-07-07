"""Postgres (JSONB) storage backend.

Implements the same :class:`StorageBackend` contract as ``JsonBackend`` using a
single JSONB "documents" table, where each collection (the old JSON filename) is
just a column value. This is the JSONB-first migration target: swapping to it
requires no change to the 140+ services above ``StorageService``.

    documents(collection text, seq bigserial, doc jsonb)  PK (collection, seq)

``seq`` preserves append order (matching the JSON list semantics). Runtime is
**synchronous** (the whole app is sync), so we use SQLAlchemy's sync engine with
the psycopg (v3) driver.
"""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS documents (
        collection text NOT NULL,
        seq bigserial NOT NULL,
        doc jsonb NOT NULL,
        PRIMARY KEY (collection, seq)
    )
    """,
    "CREATE INDEX IF NOT EXISTS documents_collection_idx ON documents (collection, seq)",
]

_INSERT = text("INSERT INTO documents (collection, doc) VALUES (:c, CAST(:d AS jsonb))")


def to_sync_url(url: str) -> str:
    """Normalize a DATABASE_URL to a synchronous psycopg driver."""
    for prefix in ("postgresql+asyncpg://", "postgresql+psycopg2://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


class PostgresBackend:
    def __init__(self, database_url: str, engine: Engine | None = None):
        self.engine: Engine = engine or create_engine(to_sync_url(database_url), pool_pre_ping=True, future=True)
        self._init_schema()

    def _init_schema(self) -> None:
        with self.engine.begin() as conn:
            for stmt in _SCHEMA:
                conn.execute(text(stmt))

    def ensure(self, filename: str) -> None:
        # Collections are implicit (a column value); nothing to create per-collection.
        return None

    def read_list(self, filename: str) -> list[dict[str, Any]]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                text("SELECT doc FROM documents WHERE collection = :c ORDER BY seq"),
                {"c": filename},
            ).fetchall()
        # psycopg returns jsonb as a Python object already.
        return [row[0] for row in rows if isinstance(row[0], dict)]

    def append(self, filename: str, item: dict[str, Any]) -> None:
        with self.engine.begin() as conn:
            conn.execute(_INSERT, {"c": filename, "d": json.dumps(item)})

    def write_list(self, filename: str, items: list[dict[str, Any]]) -> None:
        with self.engine.begin() as conn:
            conn.execute(text("DELETE FROM documents WHERE collection = :c"), {"c": filename})
            for item in items:
                conn.execute(_INSERT, {"c": filename, "d": json.dumps(item)})
