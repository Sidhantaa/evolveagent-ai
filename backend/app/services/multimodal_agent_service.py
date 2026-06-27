from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

ITEM_TYPES = ["screenshot", "ui_bug", "diagram", "whiteboard", "document_image", "custom"]
ANALYSIS_TYPES = ["screenshot", "ui_bug", "diagram", "whiteboard", "document_image", "custom"]

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
    """v21.0 Multi-Modal Real-World Agent.

    A local/mock multimodal workflow foundation. Users register visual item
    metadata and a text description; the service produces structured, rule-based
    analyses (screenshots, UI bugs, diagrams, whiteboards, document images) and
    action plans. It does NOT call a paid vision API — analysis is mock/local
    only and labelled mock_mode=true. Stateful actions are governance-logged.
    """

    items_file = "multimodal_items.json"
    analyses_file = "multimodal_analyses.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

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

    def analyze_item(self, item_id: str, analysis_type: str | None = None) -> dict:
        item = self.get_item(item_id)
        if item is None:
            raise ValueError("Item not found")
        resolved_type = self._enum(analysis_type or item.get("item_type"), ANALYSIS_TYPES, "screenshot")
        outcome = self._analyze(resolved_type, item.get("description", ""))
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
            "mock_mode": True,
            "created_at": self._now(),
        }
        self.storage.append(self.analyses_file, analysis)
        self._log("multimodal_item_analyzed", item.get("workspace_id"), f"Analyzed item {item_id} as {resolved_type} (mock).")
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
        return {
            "total_items": len(items),
            "total_analyses": len(analyses),
            "analysis_type_counts": type_counts,
            "total_issues_found": total_issues,
            "recent_analyses": list(reversed(analyses[-5:])),
            "mock_mode": True,
            "recommended_next_action": (
                "Register a screenshot or diagram and run an analysis."
                if not items
                else "Analyze a registered item or convert findings into a governed task."
            ),
        }
