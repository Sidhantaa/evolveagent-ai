from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from app.config import settings
from app.services.providers.anthropic_provider import AnthropicProvider
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.mistral_provider import MistralProvider
from app.services.providers.mock_provider import MockProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.models.response_models import ProviderStatus


@dataclass
class LLMResult:
    output: str
    provider: str
    model: str
    latency_ms: int
    success: bool
    fallback_used: bool = False
    error: str | None = None


@dataclass(frozen=True)
class RouteChoice:
    provider: str
    model: str
    label: str | None = None


class LLMRouter:
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "gemini": GeminiProvider(),
            "mistral": MistralProvider(),
            "mock": MockProvider(),
        }

    def generate(self, agent_name: str, system_prompt: str, user_prompt: str, avoid_provider: str | None = None) -> LLMResult:
        route = self.route_for_agent(agent_name, avoid_provider=avoid_provider)
        return self.generate_with_route(route, system_prompt, user_prompt)

    def generate_for_provider(self, provider: str, model: str, system_prompt: str, user_prompt: str) -> LLMResult:
        return self.generate_with_route(RouteChoice(provider, model), system_prompt, user_prompt)

    def generate_with_route(self, route: RouteChoice, system_prompt: str, user_prompt: str) -> LLMResult:
        attempts = [route, *self.fallback_routes(route.provider)]
        last_error: str | None = None
        fallback_used = False

        for attempt in attempts:
            if settings.use_mock_llm and attempt.provider != "mock":
                last_error = "LLM_MODE is mock"
                fallback_used = True
                continue

            started = perf_counter()
            try:
                output = self.providers[attempt.provider].generate(system_prompt, user_prompt, attempt.model)
                return LLMResult(
                    output=output,
                    provider=attempt.provider,
                    model=attempt.model,
                    latency_ms=int((perf_counter() - started) * 1000),
                    success=True,
                    fallback_used=fallback_used,
                    error=last_error,
                )
            except Exception as exc:
                last_error = str(exc)
                fallback_used = True

        started = perf_counter()
        output = self.providers["mock"].generate(system_prompt, user_prompt, "mock-agent-model")
        return LLMResult(
            output=output,
            provider="mock",
            model="mock-agent-model",
            latency_ms=int((perf_counter() - started) * 1000),
            success=True,
            fallback_used=True,
            error=last_error,
        )

    def route_for_agent(self, agent_name: str, avoid_provider: str | None = None) -> RouteChoice:
        if avoid_provider == "openai" or settings.default_provider == "mock":
            return RouteChoice("mock", "mock-agent-model")
        return RouteChoice("openai", settings.openai_text_model)

    def model_for_provider(self, provider: str) -> str:
        return {
            "openai": settings.openai_text_model,
            "anthropic": settings.anthropic_model,
            "gemini": settings.gemini_model,
            "mistral": settings.mistral_model,
            "mock": "mock-agent-model",
        }.get(provider, "mock-agent-model")

    def provider_label(self, provider: str) -> str:
        return {
            "openai": "OpenAI",
            "anthropic": "Claude",
            "gemini": "Gemini",
            "mistral": "Mistral",
            "mock": "Mock",
        }.get(provider, provider.title())

    def configured_real_routes(self) -> list[RouteChoice]:
        routes: list[RouteChoice] = []
        for provider in ["openai", "anthropic", "gemini", "mistral"]:
            if self.provider_configured(provider):
                routes.append(RouteChoice(provider, self.model_for_provider(provider), self.provider_label(provider)))
        return routes

    def consensus_routes(self) -> list[RouteChoice]:
        if settings.use_mock_llm:
            return [
                RouteChoice("openai", settings.openai_text_model, "OpenAI"),
                RouteChoice("anthropic", settings.anthropic_model, "Claude"),
                RouteChoice("gemini", settings.gemini_model, "Gemini"),
            ]

        routes = self.configured_real_routes()
        if not routes:
            return [RouteChoice("mock", "mock-agent-model", "Mock")]
        if len(routes) == 1:
            routes.append(RouteChoice("mock", "mock-agent-model", "Mock"))
        return routes

    def first_available(self, choices: list[RouteChoice], avoid_provider: str | None = None) -> RouteChoice:
        filtered = [choice for choice in choices if choice.provider != avoid_provider]
        for choice in filtered or choices:
            if self.provider_configured(choice.provider):
                return choice
        return (filtered or choices)[0]

    def provider_configured(self, provider: str) -> bool:
        return {
            "openai": bool(settings.openai_api_key),
            "anthropic": bool(settings.anthropic_api_key),
            "gemini": bool(settings.gemini_api_key),
            "mistral": bool(settings.mistral_api_key),
            "mock": True,
        }.get(provider, False)

    def status(self) -> ProviderStatus:
        details = self.provider_details()
        if settings.use_mock_llm:
            return ProviderStatus(
                llm_mode=settings.llm_mode,
                openai_configured=False,
                anthropic_configured=False,
                gemini_configured=False,
                mistral_configured=False,
                default_provider="mock",
                available_providers=["mock"],
                real_mode_ready=False,
                default_model="mock-agent-model",
                fallback_provider="mock",
                status_message="Mock mode is active. Real providers are not used until LLM_MODE=real.",
                provider_details=details,
            )
        configured = {
            "openai": self.provider_configured("openai"),
            "anthropic": self.provider_configured("anthropic"),
            "gemini": self.provider_configured("gemini"),
            "mistral": self.provider_configured("mistral"),
        }
        available = [provider for provider in ["openai", "anthropic", "gemini", "mistral"] if configured[provider]]
        available.append("mock")
        default_provider = settings.default_provider if settings.default_provider in available else "mock"
        return ProviderStatus(
            llm_mode=settings.llm_mode,
            openai_configured=configured["openai"],
            anthropic_configured=configured["anthropic"],
            gemini_configured=configured["gemini"],
            mistral_configured=configured["mistral"],
            default_provider=default_provider,
            available_providers=available,
            real_mode_ready=any(configured.values()),
            default_model=self.model_for_provider(default_provider),
            fallback_provider="mock",
            status_message=self._status_message(default_provider, configured),
            provider_details=details,
        )

    def provider_details(self) -> list[dict]:
        details = []
        for provider in ["openai", "anthropic", "gemini", "mistral", "mock"]:
            configured = self.provider_configured(provider)
            details.append(
                {
                    "provider": provider,
                    "label": self.provider_label(provider),
                    "configured": configured,
                    "model": self.model_for_provider(provider),
                    "ready": configured and (provider == "mock" or not settings.use_mock_llm),
                    "reason": self._provider_reason(provider, configured),
                    "fallback_provider": "mock" if provider != "mock" else None,
                }
            )
        return details

    def smoke_test(self, provider: str | None = None, live: bool = False) -> dict:
        selected_provider = provider or self.status().default_provider
        if selected_provider not in self.providers:
            return {"success": False, "provider": selected_provider, "live": live, "message": "Unknown provider."}
        configured = self.provider_configured(selected_provider)
        model = self.model_for_provider(selected_provider)
        if not live:
            return {
                "success": configured,
                "provider": selected_provider,
                "model": model,
                "live": False,
                "message": self._provider_reason(selected_provider, configured),
                "fallback_provider": "mock" if selected_provider != "mock" else None,
            }
        if not configured:
            return {
                "success": False,
                "provider": selected_provider,
                "model": model,
                "live": True,
                "message": self._provider_reason(selected_provider, configured),
                "fallback_provider": "mock",
            }
        started = perf_counter()
        try:
            output = self.providers[selected_provider].generate(
                "You are a provider readiness checker. Reply with a short success message.",
                "Return the words provider ready.",
                model,
            )
            return {
                "success": True,
                "provider": selected_provider,
                "model": model,
                "live": True,
                "latency_ms": int((perf_counter() - started) * 1000),
                "message": "Provider live check succeeded.",
                "output_preview": output[:120],
            }
        except Exception as exc:
            return {
                "success": False,
                "provider": selected_provider,
                "model": model,
                "live": True,
                "latency_ms": int((perf_counter() - started) * 1000),
                "message": f"Provider live check failed: {exc}",
                "fallback_provider": "mock",
            }

    def _provider_reason(self, provider: str, configured: bool) -> str:
        if provider == "mock":
            return "Mock fallback is always available."
        if settings.use_mock_llm:
            return "LLM_MODE=mock, so this provider will not be called."
        if configured:
            return "API key is configured and provider can be selected."
        return f"{provider.upper()} API key is not configured; mock fallback will be used."

    def _status_message(self, default_provider: str, configured: dict[str, bool]) -> str:
        if any(configured.values()):
            if default_provider == "mock":
                return "Real mode is enabled, but the configured default provider is unavailable. Mock fallback is active."
            return f"Real mode is ready. Default provider is {self.provider_label(default_provider)}."
        return "Real mode is enabled, but no real provider keys are configured. Mock fallback is active."

    def fallback_routes(self, original_provider: str) -> list[RouteChoice]:
        routes = [
            RouteChoice(settings.default_provider, self.model_for_provider(settings.default_provider)),
            RouteChoice("openai", settings.openai_text_model),
            RouteChoice("anthropic", settings.anthropic_model),
            RouteChoice("gemini", settings.gemini_model),
            RouteChoice("mistral", settings.mistral_model),
            RouteChoice("mock", "mock-agent-model"),
        ]
        seen = {original_provider}
        unique: list[RouteChoice] = []
        for route in routes:
            if route.provider not in seen:
                seen.add(route.provider)
                unique.append(route)
        return unique


llm_router = LLMRouter()
