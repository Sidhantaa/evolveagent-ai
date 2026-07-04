from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_timeline_aggregates_events():
    # Generate some activity: a run (governance events) and a goal.
    client.post("/api/run", json={"user_input": "Warm up the timeline."})
    client.post("/api/goals", json={"title": "v63 timeline goal", "description": "x"})
    data = client.get("/api/activity").json()
    assert data["event_count"] >= 1
    assert "governance" in data["types"]
    types_present = set(data["by_type"].keys())
    assert types_present  # at least one type represented
    first = data["events"][0]
    for key in ("type", "source_collection", "title", "timestamp", "governance_linked"):
        assert key in first


def test_timeline_orders_newest_first():
    data = client.get("/api/activity?limit=20").json()
    timestamps = [e["timestamp"] for e in data["events"] if e["timestamp"]]
    assert timestamps == sorted(timestamps, reverse=True)


def test_type_filter():
    data = client.get("/api/activity?types=governance").json()
    assert all(e["type"] == "governance" for e in data["events"])


def test_export_markdown_and_json():
    md = client.get("/api/activity/export?format=markdown").json()
    assert md["format"] == "markdown"
    assert "Activity Timeline" in md["content"]
    js = client.get("/api/activity/export?format=json").json()
    assert js["format"] == "json"
    assert js["content"].strip().startswith("[")


def test_summary_and_analytics():
    summary = client.get("/api/activity/summary").json()
    for key in ("total_events", "by_type", "types"):
        assert key in summary
    analytics = client.get("/api/analytics").json()
    for key in ("activity_timeline_events", "activity_timeline_sources"):
        assert key in analytics


def test_timeline_is_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/activity")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {e.get("action_type") for e in after["recent_events"]}
    assert "activity_timeline_viewed" in actions


def test_existing_endpoints_still_work():
    assert client.get("/api/search/sources").status_code == 200
    assert client.get("/api/master-agent/summary").status_code == 200
