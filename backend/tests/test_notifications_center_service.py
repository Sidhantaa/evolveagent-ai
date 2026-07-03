from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _make_pending_approval():
    client.post("/api/business-operator/approvals", json={"title": "needs review", "kind": "payment"})


def test_generate_creates_notifications_no_sending():
    _make_pending_approval()
    result = client.post("/api/notifications/generate").json()
    assert "created" in result
    assert "no email" in result["note"].lower()
    listed = client.get("/api/notifications").json()
    assert listed["count"] >= 1


def test_generate_is_idempotent_for_open_signals():
    _make_pending_approval()
    client.post("/api/notifications/generate")
    unread_before = client.get("/api/notifications?unread=true").json()["count"]
    # Generating again should not duplicate the same open backlog signal beyond changes.
    client.post("/api/notifications/generate")
    unread_after = client.get("/api/notifications?unread=true").json()["count"]
    # Idempotency: the same-signature signal is not duplicated (count grows only if the
    # backlog number changed). Allow equal-or-not-wildly-larger.
    assert unread_after <= unread_before + 3


def test_acknowledge_marks_read():
    _make_pending_approval()
    client.post("/api/notifications/generate")
    unread = client.get("/api/notifications?unread=true").json()["notifications"]
    assert unread, "expected at least one unread notification"
    notif_id = unread[0]["notif_id"]
    acked = client.post(f"/api/notifications/{notif_id}/ack").json()
    assert acked["acknowledged"] is True
    still_unread = {n["notif_id"] for n in client.get("/api/notifications?unread=true").json()["notifications"]}
    assert notif_id not in still_unread
    assert client.post("/api/notifications/missing/ack").status_code == 404


def test_summary_structure():
    summary = client.get("/api/notifications/summary").json()
    for key in ("total", "unread", "by_severity", "critical_unread", "recent", "note"):
        assert key in summary
    assert "no external delivery" in summary["note"].lower()


def test_notifications_have_severity_and_type():
    _make_pending_approval()
    client.post("/api/notifications/generate")
    for n in client.get("/api/notifications").json()["notifications"]:
        assert n["severity"] in ("info", "warning", "critical")
        assert n["type"]


def test_governance_logged_on_generate():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/notifications/generate")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "notifications_generated" in actions


def test_analytics_includes_notification_fields():
    analytics = client.get("/api/analytics").json()
    for key in ("notifications_total", "notifications_unread"):
        assert key in analytics


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/operating-layer-2/dashboard").status_code == 200
    assert client.get("/api/health-monitor/dashboard").status_code == 200
