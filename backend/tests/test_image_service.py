from app.config import settings
from app.agents.image_agent import ImageAgent
from app.models.response_models import ImageResult
from app.services.image_service import ImageService


def test_image_service_uses_mock_mode_by_default():
    result = ImageService().generate("High quality image of a futuristic car")

    assert result.provider == "mock_image"
    assert result.model == "mock-image-generator"
    assert result.fallback_used is False
    assert result.image_url.startswith("/static/generated/")


def test_mock_image_preview_hides_provider_text():
    service = ImageService()
    result = service.generate("High quality image of a futuristic car")
    svg_path = service.mock_provider.static_dir / result.image_url.removeprefix("/static/")
    svg = svg_path.read_text(encoding="utf-8")

    assert "Mock Generated Image" in svg
    assert "Provider: mock_image" not in svg


def test_real_image_mode_without_key_falls_back_to_mock(monkeypatch):
    monkeypatch.setattr(settings, "image_mode", "real")
    monkeypatch.setattr(settings, "image_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", None)

    result = ImageService().generate("High quality image of a futuristic car")

    assert result.provider == "mock_image"
    assert result.model == "mock-image-generator"
    assert result.fallback_used is True
    assert result.fallback_error == "OPENAI_API_KEY is not configured"


def test_real_image_mode_openai_failure_falls_back_to_mock(monkeypatch):
    class FailingOpenAIProvider:
        def generate(self, prompt: str, safety_rewritten: bool = False):
            raise RuntimeError("OpenAI image API unavailable")

    monkeypatch.setattr(settings, "image_mode", "real")
    monkeypatch.setattr(settings, "image_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    service = ImageService()
    service.openai_provider = FailingOpenAIProvider()
    result = service.generate("High quality image of a futuristic car")

    assert result.provider == "mock_image"
    assert result.fallback_used is True
    assert result.fallback_error == "OpenAI image API unavailable"


def test_real_image_mode_openai_success_uses_openai_provider(monkeypatch):
    class SuccessfulOpenAIProvider:
        def generate(self, prompt: str, safety_rewritten: bool = False):
            return ImageResult(
                image_url="/static/generated/test-openai.png",
                prompt=prompt,
                provider="openai",
                model=settings.openai_image_model,
                fallback_used=False,
                safety_rewritten=safety_rewritten,
            )

    monkeypatch.setattr(settings, "image_mode", "real")
    monkeypatch.setattr(settings, "image_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    service = ImageService()
    service.openai_provider = SuccessfulOpenAIProvider()
    result = service.generate("High quality image of a futuristic car")

    assert result.provider == "openai"
    assert result.model == settings.openai_image_model
    assert result.fallback_used is False
    assert result.image_url == "/static/generated/test-openai.png"


def test_image_status_and_dry_smoke_test(monkeypatch):
    monkeypatch.setattr(settings, "image_mode", "real")
    monkeypatch.setattr(settings, "image_provider", "openai")
    monkeypatch.setattr(settings, "openai_api_key", "test-key")

    service = ImageService()
    status = service.status()
    smoke = service.smoke_test(live=False)

    assert status["real_image_ready"] is True
    assert status["active_provider"] == "openai"
    assert smoke["success"] is True
    assert smoke["live"] is False
    assert smoke["provider"] == "openai"


def test_image_agent_cleans_demo_numbering_and_prompt_command():
    prompt, safety_rewritten = ImageAgent().build_safe_prompt(
        "4. Generate an image prompt for a futuristic AI assistant"
    )

    assert safety_rewritten is False
    assert "4." not in prompt
    assert "Generate an image prompt for" not in prompt
    assert "futuristic AI assistant" in prompt
    assert prompt.startswith("A futuristic AI assistant in a sleek holographic interface")


def test_image_agent_keeps_protected_character_rewrite_after_cleaning():
    prompt, safety_rewritten = ImageAgent().build_safe_prompt("Prompt 2: generate image of spiderman")

    assert safety_rewritten is True
    assert "web-slinging superhero inspired character" in prompt
    assert "spiderman" not in prompt.lower()


def test_image_agent_cleans_prompt_punctuation():
    prompt, safety_rewritten = ImageAgent().build_safe_prompt("image of a futuristic AI assistant.")

    assert safety_rewritten is False
    assert ".," not in prompt
    assert ".." not in prompt
    assert ",," not in prompt
    assert "AI assistant" in prompt


def test_image_agent_cleans_give_me_image_command():
    prompt, safety_rewritten = ImageAgent().build_safe_prompt("give me image of sunflower")

    assert safety_rewritten is False
    assert "give me image" not in prompt.lower()
    assert "sunflower" in prompt.lower()
