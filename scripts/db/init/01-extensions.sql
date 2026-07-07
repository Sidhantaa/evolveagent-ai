-- Enable the pgvector extension for Memory v2 (semantic search).
-- Runs automatically the first time the Postgres volume is initialized.
CREATE EXTENSION IF NOT EXISTS vector;
