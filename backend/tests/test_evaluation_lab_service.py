import json

from fastapi.testclient import TestClient

from app.main import app
from app.services.evaluation_lab_service import EvaluationLabService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


client = TestClient(app)


def test_evaluation_lab_creates_default_benchmarks(tmp_path):
    storage = StorageService(str(tmp_path))
    service = EvaluationLabService(storage, GovernanceService(storage))

    benchmarks = service.list_benchmarks()

    assert len(benchmarks) >= 7
    assert {item["task_type"] for item in benchmarks} >= {"coding", "recording_summary", "app_automation"}


def test_evaluation_run_scores_existing_history(tmp_path):
    storage = StorageService(str(tmp_path))
    storage.append(
        "agent_analytics.json",
        {
            "run_id": "run-1",
            "workspace_id": "ws-1",
            "task_type": "coding",
            "agents_used": ["Research Agent", "Writing Agent"],
            "overall_judge_score": 88,
            "latency_ms": 120,
            "fallback_used": False,
        },
    )
    service = EvaluationLabService(storage, GovernanceService(storage))

    run = service.create_run(task_type="coding", workspace_id="ws-1")

    assert run["workspace_id"] == "ws-1"
    assert run["case_results"][0]["task_type"] == "coding"
    assert run["case_results"][0]["history_count"] == 1
    assert run["score"] >= 80


def test_evaluation_ab_test_compares_variants(tmp_path):
    storage = StorageService(str(tmp_path))
    for index, score in enumerate((90, 86, 88)):
        storage.append(
            "agent_analytics.json",
            {
                "run_id": f"openai-{index}",
                "workspace_id": "ws-1",
                "task_type": "coding",
                "provider": "openai",
                "model": "gpt-test",
                "overall_judge_score": score,
            },
        )
    for index, score in enumerate((72, 75, 73)):
        storage.append(
            "agent_analytics.json",
            {
                "run_id": f"mock-{index}",
                "workspace_id": "ws-1",
                "task_type": "coding",
                "provider": "mock",
                "model": "mock-agent-model",
                "overall_judge_score": score,
            },
        )
    service = EvaluationLabService(storage, GovernanceService(storage))

    result = service.create_ab_test("OpenAI vs Mock", "openai", "mock", workspace_id="ws-1")

    assert result["variant_a_count"] == 3
    assert result["variant_b_count"] == 3
    assert result["winner"] == "openai"


def test_evaluation_regression_detection(tmp_path):
    storage = StorageService(str(tmp_path))
    service = EvaluationLabService(storage, GovernanceService(storage))
    for score in (90, 92, 91):
        storage.append("evaluation_runs.json", {"evaluation_run_id": f"prior-{score}", "workspace_id": "ws-1", "score": score})

    service.create_run(task_type="image_generation", workspace_id="ws-1")
    regressions = service.regressions(workspace_id="ws-1")

    assert regressions["regression_count"] == 1
    assert regressions["recent_regressions"][0]["drop"] >= 10


def test_evaluation_export_formats(tmp_path):
    storage = StorageService(str(tmp_path))
    service = EvaluationLabService(storage, GovernanceService(storage))
    service.create_run(task_type="general")

    exported_json = json.loads(service.export(format="json"))
    exported_csv = service.export(format="csv")

    assert "dashboard" in exported_json
    assert "evaluation_run" in exported_csv


def test_evaluation_api_endpoints():
    benchmarks = client.get("/api/evaluation/benchmarks")
    assert benchmarks.status_code == 200
    assert benchmarks.json()["count"] >= 7

    run = client.post("/api/evaluation/runs", json={"task_type": "general", "notes": "api test"})
    assert run.status_code == 200
    assert run.json()["evaluation_run_id"]

    dashboard = client.get("/api/evaluation/dashboard")
    assert dashboard.status_code == 200
    assert "score_trend" in dashboard.json()

    ab_test = client.post(
        "/api/evaluation/ab-tests",
        json={"name": "General vs Mock", "variant_a": "general", "variant_b": "mock"},
    )
    assert ab_test.status_code == 200
    assert ab_test.json()["ab_test_id"]

    exported = client.get("/api/evaluation/export?format=csv")
    assert exported.status_code == 200
    assert "record_type" in exported.text
