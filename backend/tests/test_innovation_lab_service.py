from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_research_create_and_list():
    item = client.post(
        "/api/innovation-lab/research",
        json={"title": "Market sizing", "source": "internal note", "credibility": "high", "tags": ["market"]},
    ).json()
    assert item["research_id"]
    assert item["credibility"] == "high"
    listed = client.get("/api/innovation-lab/research").json()
    assert any(r["research_id"] == item["research_id"] for r in listed["research"])


def test_competitor_create_and_list():
    comp = client.post(
        "/api/innovation-lab/competitors",
        json={"name": "Acme AI", "category": "agents", "strengths": ["brand"], "weaknesses": ["pricing"]},
    ).json()
    assert comp["competitor_id"]
    listed = client.get("/api/innovation-lab/competitors").json()
    assert any(c["competitor_id"] == comp["competitor_id"] for c in listed["competitors"])


def test_trend_create_and_list():
    trend = client.post(
        "/api/innovation-lab/trends",
        json={"title": "Local-first AI", "direction": "rising", "evidence_notes": ["privacy demand"]},
    ).json()
    assert trend["trend_id"]
    assert trend["direction"] == "rising"
    listed = client.get("/api/innovation-lab/trends").json()
    assert any(t["trend_id"] == trend["trend_id"] for t in listed["trends"])


def test_idea_scoring_and_sorting():
    high = client.post(
        "/api/innovation-lab/ideas",
        json={"title": "High idea", "impact": 5, "feasibility": 5, "novelty": 5, "risk": 1},
    ).json()
    low = client.post(
        "/api/innovation-lab/ideas",
        json={"title": "Low idea", "impact": 1, "feasibility": 1, "novelty": 1, "risk": 5},
    ).json()
    assert "composite_score" in high
    assert high["composite_score"] > low["composite_score"]
    ideas = client.get("/api/innovation-lab/ideas").json()["ideas"]
    scores = [i["composite_score"] for i in ideas]
    assert scores == sorted(scores, reverse=True)


def test_experiment_create():
    exp = client.post(
        "/api/innovation-lab/experiments",
        json={"title": "Onboarding test", "hypothesis": "Shorter onboarding lifts activation", "success_metrics": ["activation rate"]},
    ).json()
    assert exp["experiment_id"]
    assert exp["status"] == "planned"
    listed = client.get("/api/innovation-lab/experiments").json()
    assert any(e["experiment_id"] == exp["experiment_id"] for e in listed["experiments"])


def test_prototype_create():
    proto = client.post(
        "/api/innovation-lab/prototypes",
        json={"title": "MVP prototype", "features": ["core flow"], "risks": ["scope"]},
    ).json()
    assert proto["prototype_id"]
    assert proto["phases"]
    listed = client.get("/api/innovation-lab/prototypes").json()
    assert any(p["prototype_id"] == proto["prototype_id"] for p in listed["prototypes"])


def test_report_generation():
    client.post("/api/innovation-lab/research", json={"title": "Report seed"})
    report = client.post("/api/innovation-lab/reports", json={"title": "Q3 innovation"}).json()
    assert report["report_id"]
    assert "top_ideas" in report
    assert report["headline"]
    listed = client.get("/api/innovation-lab/reports").json()
    assert any(r["report_id"] == report["report_id"] for r in listed["reports"])


def test_dashboard_works():
    body = client.get("/api/innovation-lab/dashboard").json()
    for key in ("research_count", "competitor_count", "trend_count", "idea_count", "experiment_count", "prototype_count", "note"):
        assert key in body
    assert "no web browsing" in body["note"].lower()


def test_governance_event_written():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/innovation-lab/ideas", json={"title": "Gov idea"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "innovation_idea_created" in actions


def test_regression_existing_endpoints():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/executive-board/dashboard").status_code == 200
