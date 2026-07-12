from __future__ import annotations

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Five honest states for a capability, matching the exact vocabulary the
# Route/Page Coverage Audit (docs/architecture/Route-Page-Coverage-Audit.md)
# and the v200 strategy doc ("what is real, mock, blocked, or needs config")
# asked for -- plus "local" for capabilities that are genuinely real but never
# call an external service (a local git command, a keyword search), which is
# a meaningfully different state from a deliberately-simulated mock.
STATUS_REAL = "real"
STATUS_LOCAL = "local"
STATUS_MOCK = "mock"
STATUS_NEEDS_CONFIG = "needs_config"
STATUS_BLOCKED = "blocked"
STATUS_UNKNOWN = "unknown"

ALL_STATUSES = (STATUS_REAL, STATUS_LOCAL, STATUS_MOCK, STATUS_NEEDS_CONFIG, STATUS_BLOCKED, STATUS_UNKNOWN)


def classify_optin_global(status: dict, enabled_key: str, configured_key: str | None = None) -> dict:
    """A persistent global on/off switch (e.g. writes_enabled), optionally gated
    by a separate configured signal (e.g. a token/key)."""
    if configured_key is not None and not bool(status.get(configured_key)):
        return {"status": STATUS_NEEDS_CONFIG, "detail": f"{configured_key} is not set"}
    enabled = bool(status.get(enabled_key))
    return {"status": STATUS_REAL, "detail": f"{enabled_key}=true"} if enabled else {"status": STATUS_MOCK, "detail": f"{enabled_key}=false"}


def classify_key_gated_per_call(status: dict, key_field: str) -> dict:
    """Real-vs-mock is decided per call (e.g. allow_live=True passed by the
    caller), gated only by whether a key is configured."""
    if bool(status.get(key_field)):
        return {"status": STATUS_REAL, "detail": f"{key_field}=true (used per-call when the caller opts in)"}
    return {"status": STATUS_NEEDS_CONFIG, "detail": f"{key_field}=false"}


def classify_mode_string(status: dict, mode_field: str, real_values: set, configured_field: str) -> dict:
    mode = str(status.get(mode_field, "")).lower()
    if mode not in real_values:
        return {"status": STATUS_MOCK, "detail": f"{mode_field}={mode or 'unset'}"}
    if bool(status.get(configured_field)):
        return {"status": STATUS_REAL, "detail": f"{mode_field}={mode}, {configured_field}=true"}
    return {"status": STATUS_NEEDS_CONFIG, "detail": f"{mode_field}={mode} but {configured_field}=false"}


def classify_available(status: dict, real_status: str = STATUS_REAL) -> dict:
    if status.get("available"):
        return {"status": real_status, "detail": "available"}
    return {"status": STATUS_BLOCKED, "detail": "not available"}


def classify_static(value: str, detail: str) -> dict:
    return {"status": value, "detail": detail}


class CapabilityDirectoryService:
    """A single, honest inventory of every real/local/mock/needs-config/blocked
    capability built across this app's opt-in-real surface -- the "feature/
    control center" the v200 strategy doc's Current Execution Priority #2 asks
    for, and the "Capability Directory" the Route/Page Coverage Audit flagged
    as a missing core product piece.

    Every classification is computed from a capability's own already-real
    status()-style method (nothing here is invented or hardcoded to a fixed
    verdict) -- this service only normalizes ~20 already-existing, independently
    real status signals into one consistent vocabulary. The registry (which
    capabilities exist, and how to classify each) is supplied by the caller
    (routes.py, where every underlying service instance already lives) rather
    than constructed here, to avoid this service depending on ~20 other
    services directly.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService, capabilities: list[dict]):
        self.storage = storage
        self.governance = governance_service
        self._capabilities = capabilities

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(GovernanceEvent(
            task_type="capability_directory", agent_name="Capability Directory",
            action_type=action_type, tool_used="CapabilityDirectoryService",
            permission_level="read_only", approved=True, blocked=False, risk_score=1,
            reason=reason,
        ))

    def _last_verified(self, tool_used: str | None) -> str | None:
        """The most recent governance-log event recorded by this capability's
        own service -- a real, computed "last used" signal, not a placeholder."""
        if not tool_used:
            return None
        events = [e for e in self.storage.read_list("governance_log.json") if e.get("tool_used") == tool_used]
        if not events:
            return None
        return max(events, key=lambda e: e.get("created_at", ""))["created_at"]

    def list_capabilities(self, category: str | None = None, status: str | None = None) -> list[dict]:
        entries = []
        for cap in self._capabilities:
            try:
                classification = cap["classify"]()
            except Exception as exc:  # a broken status() must never break the directory itself
                classification = {"status": STATUS_UNKNOWN, "detail": f"status check failed: {type(exc).__name__}: {exc}"}
            entries.append({
                "name": cap["name"],
                "category": cap["category"],
                "route": cap["route"],
                "safety_level": cap["safety_level"],
                "status": classification.get("status", STATUS_UNKNOWN),
                "detail": classification.get("detail", ""),
                "last_verified": self._last_verified(cap.get("tool_used")),
            })
        if category:
            entries = [e for e in entries if e["category"] == category]
        if status:
            entries = [e for e in entries if e["status"] == status]
        entries.sort(key=lambda e: (e["category"], e["name"]))
        return entries

    def categories(self) -> list[str]:
        return sorted({cap["category"] for cap in self._capabilities})

    def summary(self) -> dict:
        entries = self.list_capabilities()
        by_status: dict[str, int] = {}
        for e in entries:
            by_status[e["status"]] = by_status.get(e["status"], 0) + 1
        self._log("capability_directory_viewed", f"Directory viewed: {len(entries)} capabilities.")
        return {
            "total": len(entries),
            "by_status": {s: by_status.get(s, 0) for s in ALL_STATUSES if by_status.get(s)},
            "categories": self.categories(),
            "capabilities": entries,
        }

    def analytics_summary(self) -> dict:
        entries = self.list_capabilities()
        by_status: dict[str, int] = {}
        for e in entries:
            by_status[e["status"]] = by_status.get(e["status"], 0) + 1
        return {
            "capability_directory_total": len(entries),
            "capability_directory_real": by_status.get(STATUS_REAL, 0) + by_status.get(STATUS_LOCAL, 0),
            "capability_directory_needs_config": by_status.get(STATUS_NEEDS_CONFIG, 0),
        }
