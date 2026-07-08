"""v140 Workspace Brain — wires Memory v2 (the v100 pgvector/real-embeddings
service, which until now had zero callers outside its own routes/tests) into
WorkspaceService.relevant_memory(), the method that actually feeds context into
every live agent run. Keyword mode (no Postgres) — the vast majority of local
setups — keeps the exact original heuristic behavior; the pgvector path (real
cosine similarity) runs only when TEST_DATABASE_URL is set (CI provides it)."""

import os
import uuid

import pytest

from app.services.governance_service import GovernanceService
from app.services.memory_service import MemoryService
from app.services.storage_service import StorageService
from app.services.workspace_service import WorkspaceService

TEST_DB = os.environ.get("TEST_DATABASE_URL")


def _services(tmp_path, memory_v2=None):
    s = StorageService(data_dir=str(tmp_path))
    ws = WorkspaceService(s, memory_v2=memory_v2)
    return s, ws


def test_without_memory_v2_behavior_is_unchanged(tmp_path):
    _, ws = _services(tmp_path)
    wid = ws.default_workspace_id()
    ws.create_memory(wid, {"title": "Deploy runbook", "content": "Use blue-green deploys for the API."})
    context, selected = ws.relevant_memory(wid, "how do we deploy the api")
    assert selected and "blue-green" in context.lower()
    assert ws.summarize_workspace(wid)["semantic_recall_engine"] == "heuristic"


def test_memory_v2_in_keyword_mode_falls_back_to_heuristic(tmp_path):
    """memory_v2 wired but not on Postgres (mode='keyword') -> still falls back
    to the original heuristic search; only pgvector mode changes retrieval."""
    s = StorageService(data_dir=str(tmp_path))
    memory_v2 = MemoryService(s, GovernanceService(s), database_url=None)
    ws = WorkspaceService(s, memory_v2=memory_v2)
    wid = ws.default_workspace_id()
    ws.create_memory(wid, {"title": "Release process", "content": "Tag main, then run the release workflow."})
    assert memory_v2.mode == "keyword"
    context, selected = ws.relevant_memory(wid, "how do we release")
    assert selected and "release workflow" in context.lower()
    assert ws.summarize_workspace(wid)["semantic_recall_engine"] == "keyword"


def test_create_memory_mirrors_into_memory_v2(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    memory_v2 = MemoryService(s, GovernanceService(s), database_url=None)
    ws = WorkspaceService(s, memory_v2=memory_v2)
    wid = ws.default_workspace_id()
    ws.create_memory(wid, {"title": "Onboarding notes", "content": "New hires get repo access on day one."})
    hits = memory_v2.search("onboarding repo access", workspace_id=wid)
    assert hits["count"] >= 1
    assert "onboarding" in hits["results"][0]["text"].lower()


def test_memory_v2_mirror_failure_never_blocks_workspace_memory_creation(tmp_path):
    class BrokenMemoryV2:
        mode = "keyword"

        def add(self, *args, **kwargs):
            raise RuntimeError("boom")

    s = StorageService(data_dir=str(tmp_path))
    ws = WorkspaceService(s, memory_v2=BrokenMemoryV2())
    wid = ws.default_workspace_id()
    memory = ws.create_memory(wid, {"title": "Still works", "content": "Mirroring failure must not block this."})
    assert memory["title"] == "Still works"


@pytest.mark.skipif(not TEST_DB, reason="TEST_DATABASE_URL not set")
def test_pgvector_mode_powers_real_semantic_recall(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    memory_v2 = MemoryService(s, GovernanceService(s), database_url=TEST_DB)
    ws = WorkspaceService(s, memory_v2=memory_v2)
    wid = ws.default_workspace_id()
    tag = uuid.uuid4().hex
    ws.create_memory(wid, {"title": f"Kubernetes {tag}", "content": "Helm chart deployment steps for the cluster."})
    ws.create_memory(wid, {"title": f"Frontend {tag}", "content": "React component structure and Vite config."})
    assert ws.summarize_workspace(wid)["semantic_recall_engine"] == "pgvector"
    context, selected = ws.relevant_memory(wid, f"{tag} kubernetes helm cluster deployment")
    assert selected
    assert "kubernetes" in selected[0]["title"].lower()


def test_workspace_isolation_in_memory_v2_search(tmp_path):
    """Two workspaces' memories must never bleed into each other's recall,
    even though Memory v2 is a single shared pool under the hood."""
    s = StorageService(data_dir=str(tmp_path))
    memory_v2 = MemoryService(s, GovernanceService(s), database_url=None)
    ws = WorkspaceService(s, memory_v2=memory_v2)
    wid_a = ws.create_workspace({"name": "Workspace A"})["workspace_id"]
    wid_b = ws.create_workspace({"name": "Workspace B"})["workspace_id"]
    ws.create_memory(wid_a, {"title": "Secret A", "content": "zzyzxqrkalpha content"})
    ws.create_memory(wid_b, {"title": "Secret B", "content": "wwvutplmbeta content"})
    hits_a = memory_v2.search("zzyzxqrkalpha", workspace_id=wid_a)
    hits_b = memory_v2.search("zzyzxqrkalpha", workspace_id=wid_b)
    assert hits_a["count"] >= 1
    assert hits_b["count"] == 0


def test_endpoints_still_work_and_search_accepts_workspace_id():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    added = client.post("/api/memory-v2/add", json={"text": "workspace brain smoke text", "kind": "note"}).json()
    assert added["id"]
    resp = client.get("/api/memory-v2/search", params={"q": "workspace brain smoke", "workspace_id": "does-not-exist"}).json()
    assert "results" in resp
    assert client.get("/api/workspaces").status_code == 200
