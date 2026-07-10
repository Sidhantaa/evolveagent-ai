from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_item(**overrides) -> dict:
    payload = {
        "title": overrides.get("title", "Login screen"),
        "item_type": overrides.get("item_type", "screenshot"),
        "description": overrides.get("description", "A screenshot with a button, a form, and an input field."),
    }
    response = client.post("/api/multimodal/items", json=payload)
    assert response.status_code == 200
    return response.json()


def test_create_and_list_item():
    created = _create_item(title="Create-Test Item")
    assert created["item_id"]
    assert created["item_type"] == "screenshot"
    listed = client.get("/api/multimodal/items").json()
    assert any(item["item_id"] == created["item_id"] for item in listed["items"])


def _assert_analysis_shape(analysis: dict):
    for key in ("analysis_id", "item_id", "analysis_type", "summary", "detected_elements", "issues", "recommended_actions", "confidence", "mock_mode"):
        assert key in analysis
    assert analysis["mock_mode"] is True
    assert 0 <= analysis["confidence"] <= 100


def test_analyze_screenshot():
    item = _create_item(description="Screenshot shows a header, a sidebar, a table and a chart.")
    analysis = client.post(f"/api/multimodal/items/{item['item_id']}/analyze", json={"analysis_type": "screenshot"}).json()
    _assert_analysis_shape(analysis)
    assert analysis["analysis_type"] == "screenshot"
    assert analysis["detected_elements"]


def test_analyze_ui_bug():
    item = _create_item(item_type="ui_bug", description="The button overlaps the footer and text is cut off with low contrast.")
    analysis = client.post(f"/api/multimodal/items/{item['item_id']}/analyze", json={"analysis_type": "ui_bug"}).json()
    _assert_analysis_shape(analysis)
    assert analysis["analysis_type"] == "ui_bug"
    assert analysis["issues"]


def test_analyze_diagram_and_whiteboard():
    diagram = _create_item(item_type="diagram", description="Boxes connected by arrows to a database and a service.")
    diagram_analysis = client.post(f"/api/multimodal/items/{diagram['item_id']}/analyze", json={"analysis_type": "diagram"}).json()
    _assert_analysis_shape(diagram_analysis)
    assert diagram_analysis["recommended_actions"]

    whiteboard = _create_item(item_type="whiteboard", description="Hand-drawn nodes and decision points.")
    wb_analysis = client.post(f"/api/multimodal/items/{whiteboard['item_id']}/analyze", json={"analysis_type": "whiteboard"}).json()
    _assert_analysis_shape(wb_analysis)
    assert wb_analysis["analysis_type"] == "whiteboard"


def test_analyze_uses_item_type_when_unspecified():
    item = _create_item(item_type="diagram", description="Nodes and arrows.")
    analysis = client.post(f"/api/multimodal/items/{item['item_id']}/analyze", json={}).json()
    assert analysis["analysis_type"] == "diagram"


def test_analyze_item_not_found():
    assert client.post("/api/multimodal/items/missing/analyze", json={}).status_code == 404


def test_dashboard_response_shape():
    item = _create_item(title="Dashboard-Test Item")
    client.post(f"/api/multimodal/items/{item['item_id']}/analyze", json={})
    body = client.get("/api/multimodal/dashboard").json()
    for key in ("total_items", "total_analyses", "analysis_type_counts", "total_issues_found", "recent_analyses", "mock_mode"):
        assert key in body
    assert body["mock_mode"] is True


def test_governance_event_logged():
    before = client.get("/api/governance").json()["total_events"]
    item = _create_item(title="Gov-Test Item")
    client.post(f"/api/multimodal/items/{item['item_id']}/analyze", json={})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    actions = {event.get("action_type") for event in after["recent_events"]}
    assert "multimodal_item_analyzed" in actions or "multimodal_item_created" in actions


def test_existing_run_endpoint_still_works():
    response = client.post("/api/run", json={"user_input": "Explain how EvolveAgent AI works."})
    assert response.status_code == 200
    assert isinstance(response.json().get("final_output"), str)


# ------------------------------------------------------------------
# v170 — real vision analysis (opt-in, per-call image, never persisted).
# Mock/heuristic default behavior above is completely unaffected.
# ------------------------------------------------------------------
PNG = (
    "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lE"
    "QVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
)


