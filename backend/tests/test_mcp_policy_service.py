from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# All policy tests target UNIQUE custom connector slugs (prefixed "v45") so the
# deny rules they create never leak into the shared template-action tests
# (github/context7/filesystem/etc.) that run in the same session.


def _custom_connector(slug: str, risk_level: str = "medium") -> dict:
    connector = client.post(
        "/api/mcp/connectors",
        json={"name": f"Test {slug}", "slug": slug, "risk_level": risk_level},
    ).json()
    client.post(f"/api/mcp/connectors/{connector['connector_id']}/enable")
    return connector


def _create_policy(**payload) -> dict:
    response = client.post("/api/mcp/policies", json=payload)
    assert response.status_code == 200
    return response.json()


def test_create_and_list_policy():
    policy = _create_policy(name="No writes", connector_slug="v45list", action="do_thing")
    assert policy["policy_id"]
    assert policy["effect"] == "deny"  # tighten-only
    listed = client.get("/api/mcp/policies").json()
    assert any(p["policy_id"] == policy["policy_id"] for p in listed["policies"])


def test_effect_is_always_deny():
    policy = _create_policy(name="attempt allow", connector_slug="v45effect")
    assert policy["effect"] == "deny"


def test_evaluate_deny_match_and_nonmatch():
    connector = _custom_connector("v45eval")
    _create_policy(name="deny do_write", connector_slug="v45eval", action="do_write")
    denied = client.post(
        "/api/mcp/policies/evaluate",
        json={"connector_id": connector["connector_id"], "action_name": "do_write"},
    ).json()
    assert denied["allowed"] is False
    assert denied["policy_id"]
    allowed = client.post(
        "/api/mcp/policies/evaluate",
        json={"connector_id": connector["connector_id"], "action_name": "do_read"},
    ).json()
    assert allowed["allowed"] is True


def test_except_actions_carveout():
    connector = _custom_connector("v45fs")
    _create_policy(name="lockdown", connector_slug="v45fs", action="*", except_actions=["safe_read"])
    blocked = client.post(
        "/api/mcp/policies/evaluate",
        json={"connector_id": connector["connector_id"], "action_name": "risky_write"},
    ).json()
    assert blocked["allowed"] is False
    exempt = client.post(
        "/api/mcp/policies/evaluate",
        json={"connector_id": connector["connector_id"], "action_name": "safe_read"},
    ).json()
    assert exempt["allowed"] is True


def test_risk_level_match_scoped_to_slug():
    connector = _custom_connector("v45risk", risk_level="high")
    # Scoped to this slug so it does not leak to other high-risk connectors.
    _create_policy(name="deny high on v45risk", connector_slug="v45risk", action="*", risk_level="high")
    result = client.post(
        "/api/mcp/policies/evaluate",
        json={"connector_id": connector["connector_id"], "action_name": "anything"},
    ).json()
    assert result["allowed"] is False


def test_policy_applied_in_planning():
    connector = _custom_connector("v45plan")
    _create_policy(name="block plan action", connector_slug="v45plan", action="blocked_action")
    plan = client.post(
        f"/api/mcp/connectors/{connector['connector_id']}/plan-action",
        json={"action_name": "blocked_action"},
    ).json()
    assert plan["planned"] is False
    assert "policy" in (plan.get("blocked_reason") or "").lower()


def test_disabled_policy_does_not_deny():
    connector = _custom_connector("v45disable")
    policy = _create_policy(name="temp block", connector_slug="v45disable", action="do_read")
    client.patch(f"/api/mcp/policies/{policy['policy_id']}", json={"enabled": False})
    result = client.post(
        "/api/mcp/policies/evaluate",
        json={"connector_id": connector["connector_id"], "action_name": "do_read"},
    ).json()
    assert result["allowed"] is True


def test_tighten_only_no_matching_policy_unchanged():
    # A connector with no matching policy plans normally.
    connector = _custom_connector("v45clean")
    plan = client.post(
        f"/api/mcp/connectors/{connector['connector_id']}/plan-action",
        json={"action_name": "some_action"},
    ).json()
    assert plan["planned"] is True
    assert plan["allowed"] is True


def test_update_policy_and_404():
    policy = _create_policy(name="editable", connector_slug="v45edit")
    updated = client.patch(f"/api/mcp/policies/{policy['policy_id']}", json={"name": "renamed"}).json()
    assert updated["name"] == "renamed"
    assert client.patch("/api/mcp/policies/missing", json={"name": "x"}).status_code == 404
    assert client.get("/api/mcp/policies/missing").status_code == 404


def test_summary_and_analytics():
    _create_policy(name="for summary", connector_slug="v45summary")
    summary = client.get("/api/mcp/policies/summary").json()
    assert summary["effect"] == "deny_only"
    assert summary["total_policies"] >= 1
    analytics = client.get("/api/analytics").json()
    for key in ("mcp_policies_total", "mcp_policies_active"):
        assert key in analytics


def test_governance_logged_on_create_and_denial():
    connector = _custom_connector("v45gov")
    before = client.get("/api/governance").json()["total_events"]
    _create_policy(name="gov deny", connector_slug="v45gov", action="blocked_action")
    client.post(f"/api/mcp/connectors/{connector['connector_id']}/plan-action", json={"action_name": "blocked_action"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "mcp_policy_created" in actions or "mcp_policy_denied" in actions


def test_existing_template_actions_unaffected_by_v45_policies():
    # Confirms tighten-only isolation: a normal github connector still plans its
    # own actions (no v45 policy targets real template slugs).
    connector = client.post("/api/mcp/connectors", json={"slug": "github"}).json()
    plan = client.post(
        f"/api/mcp/connectors/{connector['connector_id']}/plan-action",
        json={"action_name": "list_issues"},
    ).json()
    assert plan["planned"] is True


def test_existing_endpoints_still_work():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)
    assert client.get("/api/mcp/summary").status_code == 200
    assert client.get("/api/operating-layer/dashboard").status_code == 200
