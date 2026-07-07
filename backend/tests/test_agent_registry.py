from fastapi.testclient import TestClient

from app.main import app
from app.services.agent_registry_service import AgentRegistryService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

client = TestClient(app)


def _service(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    s.write_list("agent_profiles.json", [{
        "agent_id": "a1", "name": "Studio One", "role": "research things",
        "published_local": True, "guardrails": {"requires_approval": ["send_email"]},
        "evaluation": {"score": 88}, "version": 3, "tools": ["retrieval"],
    }])
    s.write_list("custom_agents.json", [{
        "agent_id": "c1", "name": "Resume Agent", "role": "resumes", "enabled": False,
        "approval_level": "manual", "tools_allowed": ["files"],
    }])
    s.write_list("agent_departments.json", [{
        "department_id": "d1", "name": "Engineering", "active": True,
        "manager_agent": "Engineering Manager Agent",
        "worker_agents": ["Coder Agent"], "reviewer_agents": [], "auditor_agents": [],
        "allowed_tools": ["build_run"], "permission_level": "approve_to_run",
        "description": "builds things",
    }])
    return AgentRegistryService(s, GovernanceService(s))


def test_unifies_all_three_sources(tmp_path):
    reg = _service(tmp_path)
    res = reg.list_agents()
    assert res["count"] == 4  # 1 studio + 1 custom + 2 department members
    assert {e["source"] for e in res["agents"]} == {"agent_studio", "custom_agents", "department"}


def test_normalized_shape_and_flags(tmp_path):
    reg = _service(tmp_path)
    studio = next(e for e in reg.list_agents()["agents"] if e["source"] == "agent_studio")
    assert studio["status"] == "published" and studio["approval_gated"] is True
    assert studio["quality_score"] == 88 and studio["version"] == 3
    custom = next(e for e in reg.list_agents()["agents"] if e["source"] == "custom_agents")
    assert custom["status"] == "disabled" and custom["approval_gated"] is True
    dept = [e for e in reg.list_agents()["agents"] if e["source"] == "department"]
    assert any(e["role"].startswith("manager") for e in dept)
    assert all(e["approval_gated"] for e in dept)  # approve_to_run


def test_filter_by_source_and_query(tmp_path):
    reg = _service(tmp_path)
    assert reg.list_agents(source="agent_studio")["agents"][0]["name"] == "Studio One"
    assert reg.list_agents(q="resume")["agents"][0]["name"] == "Resume Agent"
    assert reg.list_agents(q="zzz-no-match")["count"] == 0


def test_get_by_registry_id(tmp_path):
    reg = _service(tmp_path)
    e = reg.get("studio:a1")
    assert e["name"] == "Studio One"
    import pytest
    with pytest.raises(ValueError):
        reg.get("studio:nope")


def test_endpoints_and_analytics():
    r = client.get("/api/agent-registry").json()
    assert "agents" in r and "count" in r
    s = client.get("/api/agent-registry/summary").json()
    assert "agent_registry_total" in s and "agent_registry_by_source" in s
    assert "agent_registry_total" in client.get("/api/analytics").json()
    assert client.get("/api/agent-registry/definitely:not:there").status_code == 404
