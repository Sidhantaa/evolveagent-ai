from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

MODEL = os.environ.get("DESIGN_AGENT_MODEL", "openai/gpt-4o")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
_ALLOWED_MIME = ("image/png", "image/jpeg", "image/webp", "image/gif")
MAX_DATA_URL = 15 * 1024 * 1024  # ~11 MB image after base64

# Verbatim agent instructions from gokubuilds/Multimodal_design_agent.
AGENTS: dict[str, dict] = {
    "visual": {
        "title": "Visual Design Analysis",
        "prompt": (
            "You are a visual analysis expert that:\n"
            "1. Identifies design elements, patterns, and visual hierarchy\n"
            "2. Analyzes color schemes, typography, and layouts\n"
            "3. Detects UI components and their relationships\n"
            "4. Evaluates visual consistency and branding\n"
            "Be specific and technical in your analysis"
        ),
        "checklist": [
            "Visual hierarchy — is the primary action obvious within 3 seconds?",
            "Color — palette count, contrast ratios (WCAG AA 4.5:1 for text), semantic use.",
            "Typography — type scale, line length (45–75 chars), weight/contrast pairing.",
            "Layout — grid/alignment, spacing rhythm, density vs. whitespace.",
            "Components — button/input/card consistency, state coverage, iconography.",
            "Branding — consistency of tone, logo treatment, visual identity.",
        ],
    },
    "ux": {
        "title": "UX Analysis",
        "prompt": (
            "You are a UX analysis expert that:\n"
            "1. Evaluates user flows and interaction patterns\n"
            "2. Identifies usability issues and opportunities\n"
            "3. Suggests UX improvements based on best practices\n"
            "4. Analyzes accessibility and inclusive design\n"
            "Focus on user-centric insights and practical improvements"
        ),
        "checklist": [
            "Primary flow — steps to the core task; any dead-ends or friction.",
            "Feedback — loading, empty, error, and success states present?",
            "Affordances — do interactive elements look interactive?",
            "Accessibility — focus order, alt text, target sizes (44px), color independence.",
            "Cognitive load — choices per screen, progressive disclosure.",
            "Recovery — undo, confirmation on destructive actions, forgiving inputs.",
        ],
    },
    "market": {
        "title": "Market Research",
        "prompt": (
            "You are a market research expert that:\n"
            "1. Identifies market trends and competitor patterns\n"
            "2. Analyzes similar products and features\n"
            "3. Suggests market positioning and opportunities\n"
            "4. Provides industry-specific insights\n"
            "Focus on actionable market intelligence"
        ),
        "checklist": [
            "Category — what product space does this UI signal?",
            "Comparable patterns — which established products use similar layouts?",
            "Differentiators — what stands out vs. the norm?",
            "Positioning — premium / utilitarian / playful; who is the target user?",
            "Opportunity — an underserved need this design could lean into.",
            "Risk — where it may feel generic or fall behind category expectations.",
        ],
    },
}
_ALIASES = {"visual": "visual", "vision": "visual", "design": "visual", "ux": "ux",
            "usability": "ux", "accessibility": "ux", "market": "market", "research": "market"}


