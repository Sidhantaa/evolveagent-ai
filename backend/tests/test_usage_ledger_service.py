from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_record_usage_estimates_cost():
    entry = client.post("/api/usage-ledger/entries", json={"workspace_id": "v50a", "capability": "text", "units": 1000}).json()
    assert entry["entry_id"]
    assert entry["capability"] == "text"
    assert entry["estimated_cost"] > 0  # derived from default rate
    assert "no billing" in entry["note"].lower()


def test_record_usage_explicit_cost():
    entry = client.post("/api/usage-ledger/entries", json={"workspace_id": "v50b", "capability": "image", "units": 3, "estimated_cost": 0.5}).json()
    assert entry["estimated_cost"] == 0.5


def test_list_entries_filtered():
    client.post("/api/usage-ledger/entries", json={"workspace_id": "v50c", "capability": "mcp", "units": 1})
    listed = client.get("/api/usage-ledger/entries?workspace_id=v50c").json()
    assert all(e["workspace_id"] == "v50c" for e in listed["entries"])
    assert listed["count"] >= 1


def test_budget_set_and_status_under_near_over():
    client.post("/api/usage-ledger/budgets", json={"workspace_id": "v50budget", "monthly_limit": 1.0})
    # Under budget.
    client.post("/api/usage-ledger/entries", json={"workspace_id": "v50budget", "capability": "other", "units": 1, "estimated_cost": 0.3})
    s = client.get("/api/usage-ledger/summary?workspace_id=v50budget").json()
    assert s["monthly_limit"] == 1.0
    assert s["budget_status"] == "under"
    # Near budget (>=80%).
    client.post("/api/usage-ledger/entries", json={"workspace_id": "v50budget", "capability": "other", "units": 1, "estimated_cost": 0.55})
    s = client.get("/api/usage-ledger/summary?workspace_id=v50budget").json()
    assert s["budget_status"] == "near"
    # Over budget.
    client.post("/api/usage-ledger/entries", json={"workspace_id": "v50budget", "capability": "other", "units": 1, "estimated_cost": 0.5})
    s = client.get("/api/usage-ledger/summary?workspace_id=v50budget").json()
    assert s["budget_status"] == "over"
    assert s["warning"]


def test_summary_by_capability():
    client.post("/api/usage-ledger/entries", json={"workspace_id": "v50cap", "capability": "text", "units": 100, "estimated_cost": 0.2})
    client.post("/api/usage-ledger/entries", json={"workspace_id": "v50cap", "capability": "image", "units": 1, "estimated_cost": 0.4})
    s = client.get("/api/usage-ledger/summary?workspace_id=v50cap").json()
    assert s["total_estimated_cost"] >= 0.6
    assert "text" in s["by_capability"]
    assert "image" in s["by_capability"]


def test_budget_update_overwrites():
    client.post("/api/usage-ledger/budgets", json={"workspace_id": "v50upd", "monthly_limit": 5})
    client.post("/api/usage-ledger/budgets", json={"workspace_id": "v50upd", "monthly_limit": 10})
    budgets = client.get("/api/usage-ledger/budgets").json()["budgets"]
    match = [b for b in budgets if b["workspace_id"] == "v50upd"]
    assert len(match) == 1
    assert match[0]["monthly_limit"] == 10


def test_governance_logged_on_record():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/usage-ledger/entries", json={"workspace_id": "v50gov", "capability": "text", "units": 1})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "usage_recorded" in actions


def test_analytics_includes_usage_fields():
    analytics = client.get("/api/analytics").json()
    for key in ("usage_entries", "usage_total_estimated_cost", "usage_budgets"):
        assert key in analytics


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/health-monitor/dashboard").status_code == 200
    assert client.get("/api/operating-layer/dashboard").status_code == 200
