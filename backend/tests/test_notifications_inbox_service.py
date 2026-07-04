from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_generate_returns_items_and_grouping():
    data = client.post("/api/notifications-inbox/generate").json()
    assert "generated" in data
    assert "items" in data and "by_severity" in data
    for item in data["items"]:
        for key in ("id", "type", "severity", "title", "source_route", "resolved"):
            assert key in item
        assert item["severity"] in ("critical", "warning", "info")


def test_generation_is_idempotent():
    client.post("/api/notifications-inbox/generate")
    first = client.get("/api/notifications-inbox").json()["count"]
    client.post("/api/notifications-inbox/generate")
    second = client.get("/api/notifications-inbox").json()["count"]
    # No unresolved duplicates created on a second pass.
    assert second == first


def test_items_sorted_by_severity():
    items = client.get("/api/notifications-inbox").json()["items"]
    order = {"critical": 0, "warning": 1, "info": 2}
    sevs = [order.get(i["severity"], 3) for i in items]
    assert sevs == sorted(sevs)


def test_resolve_removes_from_unresolved():
    client.post("/api/notifications-inbox/generate")
    items = client.get("/api/notifications-inbox").json()["items"]
    if items:
        target = items[0]["id"]
        res = client.post(f"/api/notifications-inbox/{target}/resolve").json()
        assert res["resolved"] is True
        remaining = client.get("/api/notifications-inbox").json()["items"]
        assert all(i["id"] != target for i in remaining)
        # still visible with include_resolved
        withres = client.get("/api/notifications-inbox?include_resolved=true").json()["items"]
        assert any(i["id"] == target for i in withres)


def test_resolve_unknown_404():
    assert client.post("/api/notifications-inbox/nope/resolve").status_code == 404


def test_summary_and_analytics():
    summary = client.get("/api/notifications-inbox/summary").json()
    assert "unresolved_count" in summary and "by_severity" in summary
    analytics = client.get("/api/analytics").json()
    for key in ("notifications_inbox_total", "notifications_inbox_unresolved"):
        assert key in analytics


def test_generate_is_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/notifications-inbox/generate")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "notifications_inbox_generated" in {e.get("action_type") for e in after["recent_events"]}


def test_v56_center_still_works():
    # additive: the original notifications center is untouched
    assert client.get("/api/notifications/summary").status_code == 200
    assert client.get("/api/provider-control/summary").status_code == 200