class DesignAgentService:
    """Design Agent — multimodal UI/UX design analysis, in-app.

    Analyzes a design image across three lenses (Visual / UX / Market) using the
    verbatim prompts from the original project. **Mock-safe by default**: unless
    the caller explicitly opts into a live run *and* an ``OPENROUTER_API_KEY`` is
    present in the environment, it returns a deterministic per-lens checklist and
    makes **no network call**. A live run (explicit ``allow_live=True``) is the
    user's approval to send the image to the configured OpenRouter model.

    Secret-safe: the API key is read only from the environment and never stored,
    logged, or returned. Image bytes are never persisted — only analysis text and
    lightweight metadata are kept in history.
    """

    analyses_file = "design_agent_analyses.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _key() -> str | None:
        return os.environ.get("OPENROUTER_API_KEY") or None

    def _log(self, action_type: str, reason: str, risk: int) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="design_agent",
                agent_name="Design Agent",
                action_type=action_type,
                tool_used="DesignAgentService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=risk,
                reason=reason,
            )
        )

    def status(self) -> dict:
        return {
            "available": True,
            "model": MODEL,
            "key_configured": bool(self._key()),
            "live_default": False,
            "lenses": list(AGENTS.keys()),
            "privacy_note": (
                "Mock-safe by default. A live run sends the image to the configured "
                "OpenRouter model only when you opt in and a key is set. The key is "
                "read from the environment and never stored, logged, or returned. "
                "Image bytes are never persisted."
            ),
        }

    @staticmethod
    def _resolve_lenses(analyses: list[str] | None) -> list[str]:
        if not analyses:
            return ["visual", "ux", "market"]
        out: list[str] = []
        for a in analyses:
            key = _ALIASES.get(str(a).strip().lower())
            if key and key not in out:
                out.append(key)
        return out or ["visual", "ux", "market"]

    @staticmethod
    def _validate_image(image: str) -> tuple[bool, str]:
        if not image or not image.startswith("data:"):
            return False, "image must be a data URL (data:image/...;base64,...)"
        if len(image) > MAX_DATA_URL:
            return False, "image is too large (max ~11 MB)"
        header = image.split(",", 1)[0]
        if not any(m in header for m in _ALLOWED_MIME):
            return False, f"unsupported image type; use one of {_ALLOWED_MIME}"
        return True, ""

    def _heuristic_section(self, lens: str) -> dict:
        agent = AGENTS[lens]
        body = "\n".join(f"- [ ] {item}" for item in agent["checklist"])
        return {"lens": lens, "title": agent["title"], "body": body}

    def _model_section(self, lens: str, image: str, context: str) -> dict:
        from openai import OpenAI  # lazy — only needed for live runs

        agent = AGENTS[lens]
        client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=self._key())
        user_text = "Analyze this UI/UX design image."
        if context:
            user_text += f"\n\nAdditional context: {context}"
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": agent["prompt"]},
                {"role": "user", "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": image}},
                ]},
            ],
            max_tokens=1200,
        )
        body = (resp.choices[0].message.content or "").strip()
        return {"lens": lens, "title": agent["title"], "body": body}

    def analyze(self, image: str, analyses: list[str] | None, context: str, allow_live: bool) -> dict:
        ok, err = self._validate_image(image)
        if not ok:
            raise ValueError(err)
        lenses = self._resolve_lenses(analyses)
        context = str(context or "")[:2000]
        want_live = bool(allow_live) and bool(self._key())

        sections: list[dict] = []
        mode = "mock"
        note = ""
        if want_live:
            try:
                for lens in lenses:
                    sections.append(self._model_section(lens, image, context))
                mode = "live"
            except Exception as exc:  # degrade safely to heuristic, never crash
                sections = [self._heuristic_section(lens) for lens in lenses]
                mode = "mock"
                note = f"Live analysis failed ({type(exc).__name__}); showing the review checklist instead."
        else:
            sections = [self._heuristic_section(lens) for lens in lenses]
            if allow_live and not self._key():
                note = "No OPENROUTER_API_KEY set — showing the review checklist. Set the key to enable live analysis."

        record = {
            "id": str(uuid4()),
            "mode": mode,
            "lenses": lenses,
            "context_chars": len(context),
            "result_chars": sum(len(s["body"]) for s in sections),
            "created_at": self._now(),
        }
        self.storage.append(self.analyses_file, record)  # note: no image bytes stored
        self._log("design_analyzed", f"Design analyzed ({mode}, lenses={lenses})", risk=4 if mode == "live" else 1)
        return {"mode": mode, "sections": sections, "note": note, "lenses": lenses, "id": record["id"]}

    def history(self, limit: int = 20) -> dict:
        rows = sorted(self.storage.read_list(self.analyses_file), key=lambda r: r.get("created_at", ""), reverse=True)
        try:
            limit = max(1, min(100, int(limit)))
        except (TypeError, ValueError):
            limit = 20
        return {"history": rows[:limit], "count": len(rows)}

    def analytics_summary(self) -> dict:
        rows = self.storage.read_list(self.analyses_file)
        return {
            "design_agent_analyses": len(rows),
            "design_agent_live_runs": sum(1 for r in rows if r.get("mode") == "live"),
        }

    def summary(self) -> dict:
        return {**self.status(), **self.analytics_summary()}
