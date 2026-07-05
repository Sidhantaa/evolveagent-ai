from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

SOURCES = [
    {"title": "A", "text": "Solar power is reliable and affordable, growing 20% in 2021 per https://example.com."},
    {"title": "B", "text": "Solar power is not reliable and not affordable. Wind is better."},
]


def test_compare_sources():
    r = client.post("/api/research-agent/compare", json={"sources": SOURCES}).json()
    assert r["source_count"] == 2
    assert len(r["pairs"]) == 1
    assert "agreement" in r["pairs"][0]


def test_claim_evidence_table():
    r = client.post("/api/research-agent/claims", json={"text": SOURCES[0]["text"]}).json()
    assert r["claim_count"] + r["evidence_count"] == len(r["rows"])
    assert any(row["type"] == "evidence" for row in r["rows"])  # has number + url


def test_contradiction_detection():
    r = client.post("/api/research-agent/contradictions", json={"sources": SOURCES}).json()
    assert r["count"] >= 1  # "reliable" vs "not reliable"


def test_citation_quality():
    r = client.post("/api/research-agent/citation-quality", json={"sources": SOURCES}).json()
    assert "average_score" in r
    a = next(row for row in r["rows"] if row["title"] == "A")
    assert a["score"] >= 50  # url + year present


def test_bias_flags():
    r = client.post("/api/research-agent/bias", json={"text": "This is obviously the best ever and everyone always agrees."}).json()
    assert r["count"] >= 2
    assert r["risk"] in ("medium", "high")


def test_brief_generation():
    r = client.post("/api/research-agent/brief", json={"topic": "Solar energy", "sources": SOURCES}).json()
    assert r["format"] == "markdown"
    assert "Research Brief: Solar energy" in r["content"]
    assert "average_citation_quality" in r


def test_summary_and_analytics():
    assert "capabilities" in client.get("/api/research-agent/summary").json()
    assert "research_agent_capabilities" in client.get("/api/analytics").json()


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/research-agent/bias", json={"text": "always never"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "research_bias_flags" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/code-intel/summary").status_code == 200
    assert client.get("/api/doc-intel/summary").status_code == 200
