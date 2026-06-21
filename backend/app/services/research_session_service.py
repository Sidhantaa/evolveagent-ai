from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urlparse
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService
from app.services.workspace_service import WorkspaceService


class ResearchSessionService:
    sessions_file = "research_sessions.json"
    sources_file = "research_sources.json"
    citations_file = "research_citations.json"

    credible_domains = {
        "edu",
        "gov",
        "who.int",
        "nih.gov",
        "ncbi.nlm.nih.gov",
        "openai.com",
        "anthropic.com",
        "google.com",
        "microsoft.com",
    }

    def __init__(
        self,
        storage: StorageService,
        workspace_service: WorkspaceService,
        governance_service: GovernanceService,
    ):
        self.storage = storage
        self.workspace_service = workspace_service
        self.governance = governance_service

    def create_session(
        self,
        query: str,
        workspace_id: str | None = None,
        require_approval: bool = True,
        notes: str | None = None,
    ) -> dict:
        resolved_workspace = self.workspace_service.resolve_workspace_id(workspace_id)
        now = self._now()
        session = {
            "research_id": str(uuid4()),
            "workspace_id": resolved_workspace,
            "query": query.strip(),
            "notes": (notes or "").strip(),
            "status": "pending_approval" if require_approval else "active",
            "approval_required": require_approval,
            "source_count": 0,
            "citation_count": 0,
            "average_credibility_score": 0,
            "created_at": now,
            "updated_at": now,
        }
        self.storage.append(self.sessions_file, session)
        self._log(
            session,
            action_type="research_session_created",
            reason="Governed research session created; external fetching requires approval.",
            risk_score=18 if require_approval else 10,
        )
        return session

    def list_sessions(self, workspace_id: str | None = None) -> list[dict]:
        resolved = self.workspace_service.resolve_workspace_id(workspace_id) if workspace_id else None
        sessions = self.storage.read_list(self.sessions_file)
        if resolved:
            sessions = [item for item in sessions if item.get("workspace_id") == resolved]
        return list(reversed(sessions))

    def get_session(self, research_id: str) -> dict | None:
        session = self._find_session(research_id)
        if not session:
            return None
        return {
            **session,
            "sources": self.list_sources(research_id),
            "citations": self.list_citations(research_id),
            "report": self.generate_report(research_id),
        }

    def approve_session(self, research_id: str, approved: bool = True) -> dict | None:
        session = self._find_session(research_id)
        if not session:
            return None
        status = "active" if approved else "rejected"
        updated = self._update_session(research_id, {"status": status, "approval_required": False})
        self._log(
            updated,
            action_type="research_approval_decision",
            approved=approved,
            blocked=not approved,
            reason="Research session approved." if approved else "Research session rejected; no external research should run.",
            risk_score=10 if approved else 25,
        )
        return updated

    def add_source(self, research_id: str, payload: dict) -> dict | None:
        session = self._find_session(research_id)
        if not session:
            return None
        now = self._now()
        source = {
            "source_id": str(uuid4()),
            "research_id": research_id,
            "workspace_id": session.get("workspace_id"),
            "title": payload.get("title", "").strip(),
            "url": payload.get("url", "").strip(),
            "snippet": payload.get("snippet", "").strip(),
            "publisher": (payload.get("publisher") or "").strip(),
            "fetched": bool(payload.get("fetched")),
            "credibility_score": 0,
            "credibility_reasons": [],
            "created_at": now,
        }
        score, reasons = self.score_source(source)
        source["credibility_score"] = score
        source["credibility_reasons"] = reasons
        self.storage.append(self.sources_file, source)
        self._refresh_counts(research_id)
        self._log(
            session,
            action_type="research_source_registered",
            tool_used="research_source_registry",
            reason=f"Registered source {source['url']} with credibility score {score}.",
            risk_score=max(0, 45 - score // 2),
        )
        return source

    def list_sources(self, research_id: str) -> list[dict]:
        return [item for item in self.storage.read_list(self.sources_file) if item.get("research_id") == research_id]

    def add_citation(self, research_id: str, payload: dict) -> dict | None:
        session = self._find_session(research_id)
        if not session:
            return None
        source = next((item for item in self.list_sources(research_id) if item.get("source_id") == payload.get("source_id")), None)
        if not source:
            return None
        citation = {
            "citation_id": str(uuid4()),
            "research_id": research_id,
            "workspace_id": session.get("workspace_id"),
            "source_id": source["source_id"],
            "source_title": source.get("title"),
            "source_url": source.get("url"),
            "claim": payload.get("claim", "").strip(),
            "quote": (payload.get("quote") or "").strip(),
            "created_at": self._now(),
        }
        self.storage.append(self.citations_file, citation)
        self._refresh_counts(research_id)
        self._log(
            session,
            action_type="research_citation_created",
            tool_used="citation_tracker",
            reason=f"Linked claim to source {source.get('url')}.",
            risk_score=10,
        )
        return citation

    def list_citations(self, research_id: str) -> list[dict]:
        return [item for item in self.storage.read_list(self.citations_file) if item.get("research_id") == research_id]

    def generate_report(self, research_id: str) -> dict | None:
        session = self._find_session(research_id)
        if not session:
            return None
        sources = sorted(self.list_sources(research_id), key=lambda item: item.get("credibility_score", 0), reverse=True)
        citations = self.list_citations(research_id)
        top_sources = sources[:5]
        claims = [item.get("claim", "") for item in citations if item.get("claim")]
        gaps = []
        if not sources:
            gaps.append("No sources have been registered yet.")
        if sources and not citations:
            gaps.append("Sources exist, but no claims have been linked to citations yet.")
        if any(item.get("credibility_score", 0) < 50 for item in sources):
            gaps.append("Some sources have low credibility scores and need verification.")
        return {
            "research_id": research_id,
            "query": session.get("query"),
            "summary": self._summary(session, sources, citations),
            "top_sources": top_sources,
            "cited_claims": claims,
            "source_count": len(sources),
            "citation_count": len(citations),
            "evidence_gaps": gaps,
            "status": session.get("status"),
        }

    def score_source(self, source: dict) -> tuple[int, list[str]]:
        url = source.get("url", "")
        parsed = urlparse(url)
        host = parsed.netloc.lower().replace("www.", "")
        score = 45
        reasons = []
        if parsed.scheme == "https":
            score += 10
            reasons.append("Uses HTTPS.")
        else:
            reasons.append("Does not use HTTPS.")
        if any(host == domain or host.endswith(f".{domain}") for domain in self.credible_domains):
            score += 25
            reasons.append("Domain is an official or high-trust source.")
        if source.get("publisher"):
            score += 8
            reasons.append("Publisher is provided.")
        if len(source.get("snippet", "")) >= 120:
            score += 7
            reasons.append("Snippet has enough context for review.")
        if "blog" in host or "medium.com" in host:
            score -= 10
            reasons.append("Source may be editorial or user-generated.")
        return max(0, min(100, score)), reasons

    def _summary(self, session: dict, sources: list[dict], citations: list[dict]) -> str:
        if not sources:
            return f"Research session for '{session.get('query')}' is ready for governed source collection."
        return (
            f"Research session for '{session.get('query')}' has {len(sources)} source(s), "
            f"{len(citations)} cited claim(s), and an average credibility score of "
            f"{session.get('average_credibility_score', 0)}."
        )

    def _refresh_counts(self, research_id: str) -> None:
        sources = self.list_sources(research_id)
        citations = self.list_citations(research_id)
        avg = round(sum(item.get("credibility_score", 0) for item in sources) / len(sources), 2) if sources else 0
        self._update_session(
            research_id,
            {
                "source_count": len(sources),
                "citation_count": len(citations),
                "average_credibility_score": avg,
            },
        )

    def _find_session(self, research_id: str) -> dict | None:
        return next((item for item in self.storage.read_list(self.sessions_file) if item.get("research_id") == research_id), None)

    def _update_session(self, research_id: str, updates: dict) -> dict:
        sessions = self.storage.read_list(self.sessions_file)
        updated: dict | None = None
        for index, session in enumerate(sessions):
            if session.get("research_id") == research_id:
                updated = {**session, **updates, "updated_at": self._now()}
                sessions[index] = updated
                break
        if updated is None:
            raise ValueError("Research session not found")
        self.storage.write_list(self.sessions_file, sessions)
        return updated

    def _log(
        self,
        session: dict,
        action_type: str,
        reason: str,
        tool_used: str | None = None,
        approved: bool = False,
        blocked: bool = False,
        risk_score: int = 0,
    ) -> None:
        self.governance.log_event(
            GovernanceEvent(
                run_id=session.get("research_id"),
                workspace_id=session.get("workspace_id"),
                task_type="research",
                agent_name="Research Governance Agent",
                action_type=action_type,
                tool_used=tool_used,
                permission_level="read_only" if not approved else "plan_only",
                approved=approved,
                blocked=blocked,
                risk_score=risk_score,
                reason=reason,
            )
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(UTC).isoformat()
