from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _ws():
    d = client.post("/api/workspaces", json={"name": "v78 BI ws"}).json()
    return d.get("workspace_id") or d.get("id") or (d.get("workspace") or {}).get("workspace_id")


def test_dashboard_has_sections():
    dash = client.get("/api/business-intel/dashboard").json()
    for key in ("kpis", "lead_pipeline", "proposal_tracker", "revenue_forecast", "risk_register"):
        assert key in dash
    assert "MOCK" in dash["revenue_forecast"]["note"].upper()


def test_pipeline_reflects_leads():
    wid = _ws()
    client.post("/api/business/leads", json={"name": "Acme", "status": "won", "workspace_id": wid})
    client.post("/api/business/leads", json={"name": "Beta", "status": "lost", "workspace_id": wid})
    dash = client.get(f"/api/business-intel/dashboard?workspace_id={wid}").json()
    assert dash["kpis"]["total_leads"] >= 2
    assert dash["kpis"]["win_rate_pct"] == 50  # 1 won of 2 closed
    assert dash["lead_pipeline"]["by_stage"].get("won", 0) >= 1


def test_revenue_forecast_is_mock_and_numeric():
    wid = _ws()
    client.post("/api/business/leads", json={"name": "Gamma", "status": "won", "workspace_id": wid})
    dash = client.get(f"/api/business-intel/dashboard?workspace_id={wid}").json()
    assert isinstance(dash["revenue_forecast"]["mock_forecast_usd"], int)
    assert dash["revenue_forecast"]["mock_forecast_usd"] >= 5000  # 1 won * 5000


def test_empty_pipeline_flags_risk():
    wid = _ws()
    dash = client.get(f"/api/business-intel/dashboard?workspace_id={wid}").json()
    assert any("Empty pipeline" in r["title"] for r in dash["risk_register"]["risks"])


def test_report_markdown():
    r = client.get("/api/business-intel/report").json()
    assert r["format"] == "markdown"
    assert "Business Report" in r["content"]
    assert "executive_summary" in r


def test_summary_and_analytics():
    assert "capabilities" in client.get("/api/business-intel/summary").json()
    analytics = client.get("/api/analytics").json()
    for key in ("business_intel_leads", "business_intel_proposals"):
        assert key in analytics


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/business-intel/dashboard")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "business_intel_viewed" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/research-agent/summary").status_code == 200
    assert client.get("/api/code-intel/summary").status_code == 200
