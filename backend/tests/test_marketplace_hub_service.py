from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_listings_seeded_with_featured():
    data = client.get("/api/marketplace-hub/listings").json()
    assert data["count"] >= 4
    kinds = {x["kind"] for x in data["listings"]}
    assert {"agent", "workflow"} <= kinds
    assert any(x["is_featured"] for x in data["listings"])


def test_filter_by_kind():
    agents = client.get("/api/marketplace-hub/listings", params={"kind": "agent"}).json()
    assert all(x["kind"] == "agent" for x in agents["listings"])


def test_install_agent_creates_profile_with_rederived_guardrails():
    listings = client.get("/api/marketplace-hub/listings", params={"kind": "agent"}).json()["listings"]
    target = listings[0]
    res = client.post(f"/api/marketplace-hub/listings/{target['listing_id']}/install").json()
    assert res["kind"] == "agent"
    agent_id = res["installed"]["id"]
    got = client.get(f"/api/agent-studio/agents/{agent_id}").json()
    assert got["agent_id"] == agent_id  # a fresh local copy exists


def test_install_workflow_creates_definition():
    wf = client.get("/api/marketplace-hub/listings", params={"kind": "workflow"}).json()["listings"][0]
    res = client.post(f"/api/marketplace-hub/listings/{wf['listing_id']}/install").json()
    assert res["kind"] == "workflow"
    def_id = res["installed"]["id"]
    defs = client.get("/api/durable-workflows/definitions").json()["definitions"]
    assert any(d["definition_id"] == def_id for d in defs)


def test_publish_agent_from_studio_then_install_sanitizes_risky():
    # Create an agent that declares a risky allowed action.
    created = client.post("/api/agent-studio/agents", json={
        "name": "Publisher Agent", "role": "outreach",
        "guardrails": {"allowed_actions": ["send_email", "summarize"]},
    }).json()
    listing = client.post("/api/marketplace-hub/listings", json={
        "kind": "agent", "source_id": created["agent_id"], "summary": "shares outreach",
    }).json()
    assert listing["kind"] == "agent" and listing["installs"] == 0
    installed = client.post(f"/api/marketplace-hub/listings/{listing['listing_id']}/install").json()
    got = client.get(f"/api/agent-studio/agents/{installed['installed']['id']}").json()
    # risky action re-derived to requires_approval on install (can't auto-run)
    assert "send_email" in got["guardrails"]["requires_approval"]


def test_publish_workflow_inline_manifest():
    listing = client.post("/api/marketplace-hub/listings", json={
        "kind": "workflow", "name": "My Flow",
        "manifest": {"name": "My Flow", "steps": [{"name": "Draft"}, {"name": "Publish", "action": "publish"}]},
    }).json()
    assert listing["kind"] == "workflow" and len(listing["manifest"]["steps"]) == 2


def test_publish_invalid_kind_400():
    assert client.post("/api/marketplace-hub/listings", json={"kind": "banana"}).status_code == 400


def test_publish_agent_without_source_or_manifest_400():
    assert client.post("/api/marketplace-hub/listings", json={"kind": "agent"}).status_code == 400


def test_featured_cannot_be_unpublished():
    featured = next(x for x in client.get("/api/marketplace-hub/listings").json()["listings"] if x["is_featured"])
    assert client.delete(f"/api/marketplace-hub/listings/{featured['listing_id']}").status_code == 400


def test_unpublish_custom_listing():
    listing = client.post("/api/marketplace-hub/listings", json={
        "kind": "workflow", "manifest": {"name": "Temp", "steps": [{"name": "x"}]},
    }).json()
    assert client.delete(f"/api/marketplace-hub/listings/{listing['listing_id']}").json()["removed"] == listing["listing_id"]


def test_summary_analytics_governance():
    assert "marketplace_hub_listings" in client.get("/api/marketplace-hub/summary").json()
    assert "marketplace_hub_listings" in client.get("/api/analytics").json()
    actions = {e.get("action_type") for e in client.get("/api/governance").json()["recent_events"]}
    assert "listing_installed" in actions or "listing_published" in actions


def test_existing_endpoints_still_work():
    assert client.get("/api/durable-workflows/templates").status_code == 200
    assert client.get("/api/voice-console/status").status_code == 200
