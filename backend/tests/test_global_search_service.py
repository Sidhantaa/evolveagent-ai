from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_sources_lists_all_collections():
    data = client.get("/api/search/sources").json()
    types = set(data["types"])
    for expected in ("goal", "agent", "file", "workflow", "report", "message"):
        assert expected in types
    assert data["total_indexed_items"] >= 0
    assert "excludes secrets" in data["note"].lower()


def test_search_finds_a_created_goal():
    slug = "v62searchtoken-alpha"
    client.post("/api/goals", json={"title": f"Ship {slug} release", "description": "search me"})
    result = client.get(f"/api/search?q={slug}").json()
    assert result["result_count"] >= 1
    assert any(slug in r["title"].lower() or slug in r["preview"].lower() for r in result["results"])
    hit = result["results"][0]
    for key in ("type", "label", "source_collection", "id", "title", "preview", "score"):
        assert key in hit


def test_type_filter_restricts_results():
    slug = "v62typefilter-beta"
    client.post("/api/goals", json={"title": f"{slug} goal", "description": "x"})
    # Filtering to a type that can't contain this token yields no results.
    result = client.get(f"/api/search?q={slug}&types=agent").json()
    assert all(r["type"] == "agent" for r in result["results"])


def test_empty_query_is_rejected():
    assert client.get("/api/search?q=").status_code == 422


def test_search_is_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/search?q=anything")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {e.get("action_type") for e in after["recent_events"]}
    assert "global_search" in actions


def test_analytics_includes_search_metrics():
    analytics = client.get("/api/analytics").json()
    for key in ("search_sources", "search_indexed_items"):
        assert key in analytics


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/master-agent/summary").status_code == 200
