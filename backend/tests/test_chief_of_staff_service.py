from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_generate_daily_plan():
    plan = client.post("/api/chief-of-staff/daily-plan", json={}).json()
    assert plan["plan_id"]
    assert plan["date"]
    assert isinstance(plan["top_priorities"], list)
    assert isinstance(plan["schedule_blocks"], list)
    assert isinstance(plan["followups_due"], list)
    assert isinstance(plan["recommended_next_actions"], list)
    listed = client.get("/api/chief-of-staff/daily-plans").json()
    assert any(item["plan_id"] == plan["plan_id"] for item in listed["daily_plans"])


def test_generate_weekly_plan():
    plan = client.post("/api/chief-of-staff/weekly-plan", json={}).json()
    assert plan["plan_id"]
    assert plan["week_start"]
    assert isinstance(plan["milestones"], list)
    assert isinstance(plan["priority_themes"], list)
    assert isinstance(plan["blocked_items"], list)
    assert isinstance(plan["recommended_focus"], list)
    listed = client.get("/api/chief-of-staff/weekly-plans").json()
    assert any(item["plan_id"] == plan["plan_id"] for item in listed["weekly_plans"])


def test_priority_ranking_from_mixed_local_data():
    # Seed signals across multiple sources.
    client.post("/api/business/leads", json={"name": "Hot Lead", "status": "qualified"})
    client.post("/api/business/support-cases", json={"subject": "Down hard", "priority": "high"})
    body = client.get("/api/chief-of-staff/priorities").json()
    assert isinstance(body["priority_items"], list)
    assert body["count"] >= 1
    item = body["priority_items"][0]
    for key in ("item_id", "item_type", "title", "priority_score", "reason", "recommended_action", "source_id"):
        assert key in item
    # Scores should be sorted descending.
    scores = [i["priority_score"] for i in body["priority_items"]]
    assert scores == sorted(scores, reverse=True)
    # A high-priority open support case should rank with a strong score somewhere.
    assert any(i["item_type"] == "support_case" and i["priority_score"] >= 50 for i in body["priority_items"])


def test_create_list_update_followup():
    created = client.post(
        "/api/chief-of-staff/followups",
        json={"title": "Call client", "priority": "high", "due_date": "2026-07-01"},
    ).json()
    assert created["followup_id"]
    assert created["status"] == "open"
    assert created["priority"] == "high"

    listed = client.get("/api/chief-of-staff/followups").json()
    assert any(item["followup_id"] == created["followup_id"] for item in listed["followups"])

    updated = client.patch(f"/api/chief-of-staff/followups/{created['followup_id']}", json={"status": "done"}).json()
    assert updated["status"] == "done"


def test_followup_not_found():
    assert client.patch("/api/chief-of-staff/followups/missing", json={"status": "done"}).status_code == 404


def test_overdue_followup_detection():
    client.post(
        "/api/chief-of-staff/followups",
        json={"title": "Overdue item", "due_date": "2000-01-01", "status": "open"},
    )
    body = client.get("/api/chief-of-staff/followups").json()
    assert body["overdue_count"] >= 1
    dashboard = client.get("/api/chief-of-staff/dashboard").json()
    assert any(f["title"] == "Overdue item" for f in dashboard["overdue_followups"])


def test_dashboard_response_shape():
    body = client.get("/api/chief-of-staff/dashboard").json()
    for key in (
        "today",
        "daily_plan",
        "weekly_plan",
        "priority_items",
        "open_followups",
        "overdue_followups",
        "blocked_items",
        "risk_summary",
        "recommended_next_action",
    ):
        assert key in body
    assert isinstance(body["priority_items"], list)
    assert "open_risk_count" in body["risk_summary"]


