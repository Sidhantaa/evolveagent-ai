from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from time import perf_counter

from app.config import settings
from app.services.providers.anthropic_provider import AnthropicProvider
from app.services.providers.gemini_provider import GeminiProvider
from app.services.providers.mistral_provider import MistralProvider
from app.services.providers.mock_provider import MockProvider
from app.services.providers.openai_provider import OpenAIProvider
from app.models.response_models import ProviderStatus

# Quality-tier model fields per provider. Every field here was already declared in
# Settings (openai_master_model, anthropic_strong_model, etc.) but had ZERO real
# callers before this router used them — "balanced" is deliberately the same field
# each provider already used by default, so quality="balanced" (the default) is a
# byte-for-byte behavioral no-op versus the pre-tier router.
QUALITY_TIERS = ("fast", "balanced", "quality")
_QUALITY_TIER_FIELDS = {
    "openai": {"fast": "openai_cheap_model", "balanced": "openai_text_model", "quality": "openai_master_model"},
    "anthropic": {"fast": "anthropic_fast_model", "balanced": "anthropic_model", "quality": "anthropic_strong_model"},
    "gemini": {"fast": "gemini_fast_model", "balanced": "gemini_model", "quality": "gemini_pro_model"},
    "mistral": {"fast": "mistral_fast_model", "balanced": "mistral_model", "quality": "mistral_strong_model"},
}
# Recognized model-name prefixes, used to resolve a free-text task preference
# (e.g. "claude-opus-4-8", stored by ProviderControlService) back to a provider.
_MODEL_PREFIX_PROVIDER = (
    ("claude", "anthropic"),
    ("gpt", "openai"),
    ("chatgpt", "openai"),
    ("o1", "openai"),
    ("o3", "openai"),
    ("o4", "openai"),
    ("gemini", "gemini"),
    ("mistral", "mistral"),
    ("mixtral", "mistral"),
    ("codestral", "mistral"),
    ("devstral", "mistral"),
)


