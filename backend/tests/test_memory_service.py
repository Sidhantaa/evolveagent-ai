"""Memory v2 tests. Keyword mode + local embedder run everywhere; the pgvector
path runs only when TEST_DATABASE_URL is set (CI provides it)."""

import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.memory_service import MemoryService, local_embed, DIM
from app.services.storage_service import StorageService
from app.services.governance_service import GovernanceService

client = TestClient(app)
TEST_DB = os.environ.get("TEST_DATABASE_URL")


def test_local_embed_is_deterministic_and_normalized():
    a = local_embed("kubernetes helm migration")
    b = local_embed("kubernetes helm migration")
    assert a == b and len(a) == DIM
    norm = sum(x * x for x in a) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def _keyword_service(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    return MemoryService(s, GovernanceService(s), database_url=None)


def test_keyword_mode_add_and_search(tmp_path):
    m = _keyword_service(tmp_path)
    assert m.mode == "keyword"
    m.add("Deploy the service to Kubernetes with Helm", kind="ops")
    m.add("Write unit tests for the parser", kind="dev")
    res = m.search("kubernetes helm deployment")
    assert res["count"] >= 1
    assert "kubernetes" in res["results"][0]["text"].lower()
    assert res["mode"] == "keyword"


def test_empty_text_rejected(tmp_path):
    m = _keyword_service(tmp_path)
    with pytest.raises(ValueError):
        m.add("   ")


def test_endpoints_status_add_search():
    st = client.get("/api/memory-v2/status").json()
    assert st["available"] is True and st["dimensions"] == DIM
    add = client.post("/api/memory-v2/add", json={"text": "semantic memory pipeline note", "kind": "note"}).json()
    assert add["id"] and add["mode"] in ("keyword", "pgvector")
    s = client.get("/api/memory-v2/search", params={"q": "semantic memory"}).json()
    assert "results" in s
    assert "memory_v2_items" in client.get("/api/analytics").json()


@pytest.mark.skipif(not TEST_DB, reason="TEST_DATABASE_URL not set")
def test_pgvector_mode_roundtrip(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    m = MemoryService(s, GovernanceService(s), database_url=TEST_DB)
    assert m.mode == "pgvector"
    tag = uuid.uuid4().hex
    m.add(f"alpha {tag} kubernetes helm chart deployment", kind="ops")
    m.add(f"beta {tag} frontend react vite component", kind="dev")
    res = m.search(f"{tag} kubernetes helm")
    assert res["mode"] == "pgvector" and res["count"] >= 1
    # the k8s doc should rank above the react doc for a k8s query
    assert "kubernetes" in res["results"][0]["text"].lower()
    assert 0.0 <= res["results"][0]["score"] <= 1.0
