from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

CONTRIBS = [
    {"role": "researcher", "position": "We should adopt kubernetes because the data shows it scales better."},
    {"role": "architect", "position": "We should adopt kubernetes; it scales and standardizes deployment."},
    {"role": "skeptic", "position": "We should not adopt kubernetes, it adds complexity and cost."},
]


def test_analyze_produces_all_sections():
    r = client.post("/api/collaboration/analyze", json={"topic": "Adopt Kubernetes?", "contributions": CONTRIBS}).json()
    for key in ("conversation", "consensus_summary", "disagreement_notes", "reviewer_pass", "final_decision"):
        assert key in r
    assert len(r["conversation"]) == 3


def test_consensus_and_disagreement():
    r = client.post("/api/collaboration/analyze", json={"topic": "K8s", "contributions": CONTRIBS}).json()
    assert "kubernetes" in r["consensus_summary"]  # shared across majority
    # skeptic negates → at least one disagreement flagged
    assert any("skeptic" in d["between"] for d in r["disagreement_notes"])


def test_final_decision_is_central():
    r = client.post("/api/collaboration/analyze", json={"topic": "K8s", "contributions": CONTRIBS}).json()
    assert r["final_decision"]["recommended_by"] in ("researcher", "architect")
    assert "rationale" in r["final_decision"]


def test_reviewer_flags_no_evidence():
    contribs = [{"role": "a", "position": "Just do it."}, {"role": "b", "position": "I agree."}]
    r = client.post("/api/collaboration/analyze", json={"topic": "x", "contributions": contribs}).json()
    assert len(r["reviewer_pass"]) >= 1


def test_summary_and_analytics():
    assert "capabilities" in client.get("/api/collaboration/summary").json()
    assert "agent_collaboration_capabilities" in client.get("/api/analytics").json()


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/collaboration/analyze", json={"topic": "t", "contributions": CONTRIBS})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "collaboration_analyzed" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/meeting-intel/summary").status_code == 200
    assert client.get("/api/business-intel/summary").status_code == 200
