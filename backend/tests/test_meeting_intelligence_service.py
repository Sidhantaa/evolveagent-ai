from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

TRANSCRIPT = (
    "We reviewed the roadmap. We decided to ship v79 next week. "
    "Alice will write the tests by Friday. Bob needs to update the docs. "
    "The meeting started at 10:00 and we agreed on the budget."
)


def test_analyze_extracts_decisions_and_actions():
    r = client.post("/api/meeting-intel/analyze", json={"transcript": TRANSCRIPT}).json()
    assert any("decided" in d.lower() or "agreed" in d.lower() for d in r["decisions"])
    assert len(r["action_items"]) >= 2
    assert "Alice" in r["owners"] or "Bob" in r["owners"]
    assert len(r["follow_up_drafts"]) >= 1
    assert any("draft" in f["draft"].lower() for f in r["follow_up_drafts"])


def test_timeline_captures_time_cues():
    r = client.post("/api/meeting-intel/analyze", json={"transcript": TRANSCRIPT}).json()
    assert any("10:00" in t or "friday" in t.lower() or "next week" in t.lower() for t in r["timeline"])


def test_to_goal_is_planning_only():
    goals_before = len(client.get("/api/goals").json())
    r = client.post("/api/meeting-intel/to-goal", json={"transcript": TRANSCRIPT, "title": "Ship v79"}).json()
    assert r["proposed_goal"]["title"] == "Ship v79"
    assert r["task_count"] >= 2
    assert "planning-only" in r["note"].lower()
    # Nothing was actually created.
    goals_after = len(client.get("/api/goals").json())
    assert goals_after == goals_before


def test_summary_and_analytics():
    assert "capabilities" in client.get("/api/meeting-intel/summary").json()
    assert "meeting_intel_capabilities" in client.get("/api/analytics").json()


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/meeting-intel/analyze", json={"transcript": "We agreed to proceed."})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "meeting_analyzed" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/business-intel/summary").status_code == 200
    assert client.get("/api/research-agent/summary").status_code == 200
