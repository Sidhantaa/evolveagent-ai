from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_default_evaluation_planning_first():
    # No matching profile: high risk → require_approval, low risk → allow.
    high = client.post("/api/permissions/evaluate", json={"action": "delete_repo", "risk_level": "high"}).json()
    assert high["decision"] == "require_approval"
    low = client.post("/api/permissions/evaluate", json={"action": "read_file", "risk_level": "low"}).json()
    assert low["decision"] == "allow"


def test_deny_profile_blocks():
    prof = client.post("/api/permissions/profiles", json={
        "name": "v81 deny sends", "scope_type": "tool", "scope_value": "slack",
        "action_pattern": "send*", "effect": "deny", "risk_level": "low",
    }).json()
    result = client.post("/api/permissions/evaluate", json={
        "scope_type": "tool", "scope_value": "slack", "action": "send_message", "risk_level": "high",
    }).json()
    assert result["decision"] == "deny"
    assert result["matched_profile"]["profile_id"] == prof["profile_id"]
    assert "denies" in result["explanation"]
    client.delete(f"/api/permissions/profiles/{prof['profile_id']}")


def test_most_restrictive_wins():
    a = client.post("/api/permissions/profiles", json={"name": "allowX", "action_pattern": "x*", "effect": "allow", "risk_level": "low"}).json()
    d = client.post("/api/permissions/profiles", json={"name": "denyX", "action_pattern": "x*", "effect": "deny", "risk_level": "low"}).json()
    result = client.post("/api/permissions/evaluate", json={"action": "xtest", "risk_level": "medium"}).json()
    assert result["decision"] == "deny"  # deny beats allow
    client.delete(f"/api/permissions/profiles/{a['profile_id']}")
    client.delete(f"/api/permissions/profiles/{d['profile_id']}")


def test_preview_does_not_log():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/permissions/preview", json={"action": "anything", "risk_level": "high"})
    after = client.get("/api/governance").json()["total_events"]
    assert after == before  # preview is side-effect free


def test_delete_unknown_404():
    assert client.delete("/api/permissions/profiles/nope").status_code == 404


def test_summary_and_analytics():
    summary = client.get("/api/permissions/summary").json()
    for key in ("total_profiles", "by_effect", "approval_chains"):
        assert key in summary
    assert "permission_profiles" in client.get("/api/analytics").json()


def test_evaluate_is_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/permissions/evaluate", json={"action": "test", "risk_level": "high"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "permission_evaluated" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/collaboration/summary").status_code == 200
    assert client.get("/api/meeting-intel/summary").status_code == 200
    # core PermissionService path untouched
    assert client.post("/api/run", json={"user_input": "Explain EvolveAgent."}).status_code == 200
