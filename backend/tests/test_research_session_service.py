from fastapi.testclient import TestClient

from app.main import app
from app.api import routes


client = TestClient(app)


def test_research_session_lifecycle_and_report():
    workspace_id = routes.workspace_service.default_workspace_id()
    create_response = client.post(
        "/api/research/sessions",
        json={
            "workspace_id": workspace_id,
            "query": "Compare real image API provider readiness options",
            "notes": "Use governed sources only.",
        },
    )

    assert create_response.status_code == 200
    session = create_response.json()
    assert session["status"] == "pending_approval"
    assert session["approval_required"] is True

    approve_response = client.post(f"/api/research/sessions/{session['research_id']}/approve")
    assert approve_response.status_code == 200
    assert approve_response.json()["status"] == "active"

    source_response = client.post(
        f"/api/research/sessions/{session['research_id']}/sources",
        json={
            "title": "OpenAI image generation docs",
            "url": "https://openai.com/api/images",
            "publisher": "OpenAI",
            "snippet": "Official documentation for OpenAI image generation provider configuration and capabilities.",
        },
    )
    assert source_response.status_code == 200
    source = source_response.json()
    assert source["credibility_score"] >= 70
    assert source["credibility_reasons"]

    citation_response = client.post(
        f"/api/research/sessions/{session['research_id']}/citations",
        json={
            "source_id": source["source_id"],
            "claim": "OpenAI can be used as the real image provider when configured.",
        },
    )
    assert citation_response.status_code == 200
    assert citation_response.json()["source_id"] == source["source_id"]

    report_response = client.get(f"/api/research/sessions/{session['research_id']}/report")
    assert report_response.status_code == 200
    report = report_response.json()
    assert report["source_count"] == 1
    assert report["citation_count"] == 1
    assert report["top_sources"][0]["source_id"] == source["source_id"]
    assert "OpenAI can be used" in report["cited_claims"][0]


def test_research_session_reject_and_governance_log():
    create_response = client.post(
        "/api/research/sessions",
        json={"query": "Research risky automation vendors"},
    )
    session = create_response.json()

    reject_response = client.post(f"/api/research/sessions/{session['research_id']}/reject")
    assert reject_response.status_code == 200
    assert reject_response.json()["status"] == "rejected"

    governance = client.get("/api/governance").json()
    assert any(
        event.get("run_id") == session["research_id"]
        and event.get("action_type") == "research_approval_decision"
        and event.get("blocked") is True
        for event in governance["recent_events"]
    )


def test_research_unknown_session_returns_404():
    response = client.get("/api/research/sessions/not-found")
    assert response.status_code == 404

    source_response = client.post(
        "/api/research/sessions/not-found/sources",
        json={"title": "No source", "url": "https://example.com"},
    )
    assert source_response.status_code == 404
