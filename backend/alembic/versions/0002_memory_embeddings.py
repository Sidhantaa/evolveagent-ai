"""memory_embeddings table (v100 Memory v2 / pgvector)

Revision ID: 0002_memory_embeddings
Revises: 0001_documents
Create Date: 2026-07-07
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0002_memory_embeddings"
down_revision: Union[str, None] = "0001_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_embeddings (
            id text PRIMARY KEY,
            kind text,
            text text,
            source text,
            metadata jsonb,
            embedding vector(1536),
            created_at timestamptz DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS memory_embeddings")
