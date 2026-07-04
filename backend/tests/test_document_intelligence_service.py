from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_compare_documents():
    r = client.post("/api/doc-intel/compare", json={"text_a": "the quick brown fox jumps", "text_b": "the quick brown dog sits"}).json()
    assert 0.0 <= r["similarity"] <= 1.0
    assert "verdict" in r
    assert "fox" in r["only_in_a"] or "jumps" in r["only_in_a"]


def test_ats_score():
    r = client.post("/api/doc-intel/ats", json={
        "resume_text": "Experienced python developer with fastapi and react and docker",
        "job_keywords": ["python", "fastapi", "kubernetes", "react"],
    }).json()
    assert r["ats_score"] == 75
    assert "kubernetes" in r["missing_keywords"]
    assert "python" in r["matched_keywords"]


def test_contract_risk_flags_clauses():
    r = client.post("/api/doc-intel/contract-risk", json={"text": "This agreement will automatically renew. Liability is limited. Termination for cause allowed."}).json()
    labels = {f["clause"] for f in r["flagged_clauses"]}
    assert "auto-renewal" in labels and "liability" in labels and "termination" in labels
    assert r["risk_level"] in ("medium", "high")


def test_csv_insight():
    r = client.post("/api/doc-intel/csv-insight", json={"text": "name,age,city\nAda,30,London\nBob,25,Paris"}).json()
    assert r["rows"] == 2 and r["columns"] == 3
    assert "name" in r["headers"]


def test_qa_keyword_retrieval():
    text = "EvolveAgent is local-first. The Master Agent routes requests. Governance logs every action."
    r = client.post("/api/doc-intel/qa", json={"text": text, "question": "what does the master agent do?"}).json()
    assert "master agent" in r["answer"].lower()
    assert r["confidence"] in ("low", "medium", "high")


def test_summary_and_analytics():
    summary = client.get("/api/doc-intel/summary").json()
    assert "capabilities" in summary and "contract_clause_types" in summary
    assert "doc_intel_capabilities" in client.get("/api/analytics").json()


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/doc-intel/compare", json={"text_a": "a b c", "text_b": "a b d"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "doc_compared" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/productivity/summary").status_code == 200
    assert client.get("/api/workflow-recommend/summary").status_code == 200
