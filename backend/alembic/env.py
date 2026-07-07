"""Alembic environment.

Reads the database URL from the ``DATABASE_URL`` env var (same one the app will
use). For migrations we use a *sync* driver (psycopg/pg8000-less): SQLAlchemy's
default, by stripping the ``+asyncpg`` suffix, so Alembic runs synchronously.

There are no models to autogenerate against yet — ``target_metadata`` is None
until the Postgres backend's schema lands (task 4). This file never runs at app
import; only when the ``alembic`` CLI is invoked.
"""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# No ORM metadata yet; schema is created by explicit migrations (task 4+).
target_metadata = None


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    # Alembic runs synchronously; drop the async driver suffix if present.
    return url.replace("+asyncpg", "")


def run_migrations_offline() -> None:
    context.configure(
        url=_database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    section = config.get_section(config.config_ini_section) or {}
    section["sqlalchemy.url"] = _database_url()
    connectable = engine_from_config(section, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
