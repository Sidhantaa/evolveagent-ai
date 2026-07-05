from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_dashboard_has_all_sections():
    # Generate a governance event first.
    client.post("/api/run", json={"user_input": "Warm up governance."})
    dash = client.get("/api/governance-console/dashboard").json()
    for key in ("total_events", "blocked_events", "blocked_ratio_pct", "by_risk", "by_permission_level",
                "top_actions", "policy_violations", "secret_redactions", "prompt_injection_warnings",
                "approval_audit", "external_action_audit"):
        assert key in dash
    assert dash["total_events"] >= 1
    assert isinstance(dash["top_actions"], list)


def test_risk_buckets_sum_to_total():
    dash = client.get("/api/governance-console/dashboard").json()
    by_risk = dash["by_risk"]
    assert by_risk["low"] + by_risk["medium"] + by_risk["high"] == dash["total_events"]


def test_report_markdown_and_json():
    md = client.get("/api/governance-console/report?format=markdown").json()
    assert md["format"] == "markdown"
    assert "Governance Report" in md["content"]
    js = client.get("/api/governance-console/report?format=json").json()
    assert js["format"] == "json"
    assert js["content"].strip().startswith("{")


def test_summary_and_analytics():
    assert "total_events" in client.get("/api/governance-console/summary").json()
    analytics = client.get("/api/analytics").json()
    for key in ("governance_console_events", "governance_console_blocked"):
        assert key in analytics


def test_view_is_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/governance-console/dashboard")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "governance_console_viewed" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/permissions/summary").status_code == 200
    assert client.get("/api/collaboration/summary").status_code == 200
