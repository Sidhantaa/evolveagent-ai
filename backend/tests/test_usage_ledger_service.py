from fastapi.testclient import TestClient

from app.main import app
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService
from app.services.usage_ledger_service import UsageLedgerService

client = TestClient(app)


def _isolated_ledger(tmp_path) -> UsageLedgerService:
    storage = StorageService(data_dir=str(tmp_path / "data"))
    return UsageLedgerService(storage, GovernanceService(storage))


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
    # Unique per run (not the old hardcoded "v50budget") -- this test checks
    # exact under/near/over threshold boundaries against real, persistent
    # local app/data storage, so a literal workspace_id shared across every
    # local test run ever accumulates real cross-run spend and eventually
    # makes this comparison fail for reasons unrelated to the code under test.
    from uuid import uuid4
    workspace_id = f"v50budget-{uuid4().hex[:8]}"
    client.post("/api/usage-ledger/budgets", json={"workspace_id": workspace_id, "monthly_limit": 1.0})
    # Under budget.
    client.post("/api/usage-ledger/entries", json={"workspace_id": workspace_id, "capability": "other", "units": 1, "estimated_cost": 0.3})
    s = client.get(f"/api/usage-ledger/summary?workspace_id={workspace_id}").json()
    assert s["monthly_limit"] == 1.0
    assert s["budget_status"] == "under"
    # Near budget (>=80%).
    client.post("/api/usage-ledger/entries", json={"workspace_id": workspace_id, "capability": "other", "units": 1, "estimated_cost": 0.55})
    s = client.get(f"/api/usage-ledger/summary?workspace_id={workspace_id}").json()
    assert s["budget_status"] == "near"
    # Over budget.
    client.post("/api/usage-ledger/entries", json={"workspace_id": workspace_id, "capability": "other", "units": 1, "estimated_cost": 0.5})
    s = client.get(f"/api/usage-ledger/summary?workspace_id={workspace_id}").json()
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


def test_budget_status_ignores_spend_from_a_previous_month(tmp_path):
    """Numeric-correctness lens (round 41): monthly_limit is a per-CALENDAR-MONTH
    cap, but budget_status used to compare it against ALL-TIME cumulative spend --
    so a workspace that crossed its limit once stayed permanently "over" even in
    a brand-new month with $0 spent this month. Proven here by writing an entry
    with a real, deliberately-stale created_at (last month) directly into
    storage -- the same technique as record_usage(), just with the clock rolled
    back, so this exercises the exact production code path."""
    ledger = _isolated_ledger(tmp_path)
    ledger.set_budget({"workspace_id": "stale-spend", "monthly_limit": 1.0})

    from datetime import UTC, datetime, timedelta
    last_month = (datetime.now(UTC).replace(day=1) - timedelta(days=1)).isoformat()
    ledger.storage.append(ledger.entries_file, {
        "entry_id": "old-1", "workspace_id": "stale-spend", "capability": "other",
        "units": 1, "estimated_cost": 5.0, "mode": "mock", "note": "", "created_at": last_month,
    })

    summary = ledger.summary(workspace_id="stale-spend")

    assert summary["total_estimated_cost"] == 5.0  # all-time total still reflects it
    assert summary["current_month_cost"] == 0.0  # but nothing was spent THIS month
    assert summary["budget_status"] == "under"  # so the budget must not be "over"


def test_budget_status_reflects_only_current_month_spend(tmp_path):
    ledger = _isolated_ledger(tmp_path)
    ledger.set_budget({"workspace_id": "mixed-spend", "monthly_limit": 1.0})

    from datetime import UTC, datetime, timedelta
    last_month = (datetime.now(UTC).replace(day=1) - timedelta(days=1)).isoformat()
    ledger.storage.append(ledger.entries_file, {
        "entry_id": "old-2", "workspace_id": "mixed-spend", "capability": "other",
        "units": 1, "estimated_cost": 10.0, "mode": "mock", "note": "", "created_at": last_month,
    })
    ledger.record_usage({"workspace_id": "mixed-spend", "capability": "other", "units": 1, "estimated_cost": 0.6})

    summary = ledger.summary(workspace_id="mixed-spend")

    assert summary["total_estimated_cost"] == 10.6
    assert summary["current_month_cost"] == 0.6
    assert summary["budget_status"] == "under"  # 0.6 / 1.0 < 0.8, regardless of the old 10.0


def test_department_budget_status_also_reflects_current_month_only(tmp_path):
    """AgentDepartmentService.department_budget_status()/plan_run()'s budget gate
    call UsageLedgerService.summary() directly -- confirm the fix is inherited,
    since plan_run() previously permanently blocked runs as budget_exceeded once
    lifetime spend crossed the limit, in any month."""
    from app.services.agent_department_service import AgentDepartmentService
    from app.services.permission_service import PermissionService
    storage = StorageService(data_dir=str(tmp_path / "data"))
    governance = GovernanceService(storage)
    ledger = UsageLedgerService(storage, governance)
    departments = AgentDepartmentService(storage, governance, PermissionService(), usage_ledger=ledger)

    dept = departments.create_department(name="Engineering", permission_level="read_only")
    departments.set_department_budget(dept["department_id"], 1.0)
    workspace_key = departments._dept_workspace_key(dept["department_id"])

    from datetime import UTC, datetime, timedelta
    last_month = (datetime.now(UTC).replace(day=1) - timedelta(days=1)).isoformat()
    ledger.storage.append(ledger.entries_file, {
        "entry_id": "old-3", "workspace_id": workspace_key, "capability": "other",
        "units": 1, "estimated_cost": 50.0, "mode": "mock", "note": "", "created_at": last_month,
    })

    status = departments.department_budget_status(dept["department_id"])

    assert status["budget_status"] == "under"  # not permanently "over" from a prior month


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/health-monitor/dashboard").status_code == 200
    assert client.get("/api/operating-layer/dashboard").status_code == 200