def test_status_is_mock_safe_and_secret_safe():
    s = client.get("/api/multimodal/status").json()
    assert s["available"] is True
    assert s["live_default"] is False
    assert isinstance(s["key_configured"], bool)


def test_allow_live_without_image_falls_back_to_heuristic():
    item = _create_item(title="No image")
    analysis = client.post(f"/api/multimodal/items/{item['item_id']}/analyze", json={"allow_live": True}).json()
    assert analysis["mode"] == "mock"
    assert analysis["mock_mode"] is True
    assert "image" in analysis["note"].lower()


def test_allow_live_with_image_but_no_key_falls_back_to_heuristic():
    # In CI there is no OPENROUTER_API_KEY, so a live request must degrade safely.
    item = _create_item(title="Image no key")
    analysis = client.post(
        f"/api/multimodal/items/{item['item_id']}/analyze", json={"image": PNG, "allow_live": True},
    ).json()
    assert analysis["mode"] == "mock"
    assert "key" in analysis["note"].lower()


def test_invalid_image_rejected_with_400():
    item = _create_item(title="Bad image")
    resp = client.post(f"/api/multimodal/items/{item['item_id']}/analyze", json={"image": "not-a-data-url"})
    assert resp.status_code == 400


def test_unsupported_image_type_rejected():
    item = _create_item(title="Unsupported type")
    bad = "data:image/tiff;base64,AAAA"
    resp = client.post(f"/api/multimodal/items/{item['item_id']}/analyze", json={"image": bad})
    assert resp.status_code == 400


def test_image_without_allow_live_still_uses_heuristic():
    """Passing an image without allow_live=True must NOT trigger a live call —
    opt-in requires the explicit flag, not just the presence of an image."""
    item = _create_item(title="Image but no opt-in")
    analysis = client.post(f"/api/multimodal/items/{item['item_id']}/analyze", json={"image": PNG}).json()
    assert analysis["mode"] == "mock"


def test_real_vision_analysis_when_fully_opted_in(monkeypatch):
    import openai
    from app.services.multimodal_agent_service import MultimodalAgentService

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    class FakeMessage:
        content = "Detected a login form with a submit button. No visible defects."

    class FakeChoice:
        message = FakeMessage()

    class FakeCompletions:
        @staticmethod
        def create(**kwargs):
            assert kwargs["messages"][1]["content"][1]["image_url"]["url"] == PNG
            return type("R", (), {"choices": [FakeChoice()]})()

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass
        chat = FakeChat()

    monkeypatch.setattr(openai, "OpenAI", FakeClient)

    item = _create_item(title="Real vision item", item_type="ui_bug")
    analysis = client.post(
        f"/api/multimodal/items/{item['item_id']}/analyze",
        json={"image": PNG, "allow_live": True, "analysis_type": "ui_bug"},
    ).json()
    assert analysis["mode"] == "live"
    assert analysis["mock_mode"] is False
    assert "login form" in analysis["summary"].lower()


def test_live_call_failure_degrades_to_heuristic(monkeypatch):
    import openai

    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    class BoomClient:
        def __init__(self, *args, **kwargs):
            pass

        class chat:
            class completions:
                @staticmethod
                def create(**kwargs):
                    raise TimeoutError("network unavailable")

    monkeypatch.setattr(openai, "OpenAI", BoomClient)

    item = _create_item(title="Live fails")
    analysis = client.post(
        f"/api/multimodal/items/{item['item_id']}/analyze", json={"image": PNG, "allow_live": True},
    ).json()
    assert analysis["mode"] == "mock"
    assert "failed" in analysis["note"].lower()


def test_image_bytes_never_persisted_in_analyses_history():
    item = _create_item(title="Privacy check")
    client.post(f"/api/multimodal/items/{item['item_id']}/analyze", json={"image": PNG})
    analyses = client.get("/api/multimodal/analyses").json()["analyses"]
    assert all("image" not in a for a in analyses)


def test_summary_and_analytics():
    assert "multimodal_agent_analyses" in client.get("/api/multimodal/summary").json()
    assert "multimodal_agent_analyses" in client.get("/api/analytics").json()