def test_governance_events_written_for_chief_actions():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/chief-of-staff/daily-plan", json={})
    client.post("/api/chief-of-staff/followups", json={"title": "Gov follow-up"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "chief_daily_plan_created" in actions or "chief_followup_created" in actions


# ----------------------------------------------------------------------
# Regression
# ----------------------------------------------------------------------
def test_existing_run_endpoint_still_works():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)


def test_existing_business_marketplace_department_endpoints_still_work():
    assert client.get("/api/business/dashboard").status_code == 200
    assert client.get("/api/business/leads").status_code == 200
    assert client.get("/api/agent-marketplace/packs").status_code == 200
    assert client.get("/api/departments").status_code == 200
    assert client.get("/api/analytics").status_code == 200


# ------------------------------------------------------------------
# v180 — real external signal: open GitHub PRs/issues from configured repos
# fold into priority ranking, via the already-real, read-only
# GitHubConnectorService. Off by default (no repos configured); a missing
# precondition or connector failure just means zero GitHub items, never an
# error surfaced to the caller.
# ------------------------------------------------------------------
def test_status_reports_github_wiring():
    s = client.get("/api/chief-of-staff/status").json()
    assert s["available"] is True
    assert s["github_wired"] is True  # wired in routes.py regardless of repo config
    assert isinstance(s["github_repos_configured"], list)


def test_no_repos_configured_yields_no_github_priority_items(monkeypatch):
    monkeypatch.delenv("CHIEF_OF_STAFF_GITHUB_REPOS", raising=False)
    body = client.get("/api/chief-of-staff/priorities").json()
    assert not any(item["item_type"] in ("github_pr", "github_issue") for item in body["priority_items"])


def test_real_github_prs_and_issues_fold_into_priorities(monkeypatch):
    from app.services.github_connector_service import GitHubConnectorService

    monkeypatch.setenv("CHIEF_OF_STAFF_GITHUB_REPOS", "acme/widgets")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_get(self, path, params=None):
        if path.endswith("/pulls"):
            return [{
                "id": 1, "number": 42, "title": "Stale PR", "state": "open", "draft": False,
                "user": {"login": "octocat"}, "head": {"ref": "feature/x"}, "base": {"ref": "main"},
                "html_url": "https://github.com/acme/widgets/pull/42",
                "created_at": "2020-01-01T00:00:00Z", "updated_at": "2020-01-02T00:00:00Z",
            }]
        if path.endswith("/issues"):
            return [{
                "id": 2, "number": 7, "title": "Old bug", "state": "open",
                "user": {"login": "octocat"}, "labels": [],
                "html_url": "https://github.com/acme/widgets/issues/7",
                "created_at": "2020-01-01T00:00:00Z", "updated_at": "2020-01-02T00:00:00Z",
            }]
        return []

    monkeypatch.setattr(GitHubConnectorService, "_http_get", fake_get)
    body = client.get("/api/chief-of-staff/priorities").json()
    types = {item["item_type"] for item in body["priority_items"]}
    assert "github_pr" in types and "github_issue" in types
    pr_item = next(item for item in body["priority_items"] if item["item_type"] == "github_pr")
    assert "acme/widgets#42" in pr_item["title"]
    assert "needs review" in pr_item["reason"].lower()  # old PR (2020) -> stale signal


def test_github_connector_failure_degrades_to_no_github_items(monkeypatch):
    from app.services.github_connector_service import GitHubConnectorService

    monkeypatch.setenv("CHIEF_OF_STAFF_GITHUB_REPOS", "acme/widgets")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def boom(self, path, params=None):
        raise TimeoutError("network unavailable")

    monkeypatch.setattr(GitHubConnectorService, "_http_get", boom)
    resp = client.get("/api/chief-of-staff/priorities")
    assert resp.status_code == 200  # never a crash
    body = resp.json()
    assert not any(item["item_type"] in ("github_pr", "github_issue") for item in body["priority_items"])


def test_github_items_appear_in_dashboard_count(monkeypatch):
    from app.services.github_connector_service import GitHubConnectorService

    monkeypatch.setenv("CHIEF_OF_STAFF_GITHUB_REPOS", "acme/widgets")
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")

    def fake_get(self, path, params=None):
        if path.endswith("/pulls"):
            return [{"id": 1, "number": 1, "title": "PR", "state": "open", "draft": False,
                      "user": {"login": "o"}, "head": {"ref": "x"}, "base": {"ref": "main"},
                      "html_url": "u", "created_at": "2026-01-01T00:00:00Z", "updated_at": "2026-01-01T00:00:00Z"}]
        return []

    monkeypatch.setattr(GitHubConnectorService, "_http_get", fake_get)
    dashboard = client.get("/api/chief-of-staff/dashboard").json()
    assert dashboard["github_items_count"] >= 1


def test_summary_and_analytics_include_chief_of_staff():
    assert "chief_of_staff_daily_plans" in client.get("/api/analytics").json()
