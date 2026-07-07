"""documents JSONB table (v100 Postgres storage backend)

Revision ID: 0001_documents
Revises:
Create Date: 2026-07-07
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0001_documents"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            collection text NOT NULL,
            seq bigserial NOT NULL,
            doc jsonb NOT NULL,
            PRIMARY KEY (collection, seq)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS documents_collection_idx ON documents (collection, seq)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS documents")
