from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_dataset(**overrides) -> dict:
    response = client.post("/api/training-lab/datasets", json={"name": overrides.get("name", "Test dataset")})
    assert response.status_code == 200
    return response.json()


def test_dataset_create():
    dataset = _create_dataset(name="Create-Test dataset")
    assert dataset["dataset_id"]
    assert dataset["name"] == "Create-Test dataset"
    listed = client.get("/api/training-lab/datasets").json()
    assert any(d["dataset_id"] == dataset["dataset_id"] for d in listed["datasets"])


def test_dataset_not_found():
    assert client.get("/api/training-lab/datasets/missing").status_code == 404
    assert client.post("/api/training-lab/datasets/missing/examples", json={"prompt": "hi"}).status_code == 404
    assert client.post("/api/training-lab/datasets/missing/export").status_code == 404


def test_secret_and_pii_redaction():
    dataset = _create_dataset()
    example = client.post(
        f"/api/training-lab/datasets/{dataset['dataset_id']}/examples",
        json={
            "prompt": "Contact me at john.doe@example.com or 415-555-1234. OPENAI_API_KEY=sk-abcdef1234567890",
            "completion": "My SSN is 123-45-6789.",
        },
    ).json()
    # Raw secrets/PII must not survive into stored text.
    assert "sk-abcdef1234567890" not in example["prompt"]
    assert "john.doe@example.com" not in example["prompt"]
    assert "415-555-1234" not in example["prompt"]
    assert "123-45-6789" not in example["completion"]
    assert example["redaction"]["secrets_detected"] is True
    assert example["redaction"]["pii_detected"] is True
    assert "[REDACTED_EMAIL]" in example["prompt"]


def test_approved_only_export_excludes_non_approved():
    dataset = _create_dataset()
    approved = client.post(
        f"/api/training-lab/datasets/{dataset['dataset_id']}/examples",
        json={"prompt": "Clean prompt", "completion": "Clean answer", "approved": True},
    ).json()
    pending = client.post(
        f"/api/training-lab/datasets/{dataset['dataset_id']}/examples",
        json={"prompt": "Pending prompt", "completion": "Pending answer"},
    ).json()
    rejected = client.post(
        f"/api/training-lab/datasets/{dataset['dataset_id']}/examples",
        json={"prompt": "Bad prompt", "completion": "Bad answer"},
    ).json()
    client.patch(f"/api/training-lab/examples/{rejected['example_id']}", json={"status": "rejected"})

    export = client.post(f"/api/training-lab/datasets/{dataset['dataset_id']}/export").json()
    assert export["approved_example_count"] == 1
    assert export["excluded_non_approved"] == 2
    assert len(export["jsonl_lines"]) == 1
    # The exported content is the approved example only.
    assert export["jsonl_lines"][0]["messages"][0]["content"] == "Clean prompt"
    assert pending["status"] == "pending"


def test_example_approve_reject_flow():
    dataset = _create_dataset()
    example = client.post(
        f"/api/training-lab/datasets/{dataset['dataset_id']}/examples",
        json={"prompt": "p", "completion": "c"},
    ).json()
    approved = client.patch(f"/api/training-lab/examples/{example['example_id']}", json={"status": "approved"}).json()
    assert approved["status"] == "approved"
    assert client.patch("/api/training-lab/examples/missing", json={"status": "approved"}).status_code == 404


def test_mock_training_run():
    run = client.post("/api/training-lab/runs", json={"base_model": "tiny-open-model", "method": "lora"}).json()
    assert run["run_id"]
    assert run["status"] == "mock_prepared"
    assert isinstance(run["lora_checklist"], list) and run["lora_checklist"]
    assert "no real training" in run["note"].lower()
    listed = client.get("/api/training-lab/runs").json()
    assert any(r["run_id"] == run["run_id"] for r in listed["runs"])


def test_comparison_creation():
    comparison = client.post(
        "/api/training-lab/comparisons",
        json={"baseline_model": "base", "candidate_model": "cand", "baseline_score": 0.6, "candidate_score": 0.8},
    ).json()
    assert comparison["comparison_id"]
    assert comparison["verdict"] == "candidate_better"
    listed = client.get("/api/training-lab/comparisons").json()
    assert any(c["comparison_id"] == comparison["comparison_id"] for c in listed["comparisons"])


def test_dashboard_counts_and_safety():
    dataset = _create_dataset()
    client.post(f"/api/training-lab/datasets/{dataset['dataset_id']}/examples", json={"prompt": "p", "completion": "c", "approved": True})
    body = client.get("/api/training-lab/dashboard").json()
    for key in ("total_datasets", "total_examples", "approved_examples", "rejected_examples", "total_exports", "total_runs", "safety_notes"):
        assert key in body
    assert any("does not train" in note.lower() for note in body["safety_notes"])


def test_governance_event_written():
    before = client.get("/api/governance").json()["total_events"]
    _create_dataset()
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "training_dataset_created" in actions


def test_regression_existing_endpoints():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/device-operator/dashboard").status_code == 200
    assert client.get("/api/company-brain/dashboard").status_code == 200
