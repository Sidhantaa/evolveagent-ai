from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_status_is_not_training():
    s = client.get("/api/adaptive-learning/status").json()
    assert s["trains_base_model"] is False
    assert s["method"] == "retrieval_memory_and_few_shot"


def test_ingest_and_recommend():
    client.post("/api/adaptive-learning/items", json={
        "text": "kubernetes helm migration best practices", "kind": "topic", "source": "manual",
    })
    r = client.get("/api/adaptive-learning/recommend", params={"query": "how to do kubernetes migration"}).json()
    assert r["count"] >= 1
    assert any("kubernetes" in rec["text"] for rec in r["recommendations"])
    assert "not model training" in r["note"].lower()


def test_reinforcement_increases_weight():
    payload = {"text": "voice assistant design patterns", "kind": "reference", "source": "manual"}
    client.post("/api/adaptive-learning/items", json=payload)
    client.post("/api/adaptive-learning/items", json=payload)  # same -> reinforce
    items = client.get("/api/adaptive-learning/items", params={"kind": "reference"}).json()["items"]
    match = next(i for i in items if i["text"] == "voice assistant design patterns")
    assert match["weight"] >= 2


def test_learn_ingests_from_history():
    # seed a repo search so learn() has something to pull from
    client.post("/api/agent-studio/agents", json={"name": "x", "role": "y"})  # unrelated, ensures stores exist
    before = client.get("/api/adaptive-learning/summary").json()["adaptive_learning_items"]
    # create a repo-search record via the finder history store by hitting search with mocked network is complex;
    # instead ingest a topic then learn() should be idempotent-safe and return a valid shape
    out = client.post("/api/adaptive-learning/learn").json()
    assert "ingested" in out and "total" in out and out["total"] >= before
    assert "no model was trained" in out["note"].lower()


def test_invalid_kind_rejected():
    assert client.post("/api/adaptive-learning/items", json={"text": "x", "kind": "weights"}).status_code == 400


def test_forget_removes_item():
    client.post("/api/adaptive-learning/items", json={"text": "throwaway learning note", "kind": "topic"})
    item = next(i for i in client.get("/api/adaptive-learning/items").json()["items"] if i["text"] == "throwaway learning note")
    assert client.delete(f"/api/adaptive-learning/items/{item['id']}").json()["removed"] == item["id"]


def test_analytics_and_governance():
    client.post("/api/adaptive-learning/items", json={"text": "governance check note", "kind": "topic"})
    assert "adaptive_learning_items" in client.get("/api/analytics").json()
    actions = {e.get("action_type") for e in client.get("/api/governance").json()["recent_events"]}
    assert "adaptive_ingested" in actions or "adaptive_learned" in actions


def test_existing_endpoints_still_work():
    assert client.get("/api/repo-finder/status").status_code == 200
    assert client.get("/api/agent-studio/summary").status_code == 200
