from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.agent_profile_service import AgentProfileService
from app.services.durable_workflow_service import DurableWorkflowService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

KINDS = ("agent", "workflow")

# Featured starter bundles, seeded once so the marketplace isn't empty. Each is a
# fully sanitized manifest that installs into a fresh local copy.
STARTER_LISTINGS = [
    {
        "kind": "agent",
        "name": "Chief of Staff",
        "summary": "Plans your day, prioritizes, and keeps you on track.",
        "manifest": {
            "name": "Chief of Staff",
            "role": "Run my day: plan, prioritize, and keep me on track.",
            "personality": {"tone": "professional", "verbosity": "medium"},
            "tools": ["goals", "scheduled_tasks", "productivity"],
            "guardrails": {"allowed_actions": ["plan", "summarize"], "blocked_actions": [], "requires_approval": []},
        },
    },
    {
        "kind": "agent",
        "name": "Research Assistant",
        "summary": "Digs up sources, compares claims, and briefs you.",
        "manifest": {
            "name": "Research Assistant",
            "role": "Dig up sources, compare claims, and brief me.",
            "personality": {"tone": "direct", "verbosity": "high"},
            "tools": ["retrieval", "research_agent", "search"],
            "guardrails": {"allowed_actions": ["summarize", "compare"], "blocked_actions": [], "requires_approval": []},
        },
    },
    {
        "kind": "workflow",
        "name": "Weekly Status Report",
        "summary": "Collects activity, drafts a report, sends on approval.",
        "manifest": {
            "name": "Weekly Status Report",
            "steps": [
                {"name": "Collect this week's activity"},
                {"name": "Summarize progress and blockers"},
                {"name": "Draft the report"},
                {"name": "Send report to stakeholders", "action": "send"},
            ],
        },
    },
    {
        "kind": "workflow",
        "name": "Release Checklist",
        "summary": "Tests, changelog, then deploy/announce behind approval.",
        "manifest": {
            "name": "Release Checklist",
            "steps": [
                {"name": "Run the test suite"},
                {"name": "Assemble the changelog"},
                {"name": "Deploy to production", "action": "deploy"},
                {"name": "Announce the release", "action": "publish"},
            ],
        },
    },
]