def _provider_for_model(model: str) -> str | None:
    lowered = (model or "").strip().lower()
    for prefix, provider in _MODEL_PREFIX_PROVIDER:
        if lowered.startswith(prefix):
            return provider
    return None


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
    # Recent call outcomes for real observability (provider health, fallback rate).
    # Optional collaborators, set post-construction (routes.py wires them once
    # StorageService/ProviderControlService exist) -- unset means "not tracked",
    # never a crash. Mirrors the optional-collaborator pattern used across the app.
    _calls_file = "llm_router_calls.json"
    _MAX_CALL_RECORDS = 500

    def __init__(self, usage_ledger=None):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "gemini": GeminiProvider(),
            "mistral": MistralProvider(),
            "mock": MockProvider(),
        }
        self.storage = None
        self.provider_control = None
        self.usage_ledger = usage_ledger

    def generate(
        self,
        agent_name: str,
        system_prompt: str,
        user_prompt: str,
        avoid_provider: str | None = None,
        task_type: str | None = None,
        quality: str = "balanced",
        workspace_id: str | None = None,
    ) -> LLMResult:
        route = self.route_for_agent(agent_name, avoid_provider=avoid_provider, task_type=task_type, quality=quality)
        return self.generate_with_route(route, system_prompt, user_prompt, task_type=task_type, workspace_id=workspace_id)

    def generate_for_provider(
        self, provider: str, model: str, system_prompt: str, user_prompt: str, workspace_id: str | None = None,
    ) -> LLMResult:
        return self.generate_with_route(RouteChoice(provider, model), system_prompt, user_prompt, workspace_id=workspace_id)

    def generate_with_route(
        self,
        route: RouteChoice,
        system_prompt: str,
        user_prompt: str,
        task_type: str | None = None,
        workspace_id: str | None = None,
    ) -> LLMResult:
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
                latency_ms = int((perf_counter() - started) * 1000)
                self._record_call(attempt.provider, attempt.model, True, latency_ms, task_type)
                result = LLMResult(
                    output=output,
                    provider=attempt.provider,
                    model=attempt.model,
                    latency_ms=latency_ms,
                    success=True,
                    fallback_used=fallback_used,
                    error=last_error,
                )
                self._record_usage(result, workspace_id)
                return result
            except Exception as exc:
                latency_ms = int((perf_counter() - started) * 1000)
                self._record_call(attempt.provider, attempt.model, False, latency_ms, task_type)
                last_error = str(exc)
                fallback_used = True

        started = perf_counter()
        output = self.providers["mock"].generate(system_prompt, user_prompt, "mock-agent-model")
        latency_ms = int((perf_counter() - started) * 1000)
        self._record_call("mock", "mock-agent-model", True, latency_ms, task_type)
        result = LLMResult(
            output=output,
            provider="mock",
            model="mock-agent-model",
            latency_ms=latency_ms,
            success=True,
            fallback_used=True,
            error=last_error,
        )
        self._record_usage(result, workspace_id)
        return result

    def _record_usage(self, result: LLMResult, workspace_id: str | None) -> None:
        """Best-effort cost visibility belongs beside provider execution.

        The usage ledger is a planning estimate only; recording it must never
        change model routing, fallback behavior, or the final model response.
        """
        if self.usage_ledger is None:
            return
        try:
            self.usage_ledger.record_usage(
                {
                    "workspace_id": workspace_id,
                    "capability": "text",
                    "units": 1,
                    "mode": "mock" if result.provider == "mock" else "real",
                }
            )
        except Exception:
            pass

    def route_for_agent(
        self,
        agent_name: str,
        avoid_provider: str | None = None,
        task_type: str | None = None,
        quality: str = "balanced",
    ) -> RouteChoice:
        # Task-based preference (ProviderControlService.model_by_task) wins outright
        # when it resolves to a real, available provider -- it is a more specific
        # signal than the default agent-name-agnostic route below.
        if task_type and task_type != "auto" and self.provider_control is not None:
            preferred_model = self.provider_control.preferred_model_for_task(task_type)
            if preferred_model:
                preferred_provider = _provider_for_model(preferred_model)
                if (
                    preferred_provider
                    and preferred_provider != avoid_provider
                    and self.provider_configured(preferred_provider)
                ):
                    return RouteChoice(preferred_provider, preferred_model, label=f"task:{task_type}")
        if avoid_provider == "openai" or settings.default_provider == "mock":
            return RouteChoice("mock", "mock-agent-model")
        return RouteChoice("openai", self.model_for_provider("openai", quality))

    def model_for_provider(self, provider: str, quality: str = "balanced") -> str:
        if provider == "mock":
            return "mock-agent-model"
        tiers = _QUALITY_TIER_FIELDS.get(provider)
        if not tiers:
            return "mock-agent-model"
        field = tiers.get(quality) or tiers["balanced"]
        return getattr(settings, field, None) or getattr(settings, tiers["balanced"])

    def _record_call(self, provider: str, model: str, success: bool, latency_ms: int, task_type: str | None) -> None:
        if self.storage is None:
            return
        try:
            rows = self.storage.read_list(self._calls_file)
            rows.append({
                "provider": provider,
                "model": model,
                "success": bool(success),
                "latency_ms": int(latency_ms),
                "task_type": task_type,
                "created_at": datetime.now(UTC).isoformat(),
            })
            if len(rows) > self._MAX_CALL_RECORDS:
                rows = rows[-self._MAX_CALL_RECORDS:]
            self.storage.write_list(self._calls_file, rows)
        except Exception:
            pass  # observability must never break a real call

    def provider_health(self, window: int = 200) -> dict:
        if self.storage is None:
            return {"available": False, "providers": [], "note": "No storage wired; health tracking inactive."}
        try:
            rows = self.storage.read_list(self._calls_file)[-window:]
        except Exception:
            rows = []
        if not rows:
            return {"available": True, "providers": [], "window": window, "total_calls": 0, "note": "No calls recorded yet."}
        by_provider: dict[str, list[dict]] = {}
        for row in rows:
            by_provider.setdefault(row.get("provider", "unknown"), []).append(row)
        providers = []
        for provider, calls in by_provider.items():
            total = len(calls)
            successes = sum(1 for c in calls if c.get("success"))
            avg_latency = round(sum(c.get("latency_ms", 0) for c in calls) / total) if total else 0
            providers.append({
                "provider": provider,
                "calls": total,
                "success_rate": round(successes / total * 100) if total else 0,
                "avg_latency_ms": avg_latency,
            })
        providers.sort(key=lambda p: -p["calls"])
        return {"available": True, "providers": providers, "window": window, "total_calls": len(rows)}

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

    def smoke_test(self, provider: str | None = None, live: bool = False, task_type: str | None = None) -> dict:
        route_label: str | None = None
        if task_type and task_type != "auto":
            route = self.route_for_agent("smoke-test", task_type=task_type)
            selected_provider, model, route_label = route.provider, route.model, route.label
        else:
            selected_provider = provider or self.status().default_provider
            model = self.model_for_provider(selected_provider) if selected_provider in self.providers else None
        if selected_provider not in self.providers:
            return {"success": False, "provider": selected_provider, "live": live, "message": "Unknown provider."}
        configured = self.provider_configured(selected_provider)
        if not live:
            return {
                "success": configured,
                "provider": selected_provider,
                "model": model,
                "live": False,
                "task_type": task_type,
                "route_label": route_label,
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
