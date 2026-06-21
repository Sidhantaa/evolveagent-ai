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


def test_controlled_research_search_api():
    # 1. Test mock research search directly
    search_response = client.post(
        "/api/research/search",
        json={
            "query": "Compare real image API provider options",
            "max_results": 3,
        },
    )
    assert search_response.status_code == 200
    res = search_response.json()
    assert res["query"] == "Compare real image API provider options"
    assert res["provider"] == "mock_research_search"
    assert res["external_fetch_used"] is False
    assert len(res["results"]) > 0
    assert len(res["results"]) <= 3

    # Check shape & credibility
    for item in res["results"]:
        assert "title" in item
        assert "url" in item
        assert "publisher" in item
        assert "snippet" in item
        assert "credibility_score" in item
        assert item["credibility_label"] in ["low", "medium", "high"]

    # 2. Test search with missing research session ID (should return 404)
    missing_session_response = client.post(
        "/api/research/sessions/non-existent-session-id/search",
        json={
            "query": "Compare real image API provider options",
            "max_results": 2,
        },
    )
    assert missing_session_response.status_code == 404

    # 3. Create a session, search & add sources
    workspace_id = routes.workspace_service.default_workspace_id()
    create_response = client.post(
        "/api/research/sessions",
        json={
            "workspace_id": workspace_id,
            "query": "Search for cloud security and governance policies",
        },
    )
    assert create_response.status_code == 200
    session = create_response.json()
    assert session["status"] == "pending_approval"

    # Run controlled search for this session
    session_search_response = client.post(
        f"/api/research/sessions/{session['research_id']}/search",
        json={
            "query": "cloud security and governance policies",
            "max_results": 2,
        },
    )
    assert session_search_response.status_code == 200
    updated_session = session_search_response.json()

    # Confirm sources are added
    assert updated_session["source_count"] > 0
    assert updated_session["source_count"] <= 2
    assert updated_session["search_result"]["provider"] == "mock_research_search"
    assert updated_session["search_result"]["external_fetch_used"] is False
    assert len(updated_session["sources_added"]) == updated_session["source_count"]

    # Confirm sources list has the new sources
    sources_response = client.get(f"/api/research/sessions/{session['research_id']}/sources")
    assert sources_response.status_code == 200
    sources = sources_response.json()
    assert len(sources) == updated_session["source_count"]
    for src in sources:
        assert src["research_id"] == session["research_id"]
        assert src["fetched"] is True