class MarketplaceHubService:
    """Phase 7 — a local, offline marketplace for agents and workflows.

    Publish an Agent Studio profile or a durable-workflow definition as a
    **sanitized, portable bundle**, browse featured/community listings, and
    **install** a bundle into a fresh local copy. Everything is local-first —
    no network, no accounts, no uploads. Safety is preserved end-to-end:

    * Publishing strips ids/versions/timestamps and keeps only declarative config.
    * Installing an agent goes through :meth:`AgentProfileService.import_profile`,
      which assigns a fresh id and **re-derives guardrails** (risky actions forced
      back to ``requires_approval``) — a malicious bundle can't smuggle in
      auto-running powers.
    * Installing a workflow creates a durable-workflow definition, so risky steps
      still halt for approval at run time.

    Governance-logged. No secrets are ever stored in a listing.
    """

    listings_file = "marketplace_hub_listings.json"
    installs_file = "marketplace_hub_installs.json"

    def __init__(
        self,
        storage: StorageService,
        governance_service: GovernanceService,
        agent_profile_service: AgentProfileService,
        durable_workflow_service: DurableWorkflowService,
    ):
        self.storage = storage
        self.governance = governance_service
        self.agents = agent_profile_service
        self.workflows = durable_workflow_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="marketplace_hub",
                agent_name="Marketplace Hub",
                action_type=action_type,
                tool_used="MarketplaceHubService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=2,
                reason=reason,
            )
        )

    # -- sanitizing ----------------------------------------------------------
    @staticmethod
    def _clean_agent_manifest(profile: dict) -> dict:
        return {
            "name": str(profile.get("name") or "Untitled Agent")[:120],
            "role": str(profile.get("role") or "")[:1000],
            "description": str(profile.get("description") or "")[:1000],
            "personality": profile.get("personality") or {},
            "tools": [str(t)[:60] for t in (profile.get("tools") or [])][:30],
            "examples": [e for e in (profile.get("examples") or []) if isinstance(e, dict)][:20],
            "guardrails": profile.get("guardrails") or {},
        }

    @staticmethod
    def _clean_workflow_manifest(name: str, steps: list[dict]) -> dict:
        clean_steps = []
        for s in steps or []:
            clean_steps.append({"name": str(s.get("name") or "Step")[:200], "action": str(s.get("action") or "")[:60]})
        return {"name": str(name or "Untitled Workflow")[:120], "steps": clean_steps}

    # -- seed & listing ------------------------------------------------------
    def _ensure_seed(self) -> None:
        if self.storage.read_list(self.listings_file):
            return
        seeded = []
        for entry in STARTER_LISTINGS:
            seeded.append({
                "listing_id": str(uuid4()),
                "kind": entry["kind"],
                "name": entry["name"],
                "summary": entry["summary"],
                "manifest": entry["manifest"],
                "publisher": "EvolveAgent",
                "is_featured": True,
                "installs": 0,
                "created_at": self._now(),
            })
        self.storage.write_list(self.listings_file, seeded)

    def list_listings(self, kind: str | None = None) -> dict:
        self._ensure_seed()
        rows = self.storage.read_list(self.listings_file)
        if kind in KINDS:
            rows = [r for r in rows if r.get("kind") == kind]
        rows = sorted(rows, key=lambda r: (not r.get("is_featured"), r.get("created_at", "")))
        return {"listings": rows, "count": len(rows)}

    def get_listing(self, listing_id: str) -> dict:
        self._ensure_seed()
        for r in self.storage.read_list(self.listings_file):
            if r.get("listing_id") == listing_id:
                return r
        raise ValueError(f"Listing not found: {listing_id}")

    # -- publish -------------------------------------------------------------
    def publish(self, data: dict) -> dict:
        self._ensure_seed()
        data = data or {}
        kind = data.get("kind")
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        source_id = data.get("source_id")

        if kind == "agent":
            if source_id:
                profile = self.agents.get(source_id)  # raises ValueError if missing
            else:
                profile = data.get("manifest") or {}
            if not (profile.get("name") or profile.get("role")):
                raise ValueError("Agent listing needs a source_id or a manifest with name/role")
            manifest = self._clean_agent_manifest(profile)
            name = manifest["name"]
        else:  # workflow
            if source_id:
                definition = next((d for d in self.workflows.list_definitions()["definitions"] if d.get("definition_id") == source_id), None)
                if not definition:
                    raise ValueError(f"Workflow definition not found: {source_id}")
                steps = [{"name": s.get("name"), "action": s.get("action", "")} for s in definition.get("steps", [])]
                name = definition.get("name")
            else:
                m = data.get("manifest") or {}
                steps = m.get("steps") or []
                name = m.get("name") or data.get("name")
            if not steps:
                raise ValueError("Workflow listing needs a source_id or a manifest with steps")
            manifest = self._clean_workflow_manifest(name, steps)
            name = manifest["name"]

        listing = {
            "listing_id": str(uuid4()),
            "kind": kind,
            "name": name,
            "summary": str(data.get("summary") or "")[:280],
            "manifest": manifest,
            "publisher": str(data.get("publisher") or "local")[:80],
            "is_featured": False,
            "installs": 0,
            "created_at": self._now(),
        }
        rows = self.storage.read_list(self.listings_file)
        rows.append(listing)
        self.storage.write_list(self.listings_file, rows)
        self._log("listing_published", f"Published {kind} listing '{name}'")
        return listing

    # -- install -------------------------------------------------------------
    def install(self, listing_id: str) -> dict:
        listing = self.get_listing(listing_id)
        kind = listing["kind"]
        manifest = listing["manifest"]

        if kind == "agent":
            # Sanitizing import: fresh id + guardrails re-derived (risky -> requires_approval).
            installed = self.agents.import_profile(manifest)
            installed_ref = {"type": "agent_profile", "id": installed.get("agent_id"), "name": installed.get("name")}
        else:
            definition = self.workflows.create_definition({"name": manifest.get("name"), "steps": manifest.get("steps")})
            installed_ref = {"type": "workflow_definition", "id": definition.get("definition_id"), "name": definition.get("name")}

        # bump install counter
        rows = self.storage.read_list(self.listings_file)
        for r in rows:
            if r.get("listing_id") == listing_id:
                r["installs"] = int(r.get("installs", 0)) + 1
                break
        self.storage.write_list(self.listings_file, rows)

        record = {
            "install_id": str(uuid4()),
            "listing_id": listing_id,
            "kind": kind,
            "installed": installed_ref,
            "created_at": self._now(),
        }
        self.storage.append(self.installs_file, record)
        self._log("listing_installed", f"Installed {kind} listing '{listing['name']}' -> {installed_ref.get('id')}")
        return {"installed": installed_ref, "listing_id": listing_id, "kind": kind}

    def unpublish(self, listing_id: str) -> dict:
        rows = self.storage.read_list(self.listings_file)
        target = next((r for r in rows if r.get("listing_id") == listing_id), None)
        if not target:
            raise ValueError(f"Listing not found: {listing_id}")
        if target.get("is_featured"):
            raise ValueError("Featured starter listings cannot be removed")
        kept = [r for r in rows if r.get("listing_id") != listing_id]
        self.storage.write_list(self.listings_file, kept)
        self._log("listing_unpublished", f"Unpublished listing '{target.get('name')}'")
        return {"removed": listing_id}

    def installs(self) -> dict:
        rows = sorted(self.storage.read_list(self.installs_file), key=lambda r: r.get("created_at", ""), reverse=True)
        return {"installs": rows, "count": len(rows)}

    # -- analytics -----------------------------------------------------------
    def analytics_summary(self) -> dict:
        self._ensure_seed()
        listings = self.storage.read_list(self.listings_file)
        by_kind: dict[str, int] = {}
        for r in listings:
            by_kind[r.get("kind", "unknown")] = by_kind.get(r.get("kind", "unknown"), 0) + 1
        return {
            "marketplace_hub_listings": len(listings),
            "marketplace_hub_installs": len(self.storage.read_list(self.installs_file)),
            "marketplace_hub_listings_by_kind": by_kind,
        }

    def summary(self) -> dict:
        return {**self.analytics_summary(), "kinds": list(KINDS)}
