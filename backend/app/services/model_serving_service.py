from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from app.config import settings
from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService

# v260 readiness slice: this service NEVER starts, installs, or supervises a
# model-server process. Each backend below is only ever reached with a
# short-timeout GET against an operator-configured, already-running URL --
# see docs/CODEX_ASSIGNMENT_v260_model_serving_readiness.md.
_DETECT_TIMEOUT_SECONDS = 2.5

BACKEND_SPECS = [
    {
        "backend": "ollama",
        "name": "Ollama",
        "base_url_setting": "ollama_base_url",
        "list_path": "/api/tags",
        "models_key": "models",
        "model_name_key": "name",
    },
    {
        "backend": "vllm",
        "name": "vLLM (OpenAI-compatible)",
        "base_url_setting": "vllm_base_url",
        "list_path": "/v1/models",
        "models_key": "data",
        "model_name_key": "id",
    },
    {
        "backend": "openai_compatible_endpoint",
        "name": "Generic OpenAI-Compatible Endpoint",
        "base_url_setting": "local_openai_compatible_base_url",
        "list_path": "/v1/models",
        "models_key": "data",
        "model_name_key": "id",
    },
]

BACKEND_ORDER = [spec["backend"] for spec in BACKEND_SPECS]


class ModelServingService:
    """v260 distributed model serving -- readiness slice only.

    Read-only: detects whether an operator-configured local/loopback model
    server is already running and, if so, what it reports having loaded. It
    never starts a server, downloads weights, or forwards a real inference
    request. dry_run() answers "would routing a request here be accepted"
    without ever sending one.
    """

    def __init__(self, governance_service: GovernanceService, http_client: Any | None = None):
        self.governance = governance_service
        self.http_client = http_client

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str, blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="compute_fabric",
                agent_name="Model Serving Readiness",
                action_type=action_type,
                tool_used="ModelServingService",
                permission_level="read_only",
                approved=not blocked,
                blocked=blocked,
                risk_score=5,
                reason=reason,
            )
        )

    @staticmethod
    def _spec(backend: str) -> dict | None:
        return next((spec for spec in BACKEND_SPECS if spec["backend"] == backend), None)

    def _base_url(self, spec: dict) -> str:
        return str(getattr(settings, spec["base_url_setting"]) or "").strip()

    def _get_json(self, url: str) -> dict | list | None:
        try:
            if self.http_client is not None:
                response = self.http_client.get(url, timeout=_DETECT_TIMEOUT_SECONDS)
            else:
                response = httpx.get(url, timeout=_DETECT_TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def detect(self, backend: str) -> dict:
        backend = str(backend or "").strip()[:60]
        spec = self._spec(backend)
        if spec is None:
            return {
                "backend": backend,
                "name": backend or "unknown",
                "configured": False,
                "reachable": False,
                "models": [],
                "checked_at": self._now(),
                "note": "Unknown model-serving backend.",
            }
        base_url = self._base_url(spec)
        if not base_url:
            return {
                "backend": spec["backend"],
                "name": spec["name"],
                "configured": False,
                "reachable": False,
                "models": [],
                "checked_at": self._now(),
                "note": f"Set {spec['base_url_setting'].upper()} to an already-running local endpoint to enable detection.",
            }
        payload = self._get_json(base_url.rstrip("/") + spec["list_path"])
        if payload is None:
            return {
                "backend": spec["backend"],
                "name": spec["name"],
                "configured": True,
                "reachable": False,
                "models": [],
                "checked_at": self._now(),
                "note": "Configured but not reachable (connection failed, timed out, or returned an error).",
            }
        raw_models = payload.get(spec["models_key"], []) if isinstance(payload, dict) else []
        models = [
            str(item.get(spec["model_name_key"]))
            for item in raw_models
            if isinstance(item, dict) and item.get(spec["model_name_key"])
        ][:50]
        return {
            "backend": spec["backend"],
            "name": spec["name"],
            "configured": True,
            "reachable": True,
            "models": models,
            "checked_at": self._now(),
            "note": "",
        }

    def dashboard(self) -> dict:
        detections = [self.detect(backend) for backend in BACKEND_ORDER]
        reachable = [row for row in detections if row["reachable"]]
        self._log(
            "model_serving_dashboard_viewed",
            f"Model-serving dashboard: {len(reachable)}/{len(detections)} configured backend(s) reachable.",
        )
        return {
            "backends": detections,
            "count": len(detections),
            "reachable_count": len(reachable),
            "real_execution_default": "disabled",
            "note": "Read-only readiness. No model server is ever started by this app.",
            "generated_at": self._now(),
        }

    def dry_run(self, payload: dict[str, Any]) -> dict:
        backend = str(payload.get("backend") or "").strip()[:60]
        model = str(payload.get("model") or "").strip()[:160]
        detection = self.detect(backend)
        if not detection["configured"]:
            result = {
                "accepted": False,
                "backend": backend,
                "model": model,
                "declined_reason": detection["note"],
                "missing_configuration": [f"{backend}_base_url" if backend else "backend"],
                "next_human_action": "Configure the backend's base URL, then rerun dry-run.",
            }
            self._log("model_serving_dry_run", f"Dry-run declined for unconfigured backend={backend}.", blocked=True)
            return result
        if not detection["reachable"]:
            result = {
                "accepted": False,
                "backend": backend,
                "model": model,
                "declined_reason": detection["note"],
                "missing_configuration": [],
                "next_human_action": "Start the local model server yourself, then rerun dry-run.",
            }
            self._log("model_serving_dry_run", f"Dry-run declined; backend={backend} not reachable.", blocked=True)
            return result
        model_loaded = bool(model) and model in detection["models"]
        accepted = bool(detection["models"]) and (not model or model_loaded)
        declined_reason = (
            "" if accepted
            else f"Model '{model}' is not currently loaded on this backend." if model
            else "Backend is reachable but reports no available models."
        )
        result = {
            "accepted": accepted,
            "backend": backend,
            "model": model,
            "available_models": detection["models"],
            "declined_reason": declined_reason,
            "missing_configuration": [],
            "next_human_action": (
                "Local-serving request routing is not wired yet; this is a readiness check only."
                if accepted else
                "Load the model on the backend yourself, then rerun dry-run."
            ),
        }
        self._log(
            "model_serving_dry_run",
            f"Dry-run for backend={backend}, model='{model}', accepted={accepted}.",
            blocked=not accepted,
        )
        return result

    def analytics_summary(self) -> dict:
        # Deliberately does NOT call dashboard()/detect() -- /api/analytics is a
        # hot path polled by the frontend, and every other service's
        # analytics_summary() is a local, non-blocking read. Only reports
        # which backends have a base URL configured, never live reachability.
        configured = sum(1 for spec in BACKEND_SPECS if self._base_url(spec))
        return {
            "model_serving_backends_total": len(BACKEND_SPECS),
            "model_serving_backends_configured": configured,
        }
