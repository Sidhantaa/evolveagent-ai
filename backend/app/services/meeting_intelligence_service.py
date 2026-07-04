from __future__ import annotations

import re
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

_DECISION_CUES = ["decided", "agreed", "we will", "approved", "concluded", "resolved to", "sign off"]
_ACTION_CUES = ["action item", "to-do", "todo", "will ", "needs to", "need to", "follow up", "follow-up", "assign", "by next", "due"]
_TIME_CUE = re.compile(r"\b(\d{1,2}:\d{2}|monday|tuesday|wednesday|thursday|friday|next week|tomorrow|by \w+day|q[1-4])\b", re.IGNORECASE)
# "Name will ..." → owner extraction (leading capitalized token before 'will'/'to').
_OWNER_RE = re.compile(r"\b([A-Z][a-z]+)\s+(?:will|to|should|is going to|owns|takes)\b")


class MeetingIntelligenceService:
    """v79.0 Meeting Intelligence 2.0 — make recordings and meetings useful.

    Deterministic, read-only extraction over a submitted meeting **transcript**: a
    **summary**, **decisions**, **action items** with likely **owners**, generated
    **follow-up drafts**, and a **timeline view** (sentences bearing time cues). It can
    also **propose** a goal + task plan from the meeting — planning-only; it returns a
    proposed structure and does **not** create goals/tasks or send anything. No model
    call, no web. Governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _sentences(text: str) -> list[str]:
        return [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", text or "") if len(s.strip()) > 5]

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="meeting_intelligence",
                agent_name="Meeting Intelligence",
                action_type=action_type,
                tool_used="MeetingIntelligenceService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def analyze(self, transcript: str) -> dict:
        sentences = self._sentences(transcript)
        decisions = [s for s in sentences if any(cue in s.lower() for cue in _DECISION_CUES)]
        action_items = []
        for s in sentences:
            if any(cue in s.lower() for cue in _ACTION_CUES):
                owner_match = _OWNER_RE.search(s)
                action_items.append({"item": s[:200], "owner": owner_match.group(1) if owner_match else None})
        timeline = [s[:160] for s in sentences if _TIME_CUE.search(s)]
        # Summary = first sentence + the decision lines (deterministic, no model).
        summary_parts = ([sentences[0]] if sentences else []) + decisions[:3]
        follow_ups = [self._draft_follow_up(a) for a in action_items[:5]]

        self._log("meeting_analyzed", f"Analyzed a transcript — {len(decisions)} decision(s), {len(action_items)} action item(s).")
        return {
            "summary": " ".join(summary_parts)[:600] or "No content to summarize.",
            "decisions": [d[:200] for d in decisions][:20],
            "action_items": action_items[:20],
            "owners": sorted({a["owner"] for a in action_items if a["owner"]}),
            "follow_up_drafts": follow_ups,
            "timeline": timeline[:20],
            "note": "Deterministic extraction from submitted text — no model call, nothing sent.",
        }

    @staticmethod
    def _draft_follow_up(action: dict) -> dict:
        owner = action.get("owner") or "team"
        return {"to": owner, "draft": f"Hi {owner}, following up on: {action['item']} — could you confirm status and next step? (draft — not sent)"}

    def to_goal_plan(self, transcript: str, title: str | None = None) -> dict:
        analysis = self.analyze(transcript)
        proposed_tasks = [{"title": a["item"][:120], "owner": a["owner"]} for a in analysis["action_items"]]
        self._log("meeting_to_goal_planned", "Proposed a goal + task plan from a meeting (planning-only).")
        return {
            "proposed_goal": {"title": title or "Meeting follow-ups", "description": analysis["summary"][:500]},
            "proposed_tasks": proposed_tasks,
            "task_count": len(proposed_tasks),
            "note": "Planning-only — this proposes a goal and tasks; nothing is created. Use Mission Control to create them if desired.",
        }

    def analytics_summary(self) -> dict:
        return {"meeting_intel_capabilities": 4}

    def summary(self) -> dict:
        return {
            "capabilities": ["analyze", "decisions", "action_items", "follow_up_drafts", "timeline", "to_goal_plan"],
            "note": "Deterministic, read-only meeting intelligence — no model call; conversion to goal/tasks is planning-only.",
        }
