"""v140 Workspace Brain — wires Memory v2 (the v100 pgvector/real-embeddings
service, which until now had zero callers outside its own routes/tests) into
WorkspaceService.relevant_memory(), the method that actually feeds context into
every live agent run. Keyword mode (no Postgres) — the vast majority of local
setups — keeps the exact original heuristic behavior; the pgvector path (real
cosine similarity) runs only when TEST_DATABASE_URL is set (CI provides it)."""

import os
import uuid

import pytest

from app.services.custom_agent_service import CustomAgentService
from app.services.goal_service import GoalService
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


# ------------------------------------------------------------------
# v140 task 2 — goals are the other context pillar (a workspace is defined as
# "chats, files, goals, agents, and memory") that real semantic recall hadn't
# reached yet: GoalService now mirrors created goals into Memory v2 too.
# ------------------------------------------------------------------
def test_goal_creation_mirrors_into_memory_v2(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    memory_v2 = MemoryService(s, GovernanceService(s), database_url=None)
    ws = WorkspaceService(s, memory_v2=memory_v2)
    goals = GoalService(s, memory_v2=memory_v2)
    wid = ws.default_workspace_id()
    goals.create_manual("Launch the beta", description="Ship the closed beta to design partners.", workspace_id=wid)
    hits = memory_v2.search("closed beta design partners", workspace_id=wid)
    assert hits["count"] >= 1
    assert "beta" in hits["results"][0]["text"].lower()


def test_goal_without_workspace_id_does_not_mirror(tmp_path):
    """Ad-hoc goals with no workspace can't be scoped for recall — must not
    crash, and must not silently land in the wrong workspace's search results."""
    s = StorageService(data_dir=str(tmp_path))
    memory_v2 = MemoryService(s, GovernanceService(s), database_url=None)
    goals = GoalService(s, memory_v2=memory_v2)
    goal, _ = goals.create_manual("Untracked goal", description="No workspace attached.")
    assert goal.goal_id
    assert memory_v2.count() == 0


def test_goal_mirror_failure_never_blocks_goal_creation(tmp_path):
    class BrokenMemoryV2:
        mode = "keyword"

        def add(self, *args, **kwargs):
            raise RuntimeError("boom")

    s = StorageService(data_dir=str(tmp_path))
    goals = GoalService(s, memory_v2=BrokenMemoryV2())
    goal, _ = goals.create_manual("Still creates", description="Mirroring failure must not block this.", workspace_id="ws-1")
    assert goal.title == "Still creates"


def test_relevant_memory_can_surface_a_goal_alongside_notes():
    """The workspace's own docstring defines it as project context over chats,
    files, goals, agents, and memory — relevant_memory() should be able to draw
    on a goal, not just workspace_memory notes, when v2 pgvector recall is live."""
    from unittest.mock import MagicMock

    from app.services.storage_service import StorageService as SS
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        s = SS(data_dir=tmp)
        fake_v2 = MagicMock()
        fake_v2.mode = "pgvector"
        ws = WorkspaceService(s, memory_v2=fake_v2)
        goals = GoalService(s, memory_v2=fake_v2)
        wid = ws.default_workspace_id()
        goal, _ = goals.create_manual("Cut the release", description="Coordinate the v2 release cut.", workspace_id=wid)
        fake_v2.search.return_value = {
            "results": [{"metadata": {"workspace_id": wid, "goal_id": goal.goal_id}}],
        }
        candidates = ws._semantic_candidates(wid, "release plan", limit=5)
        assert candidates and candidates[0]["type"] == "goal"
        assert "release cut" in candidates[0]["content"].lower()


def test_goal_endpoints_still_work():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    created = client.post("/api/goals", json={"title": "Smoke goal", "description": "test"}).json()
    assert created["goal"]["title"] == "Smoke goal"
    assert client.get("/api/goals").status_code == 200


# ------------------------------------------------------------------
# v140 task 3 — uploaded files are the last context pillar (chats already flow
# through create_memory via persist_workspace_memory, so they got real recall
# for free once task 1 landed): FileService now mirrors extracted text too.
# ------------------------------------------------------------------
def test_processed_file_mirrors_into_memory_v2():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    workspaces = client.get("/api/workspaces").json()
    wid = workspaces[0]["workspace_id"]
    tag = uuid.uuid4().hex
    resp = client.post(
        "/api/files/upload",
        files={"files": ("brain-note.txt", f"file-{tag}-marker unique content".encode(), "text/plain")},
        data={"workspace_id": wid},
    ).json()
    assert resp["files"][0]["status"] == "processed"
    hits = client.get("/api/memory-v2/search", params={"q": f"file-{tag}-marker", "workspace_id": wid}).json()
    assert hits["count"] >= 1
    assert any("brain-note.txt" in r["text"] for r in hits["results"])


def test_unsupported_file_type_does_not_mirror():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    workspaces = client.get("/api/workspaces").json()
    wid = workspaces[0]["workspace_id"]
    resp = client.post(
        "/api/files/upload",
        files={"files": ("unsupported.exe", b"zqxjklmnopq", "application/octet-stream")},
        data={"workspace_id": wid},
    ).json()
    assert resp["files"][0]["status"] == "failed"
    hits = client.get("/api/memory-v2/search", params={"q": "zqxjklmnopq", "workspace_id": wid}).json()
    assert hits["count"] == 0


def test_file_mirror_failure_never_blocks_upload(tmp_path):
    import asyncio
    import io
    from fastapi import UploadFile

    from app.services.file_service import FileService
    from app.services.storage_service import StorageService

    class BrokenMemoryV2:
        mode = "keyword"

        def add(self, *args, **kwargs):
            raise RuntimeError("boom")

    s = StorageService(data_dir=str(tmp_path))
    fs = FileService(s, memory_v2=BrokenMemoryV2())
    upload = UploadFile(filename="note.txt", file=io.BytesIO(b"still processes fine"))
    result = asyncio.run(fs.process_file(upload, workspace_id="ws-1"))
    assert result["status"] == "processed"


def test_file_resolves_to_a_file_type_candidate_via_semantic_candidates(tmp_path):
    from unittest.mock import MagicMock

    from app.services.storage_service import StorageService
    from app.services.workspace_service import WorkspaceService

    s = StorageService(data_dir=str(tmp_path))
    fake_v2 = MagicMock()
    fake_v2.mode = "pgvector"
    ws = WorkspaceService(s, memory_v2=fake_v2)
    wid = ws.default_workspace_id()
    s.append("files.json", {"file_id": "f1", "workspace_id": wid, "filename": "notes.txt", "text_preview": "roadmap details here"})
    fake_v2.search.return_value = {"results": [{"metadata": {"workspace_id": wid, "file_id": "f1"}}]}
    candidates = ws._semantic_candidates(wid, "roadmap", limit=5)
    assert candidates and candidates[0]["type"] == "file"
    assert candidates[0]["title"] == "notes.txt"


# ------------------------------------------------------------------
# v140 task 4 — custom agents are the last of the 5 context pillars (chats,
# files, goals, agents, and memory) to reach real semantic recall.
# ------------------------------------------------------------------
def test_custom_agent_creation_mirrors_into_memory_v2(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    memory_v2 = MemoryService(s, GovernanceService(s), database_url=None)
    ws = WorkspaceService(s, memory_v2=memory_v2)
    agents = CustomAgentService(s, memory_v2=memory_v2)
    wid = ws.default_workspace_id()
    agents.create({"name": "Pharmacy PA Agent", "role": "Organize prior authorization criteria for review.", "workspace_id": wid})
    hits = memory_v2.search("prior authorization criteria", workspace_id=wid)
    assert hits["count"] >= 1
    assert "pharmacy" in hits["results"][0]["text"].lower()


def test_custom_agent_without_workspace_id_does_not_mirror(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    memory_v2 = MemoryService(s, GovernanceService(s), database_url=None)
    agents = CustomAgentService(s, memory_v2=memory_v2)
    created = agents.create({"name": "Untracked Agent", "role": "No workspace attached."})
    assert created.agent_id
    assert memory_v2.count() == 0


def test_custom_agent_mirror_failure_never_blocks_creation(tmp_path):
    class BrokenMemoryV2:
        mode = "keyword"

        def add(self, *args, **kwargs):
            raise RuntimeError("boom")

    s = StorageService(data_dir=str(tmp_path))
    agents = CustomAgentService(s, memory_v2=BrokenMemoryV2())
    created = agents.create({"name": "Still creates", "role": "Mirroring failure must not block this.", "workspace_id": "ws-1"})
    assert created.name == "Still creates"


def test_custom_agent_resolves_to_an_agent_type_candidate_via_semantic_candidates(tmp_path):
    from unittest.mock import MagicMock

    from app.services.storage_service import StorageService
    from app.services.workspace_service import WorkspaceService

    s = StorageService(data_dir=str(tmp_path))
    fake_v2 = MagicMock()
    fake_v2.mode = "pgvector"
    ws = WorkspaceService(s, memory_v2=fake_v2)
    wid = ws.default_workspace_id()
    s.append("custom_agents.json", {"agent_id": "a1", "workspace_id": wid, "name": "Bug Fix Agent", "role": "diagnose bugs"})
    fake_v2.search.return_value = {"results": [{"metadata": {"workspace_id": wid, "agent_id": "a1"}}]}
    candidates = ws._semantic_candidates(wid, "bug diagnosis", limit=5)
    assert candidates and candidates[0]["type"] == "agent"
    assert candidates[0]["title"] == "Bug Fix Agent"


def test_custom_agent_endpoints_still_work():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    created = client.post("/api/agents/custom", json={"name": "Smoke Agent", "role": "test"}).json()
    assert created["name"] == "Smoke Agent"
    assert client.get("/api/agents/custom").status_code == 200
