"""Task 8: adaptive-learning recall via Memory v2.

Keyword mode (no memory / memory in keyword mode) behaves exactly as before.
The semantic path runs when Memory v2 is on pgvector — covered in CI via
TEST_DATABASE_URL; skipped locally without a DB.
"""

import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.adaptive_learning_service import AdaptiveLearningService
from app.services.governance_service import GovernanceService
from app.services.memory_service import MemoryService
from app.services.storage_service import StorageService

client = TestClient(app)
TEST_DB = os.environ.get("TEST_DATABASE_URL")


def _services(tmp_path, database_url=None):
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    mem = MemoryService(s, g, database_url=database_url)
    return AdaptiveLearningService(s, g, memory=mem), mem


def test_keyword_mode_unchanged_without_pg(tmp_path):
    adaptive, mem = _services(tmp_path, database_url=None)
    assert mem.mode == "keyword"
    adaptive.ingest("kubernetes helm deployment guide", kind="topic")
    rec = adaptive.recommend("kubernetes helm")
    assert rec["engine"] == "keyword"          # semantic not used without pgvector
    assert rec["count"] >= 1
    assert rec["recommendations"][0]["kind"] == "topic"


def test_new_items_mirror_into_memory(tmp_path):
    adaptive, mem = _services(tmp_path, database_url=None)
    before = mem.count()
    adaptive.ingest("voice assistant design patterns", kind="reference")
    assert mem.count() == before + 1           # mirrored on NEW item
    adaptive.ingest("voice assistant design patterns", kind="reference")
    assert mem.count() == before + 1           # reinforcement does NOT re-mirror


def test_status_reports_recall_engine():
    st = client.get("/api/adaptive-learning/status").json()
    assert st["recall_engine"] in ("semantic", "keyword")
    assert st["trains_base_model"] is False


def test_recommend_endpoint_reports_engine():
    client.post("/api/adaptive-learning/items", json={"text": "engine check note", "kind": "topic"})
    r = client.get("/api/adaptive-learning/recommend", params={"query": "engine check"}).json()
    assert r["engine"] in ("semantic", "keyword")


@pytest.mark.skipif(not TEST_DB, reason="TEST_DATABASE_URL not set")
def test_semantic_recall_on_pgvector(tmp_path):
    adaptive, mem = _services(tmp_path, database_url=TEST_DB)
    assert mem.mode == "pgvector"
    tag = uuid.uuid4().hex
    adaptive.ingest(f"{tag} kubernetes helm chart deployment runbook", kind="topic")
    adaptive.ingest(f"{tag} react component styling with tailwind", kind="reference")
    rec = adaptive.recommend(f"{tag} kubernetes helm")
    assert rec["engine"] == "semantic"
    assert rec["count"] >= 1
    assert "kubernetes" in rec["recommendations"][0]["text"].lower()
    # shape preserved for the frontend (kind/text/source/weight/match)
    assert {"kind", "text", "source", "weight", "match"} <= set(rec["recommendations"][0])
