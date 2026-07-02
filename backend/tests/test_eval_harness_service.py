from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_suite(**overrides) -> dict:
    payload = {
        "name": overrides.get("name", "Quality suite"),
        "cases": overrides.get("cases", [
            {"prompt": "Explain governance", "reference_answer": "Governance logs every action and blocks risky ones.", "expected_keywords": ["governance", "logs", "blocks"]},
            {"prompt": "Explain memory", "reference_answer": "Memory is scored and retrieved locally.", "expected_keywords": ["memory", "local", "scored"]},
        ]),
    }
    response = client.post("/api/eval-harness/suites", json=payload)
    assert response.status_code == 200
    return response.json()


def test_create_and_list_suite():
    suite = _create_suite()
    assert suite["suite_id"]
    assert suite["case_count"] == 2
    listed = client.get("/api/eval-harness/suites").json()
    assert any(s["suite_id"] == suite["suite_id"] for s in listed["suites"])


def test_run_suite_produces_scorecard():
    suite = _create_suite()
    run = client.post(f"/api/eval-harness/suites/{suite['suite_id']}/run").json()
    assert run["run_id"]
    assert 0.0 <= run["score"] <= 1.0
    assert run["case_count"] == 2
    assert "cases" in run and len(run["cases"]) == 2
    for case in run["cases"]:
        assert "score" in case and "matched_keywords" in case
    assert client.post("/api/eval-harness/suites/missing/run").status_code == 404


def test_run_is_deterministic():
    suite = _create_suite()
    first = client.post(f"/api/eval-harness/suites/{suite['suite_id']}/run").json()
    second = client.post(f"/api/eval-harness/suites/{suite['suite_id']}/run").json()
    assert first["score"] == second["score"]  # deterministic, mock-safe


def test_perfect_and_zero_scores():
    perfect = _create_suite(name="perfect", cases=[
        {"prompt": "p", "reference_answer": "alpha beta gamma", "expected_keywords": ["alpha", "beta", "gamma"]},
    ])
    run = client.post(f"/api/eval-harness/suites/{perfect['suite_id']}/run").json()
    assert run["score"] == 1.0
    zero = _create_suite(name="zero", cases=[
        {"prompt": "p", "reference_answer": "nothing relevant here", "expected_keywords": ["missing1", "missing2"]},
    ])
    run = client.post(f"/api/eval-harness/suites/{zero['suite_id']}/run").json()
    assert run["score"] == 0.0


def test_regression_tracking():
    suite = _create_suite()
    client.post(f"/api/eval-harness/suites/{suite['suite_id']}/run")
    client.post(f"/api/eval-harness/suites/{suite['suite_id']}/run")
    reg = client.get(f"/api/eval-harness/suites/{suite['suite_id']}/regression").json()
    assert reg["runs"] >= 2
    assert "delta" in reg
    assert reg["regressed"] is False  # same deterministic score → no regression


def test_list_runs_filtered():
    suite = _create_suite()
    client.post(f"/api/eval-harness/suites/{suite['suite_id']}/run")
    runs = client.get(f"/api/eval-harness/runs?suite_id={suite['suite_id']}").json()
    assert all(r["suite_id"] == suite["suite_id"] for r in runs["runs"])
    assert runs["count"] >= 1


def test_summary_and_analytics():
    suite = _create_suite()
    client.post(f"/api/eval-harness/suites/{suite['suite_id']}/run")
    s = client.get("/api/eval-harness/summary").json()
    for key in ("suite_count", "run_count", "latest_score", "regressed_runs", "note"):
        assert key in s
    analytics = client.get("/api/analytics").json()
    for key in ("eval_suites", "eval_runs", "eval_regressed_runs"):
        assert key in analytics


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    suite = _create_suite()
    client.post(f"/api/eval-harness/suites/{suite['suite_id']}/run")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "eval_suite_created" in actions or "eval_suite_run" in actions


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/retrieval/summary").status_code == 200
    assert client.get("/api/operating-layer/dashboard").status_code == 200
