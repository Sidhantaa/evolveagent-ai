from app.storage.backend import StorageBackend
from app.storage.json_backend import JsonBackend

__all__ = ["StorageBackend", "JsonBackend", "PostgresBackend"]


def __getattr__(name: str):
    # Lazy import so the (optional) SQLAlchemy/psycopg deps are only needed when
    # the Postgres backend is actually used.
    if name == "PostgresBackend":
        from app.storage.postgres_backend import PostgresBackend
        return PostgresBackend
    raise AttributeError(name)
