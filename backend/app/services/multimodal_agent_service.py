from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

ITEM_TYPES = ["screenshot", "ui_bug", "diagram", "whiteboard", "document_image", "custom"]
ANALYSIS_TYPES = ["screenshot", "ui_bug", "diagram", "whiteboard", "document_image", "custom"]

# v170 — real vision analysis (opt-in). Reuses the same OPENROUTER_API_KEY /
# OPENROUTER_BASE_URL env vars as DesignAgentService (one key, not two), but a
# dedicated model env var since this service analyzes a broader range of
# visual content than DesignAgentService's design-image lenses.
MODEL = os.environ.get("MULTIMODAL_AGENT_MODEL", "openai/gpt-4o")
OPENROUTER_BASE_URL = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
_ALLOWED_MIME = ("image/png", "image/jpeg", "image/webp", "image/gif")
MAX_DATA_URL = 15 * 1024 * 1024  # ~11 MB image after base64

_VISION_PROMPTS = {
    "screenshot": (
        "You are a UI screenshot analysis expert. Identify visible UI elements "
        "(buttons, forms, menus, tables, charts, etc.), describe the layout, and "
        "note anything visually inconsistent. Be specific and technical."
    ),
    "ui_bug": (
        "You are a UI bug-triage expert. Identify visual defects — overlapping "
        "elements, misalignment, cut-off content, low contrast, broken assets, "
        "overflow, blank states, visible error messages. For each defect, name "
        "its likely location and a concrete fix suggestion."
    ),
    "diagram": (
        "You are a systems-diagram analysis expert. Identify nodes, edges/arrows, "
        "and their relationships. Describe the flow, architecture, or process the "
        "diagram represents."
    ),
    "whiteboard": (
        "You are a whiteboard-sketch analysis expert. Identify hand-drawn "
        "components, groupings, and any legible text/labels. Describe the idea "
        "or flow being sketched."
    ),
    "document_image": (
        "You are a document-image analysis expert. Extract the key visible "
        "text and structure (headings, tables, lists) and summarize the "
        "document's content."
    ),
    "custom": (
        "You are a general visual analysis expert. Describe what you see and "
        "any details relevant to a software/product context."
    ),
}

# Local keyword heuristics for mock visual analysis (no real vision API).
_UI_ELEMENT_HINTS = {
    "button": "Button element",
    "form": "Form element",
    "input": "Input field",
    "menu": "Navigation menu",
    "modal": "Modal dialog",
    "table": "Data table",
    "chart": "Chart/graph",
    "header": "Header region",
    "footer": "Footer region",
    "sidebar": "Sidebar",
    "card": "Card component",
    "icon": "Icon",
}
_BUG_HINTS = {
    "overlap": "Overlapping elements detected.",
    "cut off": "Content appears cut off.",
    "misaligned": "Misaligned layout.",
    "broken": "Broken/missing asset.",
    "contrast": "Low color contrast.",
    "overflow": "Content overflow.",
    "blank": "Blank/empty state.",
    "error": "Error message visible.",
    "spacing": "Inconsistent spacing.",
}
_DIAGRAM_HINTS = {
    "node": "Node",
    "arrow": "Directed edge/flow",
    "box": "Process box",
    "database": "Datastore",
    "service": "Service component",
    "queue": "Queue/buffer",
    "decision": "Decision point",
}


