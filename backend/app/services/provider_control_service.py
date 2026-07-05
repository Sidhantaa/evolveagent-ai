from __future__ import annotations

import os
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Provider → the env key that enables it (readiness is reported as a boolean only —
# the value is NEVER read, logged, or returned). "local" needs no key.
PROVIDERS = [
    {"id": "openai", "name": "OpenAI", "env_keys": ["OPENAI_API_KEY"], "est_latency_ms": 900},
    {"id": "anthropic", "name": "Anthropic (Claude)", "env_keys": ["ANTHROPIC_API_KEY"], "est_latency_ms": 850},
    {"id": "gemini", "name": "Google Gemini", "env_keys": ["GEMINI_API_KEY", "GOOGLE_API_KEY"], "est_latency_ms": 800},
    {"id": "mistral", "name": "Mistral", "env_keys": ["MISTRAL_API_KEY"], "est_latency_ms": 700},
    {"id": "local", "name": "Local / Mock", "env_keys": [], "est_latency_ms": 50},
]

# Capabilities whose real/mock preference the user can set (actual real calls still
# require the provider key + the app's env mode — this is a planning preference).
CAPABILITIES = ["chat", "image", "embedding"]
TASK_TYPES = ["auto", "coding", "research", "business", "image_generation"]

# Illustrative per-1k-token cost estimates (USD) — display only, never billed.
_EST_COST_PER_1K = {"openai": 0.01, "anthropic": 0.012, "gemini": 0.007, "mistral": 0.004, "local": 0.0}


class ProviderControlService:
    """v68.0 Real Provider Control Center 2.0 — cleanly manage providers.

    A read-only readiness dashboard for OpenAI / Claude / Gemini / Mistral / local,
    plus editable *preferences* for model-per-task and real/mock-per-capability, a
    cost estimate + latency stats view, and a described fallback policy. Provider
    **key safety checks report booleans only** — a key's value is never read, logged,
    or returned. Preference changes are governance-logged.
    """

    config_file = "provider_control.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _key_set(key_name: str) -> bool:
        value = os.environ.get(key_name)
        return bool(value and value.strip())

    def _config(self) -> dict:
        records = self.storage.read_list(self.config_file)
        cfg = records[-1]["config"] if records and isinstance(records[-1], dict) and records[-1].get("config") else {}
        return {
            "model_by_task": cfg.get("model_by_task", {}),
            "capability_modes": cfg.get("capability_modes", {c: "mock" for c in CAPABILITIES}),
            "fallback_enabled": cfg.get("fallback_enabled", True),
        }

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="provider_control",
                agent_name="Provider Control",
                action_type=action_type,
                tool_used="ProviderControlService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def key_check(self) -> dict:
        # Booleans only — never a value.
        checks = []
        for provider in PROVIDERS:
            key_status = [{"key_name": k, "is_set": self._key_set(k)} for k in provider["env_keys"]]
            ready = provider["id"] == "local" or any(k["is_set"] for k in key_status)
            checks.append({"provider": provider["id"], "keys": key_status, "ready": ready})
        return {"checks": checks, "note": "Key readiness is reported as booleans only — values are never read or returned."}

    def dashboard(self) -> dict:
        cfg = self._config()
        providers = []
        for provider in PROVIDERS:
            ready = provider["id"] == "local" or any(self._key_set(k) for k in provider["env_keys"])
            providers.append({
                "id": provider["id"],
                "name": provider["name"],
                "ready": ready,
                "required_keys": provider["env_keys"],           # names only
                "est_latency_ms": provider["est_latency_ms"],
                "est_cost_per_1k_usd": _EST_COST_PER_1K.get(provider["id"], 0.0),
            })
        # Cost estimate aggregated from the v50 usage ledger (estimates only).
        ledger = self.storage.read_list("usage_ledger_entries.json")
        est_cost = round(sum(float(e.get("estimated_cost", 0) or 0) for e in ledger), 4)
        self._log("provider_control_viewed", "Rendered the Provider Control Center dashboard.")
        return {
            "providers": providers,
            "ready_count": sum(1 for p in providers if p["ready"]),
            "model_by_task": cfg["model_by_task"],
            "capability_modes": cfg["capability_modes"],
            "fallback_policy": {
                "enabled": cfg["fallback_enabled"],
                "chain": "Try the configured real provider when its key is set and mode is real; otherwise fall back to local/mock.",
            },
            "cost_estimate_usd": est_cost,
            "task_types": TASK_TYPES,
            "capabilities": CAPABILITIES,
            "note": "Read-only readiness + estimates. Real calls still require the provider key and app env mode; no secrets are exposed.",
        }

    def update(self, model_by_task: dict | None, capability_modes: dict | None, fallback_enabled: bool | None) -> dict:
        cfg = self._config()
        rejected = []
        if model_by_task:
            for task, model in model_by_task.items():
                if task in TASK_TYPES and isinstance(model, str) and len(model) <= 80:
                    cfg["model_by_task"][task] = model
                else:
                    rejected.append(f"model_by_task.{task}")
        if capability_modes:
            for cap, mode in capability_modes.items():
                if cap in CAPABILITIES and mode in ("mock", "real"):
                    cfg["capability_modes"][cap] = mode
                else:
                    rejected.append(f"capability_modes.{cap}")
        if fallback_enabled is not None:
            cfg["fallback_enabled"] = bool(fallback_enabled)
        self.storage.write_list(self.config_file, [{"config": cfg, "updated_at": self._now()}])
        self._log("provider_control_updated", f"Updated provider preferences; rejected {len(rejected)}.")
        return {"config": cfg, "rejected": rejected, "note": "Preferences only — no secret values stored; real calls remain env-gated."}

    def analytics_summary(self) -> dict:
        ready = sum(1 for p in PROVIDERS if p["id"] == "local" or any(self._key_set(k) for k in p["env_keys"]))
        return {"provider_control_ready_providers": ready, "provider_control_total_providers": len(PROVIDERS)}

    def summary(self) -> dict:
        cfg = self._config()
        return {
            "total_providers": len(PROVIDERS),
            "ready_providers": sum(1 for p in PROVIDERS if p["id"] == "local" or any(self._key_set(k) for k in p["env_keys"])),
            "capability_modes": cfg["capability_modes"],
            "fallback_enabled": cfg["fallback_enabled"],
            "note": "Provider readiness is boolean-only; preferences are local; no secrets stored.",
        }
