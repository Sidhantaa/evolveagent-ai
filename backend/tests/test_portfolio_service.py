from fastapi.testclient import TestClient

from app.main import app
from app.services.governance_service import GovernanceService
from app.services.portfolio_service import PortfolioService
from app.services.storage_service import StorageService
from app.services.workspace_service import WorkspaceService

client = TestClient(app)


def _make_workspace(name: str) -> str:
    response = client.post("/api/workspaces", json={"name": name, "description": "Portfolio test"})
    assert response.status_code == 200
    return response.json()["workspace_id"]


def _make_goal_with_tasks(workspace_id: str, title: str, task_statuses: list[str]) -> str:
    created = client.post(
        "/api/goals",
        json={"title": title, "description": "Portfolio goal", "workspace_id": workspace_id},
    )
    assert created.status_code == 200
    goal_id = created.json()["goal"]["goal_id"]
    for index, status in enumerate(task_statuses):
        added = client.post(
            f"/api/goals/{goal_id}/tasks",
            json={"title": f"Task {index}", "estimated_effort": "medium"},
        )
        assert added.status_code == 200
        task_id = added.json()["task_id"]
        if status != "pending":
            client.patch(f"/api/goals/{goal_id}/tasks/{task_id}", json={"status": status})
    return goal_id


def test_dashboard_aggregates_workspaces_goals_and_tasks():
    workspace_id = _make_workspace("Portfolio Dashboard WS")
    _make_goal_with_tasks(workspace_id, "Dashboard goal", ["done", "blocked", "pending"])

    dashboard = client.get("/api/portfolio/dashboard").json()
    assert dashboard["total_workspaces"] >= 1
    assert dashboard["total_goals"] >= 1
    assert dashboard["total_tasks"] >= 3
    assert dashboard["completed_tasks"] >= 1
    assert dashboard["blocked_tasks"] >= 1
    assert isinstance(dashboard["workspace_summaries"], list)
    assert any(item["name"] == "Portfolio Dashboard WS" for item in dashboard["workspace_summaries"])
    summary = next(item for item in dashboard["workspace_summaries"] if item["name"] == "Portfolio Dashboard WS")
    assert "runs" not in summary  # internal fields are not leaked


def test_analytics_groups_by_workspace():
    workspace_id = _make_workspace("Portfolio Analytics WS")
    _make_goal_with_tasks(workspace_id, "Analytics goal", ["done", "pending"])

    analytics = client.get("/api/portfolio/analytics").json()
    assert "Portfolio Analytics WS" in analytics["runs_by_workspace"]
    assert "Portfolio Analytics WS" in analytics["task_completion_by_workspace"]
    completion = analytics["task_completion_by_workspace"]["Portfolio Analytics WS"]
    assert completion["total"] == 2
    assert completion["completed"] == 1
    assert isinstance(analytics["top_agents"], list)
    assert isinstance(analytics["top_task_types"], list)


def test_health_score_returns_score_rating_and_drivers():
    workspace_id = _make_workspace("Portfolio Health WS")
    _make_goal_with_tasks(workspace_id, "Health goal", ["done", "done", "pending"])

    health = client.get("/api/portfolio/health").json()
    assert 0 <= health["score"] <= 100
    assert health["rating"] in {"excellent", "good", "watch", "at_risk"}
    assert isinstance(health["drivers"], list) and health["drivers"]
    assert isinstance(health["risks"], list)
    assert isinstance(health["recommendations"], list) and health["recommendations"]
    assert "task_completion_rate" in health["metrics"]


def test_health_counts_only_portfolio_workspace_regressions(tmp_path):
    storage = StorageService(str(tmp_path))
    workspace_service = WorkspaceService(storage)
    governance_service = GovernanceService(storage)
    service = PortfolioService(storage, workspace_service, governance_service)
    workspace = workspace_service.create_workspace(
        {"name": "Scoped Regression Portfolio", "description": "test", "tags": []}
    )
    storage.append(
        "evaluation_regressions.json",
        {"regression_id": "orphan-regression", "workspace_id": "missing-workspace", "severity": "high"},
    )

    health = service.health()

    assert workspace["workspace_id"]
    assert health["metrics"]["regressions"] == 0


def test_executive_report_generated_and_persisted():
    _make_workspace("Portfolio Report WS")

    report = client.post("/api/portfolio/reports", json={}).json()
    assert report["title"] == "Portfolio Executive Summary"
    assert report["summary"]
    assert isinstance(report["highlights"], list) and report["highlights"]
    assert "report_id" in report

    history = client.get("/api/portfolio/reports").json()
    assert any(item["report_id"] == report["report_id"] for item in history)

    governance = client.get("/api/governance").json()
    assert any(
        event.get("action_type") == "portfolio_report_generated"
        for event in governance["recent_events"]
    )


def test_export_json_and_markdown():
    _make_workspace("Portfolio Export WS")

    json_export = client.get("/api/portfolio/export?format=json")
    assert json_export.status_code == 200
    assert json_export.headers["content-type"].startswith("application/json")
    assert '"dashboard"' in json_export.text

    md_export = client.get("/api/portfolio/export?format=markdown")
    assert md_export.status_code == 200
    assert md_export.headers["content-type"].startswith("text/markdown")
    assert "# Portfolio Executive Summary" in md_export.text
    assert "## Workspaces" in md_export.text


def test_export_rejects_unknown_format():
    response = client.get("/api/portfolio/export?format=pdf")
    assert response.status_code == 422
