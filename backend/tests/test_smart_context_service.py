from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _ws():
    d = client.post("/api/workspaces", json={"name": "v71 ctx ws"}).json()
    return d.get("workspace_id") or d.get("id") or (d.get("workspace") or {}).get("workspace_id")


def test_plan_selects_relevant_context_with_reasons():
    wid = _ws()
    client.post("/api/goals", json={"title": "Kubernetes migration plan", "description": "migrate services to kubernetes", "workspace_id": wid})
    plan = client.post("/api/context/plan", json={"query": "kubernetes migration", "workspace_id": wid}).json()
    assert plan["selected_count"] >= 1
    assert all("reason" in s for s in plan["selected"])
    assert plan["used_chars"] <= plan["budget_chars"]


def test_budget_is_enforced():
    wid = _ws()
    for i in range(6):
        client.post("/api/goals", json={"title": f"budget context alpha {i}", "description": "alpha " * 60, "workspace_id": wid})
    plan = client.post("/api/context/plan", json={"query": "alpha", "workspace_id": wid, "budget_chars": 300}).json()
    assert plan["used_chars"] <= 300
    assert any(e["reason"] == "over context budget" for e in plan["excluded"]) or plan["selected_count"] <= 2


def test_sensitive_content_is_filtered():
    wid = _ws()
    client.post("/api/goals", json={"title": "contact sensitive", "description": "reach me at secret@example.com about alpha", "workspace_id": wid})
    plan = client.post("/api/context/plan", json={"query": "alpha", "workspace_id": wid}).json()
    # The email-bearing item must not be in selected; it should be excluded as sensitive.
    assert all("@" not in s["preview"] for s in plan["selected"])
    assert any("sensitive" in e["reason"] for e in plan["excluded"])


def test_duplicate_context_removed():
    wid = _ws()
    for _ in range(2):
        client.post("/api/goals", json={"title": "duplicate context beta", "description": "identical beta content here", "workspace_id": wid})
    plan = client.post("/api/context/plan", json={"query": "beta", "workspace_id": wid}).json()
    assert any(e["reason"] == "duplicate context removed" for e in plan["excluded"]) or plan["selected_count"] == 1


def test_summary_and_analytics():
    summary = client.get("/api/context/summary").json()
    for key in ("context_sources", "default_budget_chars", "sensitive_filters"):
        assert key in summary
    assert "smart_context_sources" in client.get("/api/analytics").json()


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/context/plan", json={"query": "anything"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "context_planned" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/workspace-os/summary").status_code == 200
    assert client.get("/api/notifications-inbox/summary").status_code == 200
