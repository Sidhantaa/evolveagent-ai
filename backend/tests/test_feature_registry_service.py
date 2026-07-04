from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_registry_lists_features():
    data = client.get("/api/features").json()
    assert data["total_features"] >= 30
    assert data["feature_count"] == data["total_features"]
    assert "Core" in data["categories"]
    first = data["features"][0]
    for key in ("key", "name", "version", "category", "service", "route", "status"):
        assert key in first


def test_search_filters_features():
    data = client.get("/api/features?q=mcp").json()
    assert data["feature_count"] >= 1
    assert all("mcp" in (f["name"] + f["key"] + f["route"]).lower() for f in data["features"])


def test_status_filter():
    data = client.get("/api/features?status=demo_safe").json()
    assert all("demo_safe" in f["status"] for f in data["features"])


def test_route_map():
    data = client.get("/api/features/route-map").json()
    assert data["count"] >= 30
    assert any(entry["route"] == "/api/master-agent" for entry in data["route_map"])


def test_try_feature_returns_open_route():
    data = client.post("/api/features/global-search/try").json()
    assert data["open_route"] == "/api/search"
    assert "Global Search" in data["launch_note"]


def test_try_unknown_feature_404():
    assert client.post("/api/features/nope-nope/try").status_code == 404


def test_summary_and_analytics():
    summary = client.get("/api/features/summary").json()
    for key in ("total_features", "by_category", "by_status"):
        assert key in summary
    analytics = client.get("/api/analytics").json()
    for key in ("registry_total_features", "registry_demo_safe_features"):
        assert key in analytics


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/features")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {e.get("action_type") for e in after["recent_events"]}
    assert "feature_registry_listed" in actions


def test_existing_endpoints_still_work():
    assert client.get("/api/home").status_code == 200
    assert client.get("/api/activity/summary").status_code == 200