class MultimodalAgentService:
    """v21.0 Multi-Modal Real-World Agent — v170 upgrade adds real vision.

    Users register visual item metadata and a text description; by default the
    service produces structured, rule-based analyses (screenshots, UI bugs,
    diagrams, whiteboards, document images) with no vision API call at all
    (labelled mock_mode=true) — this path is unchanged and remains the default.

    v170: analyze_item() can now optionally take a real image (a base64 data
    URL, passed per-call — never persisted, same privacy contract as
    DesignAgentService) plus allow_live=True. When an OPENROUTER_API_KEY is
    also configured, this sends the image to a real vision model for genuine
    analysis instead of keyword-matching a text description. Any missing
    image/key/opt-in, or a live-call failure, degrades safely to the original
    heuristic path with a clear note — never a crash, never a silent mock
    dressed up as real.
    """

    items_file = "multimodal_items.json"
    analyses_file = "multimodal_analyses.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _key() -> str | None:
        return os.environ.get("OPENROUTER_API_KEY") or None

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

    def _model_analyze(self, analysis_type: str, image: str, description: str) -> dict:
        from openai import OpenAI  # lazy — only needed for live runs

        client = OpenAI(base_url=OPENROUTER_BASE_URL, api_key=self._key())
        user_text = f"Analyze this {analysis_type.replace('_', ' ')} image."
        if description:
            user_text += f"\n\nAdditional context: {description}"
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": _VISION_PROMPTS.get(analysis_type, _VISION_PROMPTS["custom"])},
                {"role": "user", "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": image}},
                ]},
            ],
            max_tokens=1000,
        )
        body = (resp.choices[0].message.content or "").strip()
        return {
            "summary": body[:4000],
            "detected_elements": [],
            "issues": [],
            "recommended_actions": [],
            "confidence": 95,
        }

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _enum(self, value, allowed: list[str], default: str) -> str:
        candidate = str(value or "").strip().lower()
        return candidate if candidate in allowed else default

    def _filter_workspace(self, items: list[dict], workspace_id: str | None) -> list[dict]:
        if not workspace_id:
            return items
        return [item for item in items if item.get("workspace_id") == workspace_id]

    def _log(self, action_type: str, workspace_id: str | None, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                workspace_id=workspace_id,
                task_type="multimodal_agent",
                agent_name="Multi-Modal Agent",
                action_type=action_type,
                tool_used="MultimodalAgentService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    @staticmethod
    def _match(text: str, hints: dict[str, str]) -> list[str]:
        found: list[str] = []
        for keyword, label in hints.items():
            if keyword in text and label not in found:
                found.append(label)
        return found

    # ------------------------------------------------------------------
    # Items
    # ------------------------------------------------------------------
    def list_items(self, workspace_id: str | None = None) -> list[dict]:
        return self._filter_workspace(self.storage.read_list(self.items_file), workspace_id)

    def get_item(self, item_id: str) -> dict | None:
        return next((item for item in self.storage.read_list(self.items_file) if item.get("item_id") == item_id), None)

    def create_item(self, data: dict) -> dict:
        item = {
            "item_id": str(uuid4()),
            "workspace_id": data.get("workspace_id"),
            "title": self._clean(data.get("title"), 200),
            "item_type": self._enum(data.get("item_type"), ITEM_TYPES, "screenshot"),
            "description": self._clean(data.get("description"), 6000),
            "source_ref": self._clean(data.get("source_ref"), 300) or None,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.items_file, item)
        self._log("multimodal_item_created", item["workspace_id"], f"Registered visual item: {item['title'] or item['item_id']}.")
        return item

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------
    def _analyze(self, analysis_type: str, description: str) -> dict:
        text = (description or "").lower()
        detected: list[str] = []
        issues: list[str] = []
        actions: list[str] = []

        if analysis_type in {"screenshot", "ui_bug"}:
            detected = self._match(text, _UI_ELEMENT_HINTS)
            issues = self._match(text, _BUG_HINTS)
            if analysis_type == "ui_bug" and not issues:
                issues = ["No explicit defect keywords found — review visually for layout/contrast issues."]
            actions = [
                "Reproduce the state described and capture exact element bounds.",
                "Create a fix plan and route any code change through the approval workflow.",
            ]
        elif analysis_type in {"diagram", "whiteboard"}:
            detected = self._match(text, _DIAGRAM_HINTS)
            if not detected:
                detected = ["Free-form sketch — components not explicitly named."]
            actions = [
                "Convert detected nodes/edges into a structured task or workflow plan.",
                "Confirm relationships with the author before implementing.",
            ]
        elif analysis_type == "document_image":
            detected = ["Document image — text regions (mock extraction)."]
            actions = ["Use the existing document workflow to capture action items and risks."]
        else:
            detected = ["Custom visual input."]
            actions = ["Describe the desired outcome to generate a concrete plan."]

        confidence = max(10, min(85, 30 + len(detected) * 12 + len(issues) * 6))
        summary_bits = []
        if detected:
            summary_bits.append(f"{len(detected)} element(s) detected")
        if issues:
            summary_bits.append(f"{len(issues)} potential issue(s)")
        summary = f"Mock {analysis_type} analysis: " + (", ".join(summary_bits) if summary_bits else "no strong signals detected") + "."
        return {
            "summary": summary,
            "detected_elements": detected,
            "issues": issues,
            "recommended_actions": actions,
            "confidence": confidence,
        }

    def analyze_item(
        self, item_id: str, analysis_type: str | None = None, image: str | None = None, allow_live: bool = False,
    ) -> dict:
        item = self.get_item(item_id)
        if item is None:
            raise ValueError("Item not found")
        resolved_type = self._enum(analysis_type or item.get("item_type"), ANALYSIS_TYPES, "screenshot")

        if image:
            ok, err = self._validate_image(image)
            if not ok:
                raise ValueError(err)

        want_live = bool(allow_live) and bool(image) and bool(self._key())
        mode = "mock"
        note = ""
        if want_live:
            try:
                outcome = self._model_analyze(resolved_type, image, item.get("description", ""))
                mode = "live"
            except Exception as exc:  # degrade safely to heuristic, never crash
                outcome = self._analyze(resolved_type, item.get("description", ""))
                note = f"Live analysis failed ({type(exc).__name__}); showing heuristic analysis instead."
        else:
            outcome = self._analyze(resolved_type, item.get("description", ""))
            if allow_live and not image:
                note = "No image provided — showing heuristic analysis. Pass an image to enable live vision analysis."
            elif allow_live and image and not self._key():
                note = "No OPENROUTER_API_KEY set — showing heuristic analysis. Set the key to enable live vision analysis."

        analysis = {
            "analysis_id": str(uuid4()),
            "item_id": item_id,
            "workspace_id": item.get("workspace_id"),
            "analysis_type": resolved_type,
            "summary": outcome["summary"],
            "detected_elements": outcome["detected_elements"],
            "issues": outcome["issues"],
            "recommended_actions": outcome["recommended_actions"],
            "confidence": outcome["confidence"],
            "mock_mode": mode == "mock",
            "mode": mode,
            "note": note,
            "created_at": self._now(),
        }
        self.storage.append(self.analyses_file, analysis)
        self._log("multimodal_item_analyzed", item.get("workspace_id"), f"Analyzed item {item_id} as {resolved_type} ({mode}).")
        return analysis

    def list_analyses(self, workspace_id: str | None = None, limit: int = 25) -> list[dict]:
        analyses = self._filter_workspace(self.storage.read_list(self.analyses_file), workspace_id)
        return list(reversed(analyses[-limit:]))

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self, workspace_id: str | None = None) -> dict:
        items = self.list_items(workspace_id)
        analyses = self._filter_workspace(self.storage.read_list(self.analyses_file), workspace_id)
        type_counts: dict[str, int] = {}
        for analysis in analyses:
            key = analysis.get("analysis_type", "custom")
            type_counts[key] = type_counts.get(key, 0) + 1
        total_issues = sum(len(a.get("issues", [])) for a in analyses)
        live_analyses = sum(1 for a in analyses if a.get("mode") == "live")
        return {
            "total_items": len(items),
            "total_analyses": len(analyses),
            "live_analyses": live_analyses,
            "analysis_type_counts": type_counts,
            "total_issues_found": total_issues,
            "recent_analyses": list(reversed(analyses[-5:])),
            "mock_mode": not bool(self._key()),
            "recommended_next_action": (
                "Register a screenshot or diagram and run an analysis."
                if not items
                else "Analyze a registered item or convert findings into a governed task."
            ),
        }

    def status(self) -> dict:
        return {
            "available": True,
            "model": MODEL,
            "key_configured": bool(self._key()),
            "live_default": False,
            "item_types": ITEM_TYPES,
            "privacy_note": (
                "Mock-safe by default. A live analysis sends the image to the "
                "configured OpenRouter model only when the caller passes an "
                "image and allow_live=True, and a key is set. The key is read "
                "from the environment and never stored, logged, or returned. "
                "Image bytes are never persisted."
            ),
        }

    def analytics_summary(self) -> dict:
        analyses = self.storage.read_list(self.analyses_file)
        return {
            "multimodal_agent_analyses": len(analyses),
            "multimodal_agent_live_analyses": sum(1 for a in analyses if a.get("mode") == "live"),
        }

    def summary(self) -> dict:
        return {**self.status(), **self.analytics_summary()}
