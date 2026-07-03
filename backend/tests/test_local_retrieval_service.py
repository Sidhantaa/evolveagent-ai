from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _index(**payload) -> dict:
    response = client.post("/api/retrieval/documents", json=payload)
    assert response.status_code == 200
    return response.json()


def test_index_chunks_document():
    long_text = " ".join(f"Sentence number {i} about local retrieval and governance." for i in range(40))
    doc = _index(workspace_id="v51a", title="Guide", content=long_text)
    assert doc["doc_id"]
    assert doc["chunk_count"] >= 2  # long content chunked
    listed = client.get("/api/retrieval/documents?workspace_id=v51a").json()
    assert any(d["doc_id"] == doc["doc_id"] for d in listed["documents"])


def test_query_returns_relevant_chunk_with_citation():
    _index(workspace_id="v51q", title="Policies", content="The MCP policy engine enforces tighten-only deny rules before planning. Approvals are governed.")
    result = client.post("/api/retrieval/query", json={"workspace_id": "v51q", "query": "tighten-only deny policy"}).json()
    assert result["result_count"] >= 1
    top = result["results"][0]
    assert top["score"] > 0
    assert top["citation"]
    assert "matched_terms" in top
    assert "no external vector database" in result["note"].lower()


def test_query_scoring_ranks_better_match_first():
    _index(workspace_id="v51rank", title="A", content="Cats and dogs are common household pets.")
    _index(workspace_id="v51rank", title="B", content="Quantum computing uses qubits and superposition.")
    result = client.post("/api/retrieval/query", json={"workspace_id": "v51rank", "query": "quantum qubits superposition"}).json()
    assert result["results"][0]["title"] == "B"


def test_query_no_match_returns_empty():
    _index(workspace_id="v51none", title="X", content="Apples oranges bananas.")
    result = client.post("/api/retrieval/query", json={"workspace_id": "v51none", "query": "zzzzz nonexistentterm"}).json()
    assert result["result_count"] == 0


def test_workspace_isolation_in_query():
    _index(workspace_id="v51w1", title="W1", content="Alpha beta gamma retrieval.")
    _index(workspace_id="v51w2", title="W2", content="Alpha beta gamma retrieval.")
    result = client.post("/api/retrieval/query", json={"workspace_id": "v51w1", "query": "alpha beta"}).json()
    assert all(r["title"] == "W1" for r in result["results"])


def test_summary_and_analytics():
    _index(workspace_id="v51s", title="S", content="Some content for summary.")
    s = client.get("/api/retrieval/summary?workspace_id=v51s").json()
    for key in ("document_count", "chunk_count", "query_count", "note"):
        assert key in s
    analytics = client.get("/api/analytics").json()
    for key in ("retrieval_documents", "retrieval_chunks", "retrieval_queries"):
        assert key in analytics


def test_governance_logged_on_index_and_query():
    before = client.get("/api/governance").json()["total_events"]
    _index(workspace_id="v51gov", title="G", content="Governed retrieval content.")
    client.post("/api/retrieval/query", json={"workspace_id": "v51gov", "query": "governed content"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "retrieval_document_indexed" in actions or "retrieval_query" in actions


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/usage-ledger/summary").status_code == 200
    assert client.get("/api/operating-layer/dashboard").status_code == 200
