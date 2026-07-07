from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.mcp_connector_service import MCPConnectorService
from app.services.mcp_readonly_adapter import MCPReadOnlyAdapter
from app.services.storage_service import StorageService

# Default execution mode is ALWAYS mock. Real execution is only ever performed by
# the opt-in, sandboxed, read-only adapter (v43) for an allow-listed set of
# actions; otherwise every run falls back to this simulated mode. No code path
# runs a shell command, makes a network call, writes/deletes files, or returns
# secrets.
EXECUTION_MODE = "mock"

REQUEST_STATUSES = ["pending_approval", "approved", "rejected", "executed", "blocked"]


class MCPExecutionService:
    """v42.0 MCP Execution Adapter (approval-gated, mock-by-default).

    Adds a governed *request → approve → run → record* loop on top of the v41
    connector planning layer. It reuses the connector service's planning rules to
    validate every request (blocked-list, allow-list, risk/approval), then:

      - read-only low-risk actions are auto-approved,
      - everything else stays ``pending_approval`` until a human approves,
      - blocked / disabled / not-allowed actions never create a runnable request.

    Running an approved request invokes a **mock adapter** — execution is always
    simulated (``EXECUTION_MODE = "mock"``); no real MCP/network/shell/device call
    is made and no secrets are read or returned. Every step is governance-logged.
    """

    requests_file = "mcp_execution_requests.json"
    results_file = "mcp_execution_results.json"

    def __init__(
        self,
        storage: StorageService,
        governance_service: GovernanceService,
        connector_service: MCPConnectorService,
        readonly_adapter: MCPReadOnlyAdapter | None = None,
        github_adapter=None,
    ):
        self.storage = storage
        self.governance = governance_service
        self.connectors = connector_service
        # v43: opt-in, sandboxed, read-only real adapter (mock fallback by default).
        self.readonly_adapter = readonly_adapter or MCPReadOnlyAdapter()
        # v100: opt-in real adapter for the GitHub connector's read-only actions.
        # None until routes.py wires it (after github_connector_service exists).
        self.github_adapter = github_adapter

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _risk_score(self, risk_level: str) -> int:
        return {"low": 3, "medium": 6, "high": 9}.get(risk_level, 5)

    def _log(self, action_type: str, reason: str, risk_level: str, blocked: bool, approved: bool) -> str:
        event = self.governance.log_event(
            GovernanceEvent(
                task_type="mcp_execution",
                agent_name="MCP Execution Adapter",
                action_type=action_type,
                tool_used="MCPExecutionService",
                permission_level="read_only",
                approved=approved,
                blocked=blocked,
                risk_score=self._risk_score(risk_level),
                reason=reason,
            )
        )
        return getattr(event, "created_at", None) or self._now()

    def _requests(self) -> list[dict]:
        return self.storage.read_list(self.requests_file)

    def _get_request(self, request_id: str) -> dict | None:
        return next((r for r in self._requests() if r.get("request_id") == request_id), None)

    # ------------------------------------------------------------------
    # Request execution (validates via v41 planning)
    # ------------------------------------------------------------------
    def request_execution(self, connector_id: str, action_name: str, payload: dict | None = None, workspace_id: str | None = None) -> dict:
        # Reuse the connector planning layer for all risk/block/allow validation.
        plan = self.connectors.plan_connector_action(connector_id, action_name, payload or {}, workspace_id)
        if not plan.get("planned"):
            # Blocked at planning — record a blocked request (not runnable) and stop.
            record = {
                "request_id": str(uuid4()),
                "connector_id": connector_id,
                "action_name": self._clean(action_name, 80),
                "status": "blocked",
                "requires_approval": False,
                "risk_level": plan.get("risk_level", "medium"),
                "blocked_reason": plan.get("blocked_reason"),
                "plan": [],
                "workspace_id": self._clean(workspace_id, 120) or None,
                "created_at": self._now(),
                "updated_at": self._now(),
            }
            self.storage.append(self.requests_file, record)
            self._log("mcp_execution_blocked", f"Execution request blocked for {connector_id}: {plan.get('blocked_reason')}", record["risk_level"], blocked=True, approved=False)
            return record

        requires_approval = plan.get("requires_approval", True)
        status = "pending_approval" if requires_approval else "approved"
        record = {
            "request_id": str(uuid4()),
            "connector_id": connector_id,
            "action_name": self._clean(action_name, 80),
            "status": status,
            "requires_approval": requires_approval,
            "risk_level": plan.get("risk_level", "medium"),
            "blocked_reason": None,
            "plan": plan.get("plan", []),
            "workspace_id": self._clean(workspace_id, 120) or None,
            "result_id": None,
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.requests_file, record)
        self._log(
            "mcp_execution_requested",
            f"Execution requested for {connector_id} action '{record['action_name']}' (status={status}).",
            record["risk_level"],
            blocked=False,
            approved=not requires_approval,
        )
        return record

    def list_requests(self, connector_id: str | None = None, limit: int = 100) -> list[dict]:
        requests = self._requests()
        if connector_id:
            requests = [r for r in requests if r.get("connector_id") == connector_id]
        return list(reversed(requests[-limit:]))

    def get_request(self, request_id: str) -> dict | None:
        request = self._get_request(request_id)
        if request is None:
            return None
        enriched = dict(request)
        if request.get("result_id"):
            enriched["result"] = next((r for r in self.storage.read_list(self.results_file) if r.get("result_id") == request["result_id"]), None)
        return enriched

    # ------------------------------------------------------------------
    # Approve / reject
    # ------------------------------------------------------------------
    def approve_execution(self, request_id: str) -> dict:
        requests = self._requests()
        request = next((r for r in requests if r.get("request_id") == request_id), None)
        if request is None:
            raise ValueError("Execution request not found")
        if request["status"] != "pending_approval":
            raise ValueError(f"Request is not pending approval (status={request['status']})")
        request["status"] = "approved"
        request["updated_at"] = self._now()
        self.storage.write_list(self.requests_file, requests)
        self._log("mcp_execution_approved", f"Approved execution request {request_id}.", request.get("risk_level", "medium"), blocked=False, approved=True)
        return request

    def reject_execution(self, request_id: str) -> dict:
        requests = self._requests()
        request = next((r for r in requests if r.get("request_id") == request_id), None)
        if request is None:
            raise ValueError("Execution request not found")
        if request["status"] not in ("pending_approval", "approved"):
            raise ValueError(f"Request cannot be rejected (status={request['status']})")
        request["status"] = "rejected"
        request["updated_at"] = self._now()
        self.storage.write_list(self.requests_file, requests)
        self._log("mcp_execution_rejected", f"Rejected execution request {request_id}.", request.get("risk_level", "medium"), blocked=False, approved=False)
        return request

    # ------------------------------------------------------------------
    # Run (mock executor only)
    # ------------------------------------------------------------------
    def run_execution(self, request_id: str) -> dict:
        requests = self._requests()
        request = next((r for r in requests if r.get("request_id") == request_id), None)
        if request is None:
            raise ValueError("Execution request not found")
        if request["status"] == "pending_approval":
            raise ValueError("Request requires approval before it can run")
        if request["status"] != "approved":
            raise ValueError(f"Request is not runnable (status={request['status']})")

        # Re-validate against the connector at run time — never trust a stale request.
        connector = self.connectors.get_connector(request["connector_id"])
        if connector is None:
            raise ValueError("Connector not found")
        if connector.get("mode") == "disabled" or not connector.get("enabled"):
            request["status"] = "blocked"
            request["blocked_reason"] = "Connector is disabled or not enabled at run time."
            request["updated_at"] = self._now()
            self.storage.write_list(self.requests_file, requests)
            self._log("mcp_execution_blocked", f"Blocked run of {request_id}: connector disabled/not enabled.", request.get("risk_level", "high"), blocked=True, approved=False)
            return self.get_request(request_id)

        # v43/v100: try real adapters first (readonly, then github); if every
        # adapter declines (opt-in off, action not allow-listed, or wrong
        # connector), fall back to mock. Adapters never raise — a decline is a
        # plain None return, and an internal failure degrades to a safe result.
        adapter_result = self.readonly_adapter.try_execute(connector, request["action_name"], {})
        if adapter_result is None and self.github_adapter is not None:
            adapter_result = self.github_adapter.try_execute(connector, request["action_name"], {})
        if adapter_result is not None:
            result = {
                "result_id": str(uuid4()),
                "request_id": request_id,
                "connector_id": request["connector_id"],
                "action_name": request["action_name"],
                "execution_mode": adapter_result.get("execution_mode", "real_read_only"),
                "success": adapter_result.get("success", False),
                "output": adapter_result.get("output", {}),
                "secrets_used": False,
                "real_call_made": adapter_result.get("real_call_made", True),
                "note": adapter_result.get("note", "Real read-only execution (sandboxed, stdlib only)."),
                "created_at": self._now(),
            }
            run_mode = result["execution_mode"]
        else:
            result = {
                "result_id": str(uuid4()),
                "request_id": request_id,
                "connector_id": request["connector_id"],
                "action_name": request["action_name"],
                "execution_mode": EXECUTION_MODE,
                "success": True,
                "output": self._mock_output(connector, request["action_name"]),
                "secrets_used": False,
                "real_call_made": False,
                "note": "Simulated execution — no real MCP server, network call, shell command, or device action was performed.",
                "created_at": self._now(),
            }
            run_mode = EXECUTION_MODE
        self.storage.append(self.results_file, result)
        request["status"] = "executed"
        request["result_id"] = result["result_id"]
        request["updated_at"] = self._now()
        self.storage.write_list(self.requests_file, requests)
        self._log("mcp_execution_run", f"Ran ({run_mode}) execution {request_id} for action '{request['action_name']}'.", request.get("risk_level", "medium"), blocked=False, approved=True)
        return self.get_request(request_id)

    def _mock_output(self, connector: dict, action_name: str) -> dict:
        return {
            "connector": connector.get("name"),
            "action": action_name,
            "summary": f"[MOCK] '{action_name}' on '{connector.get('name')}' would run here once a real, approved adapter is configured.",
            "items": [],
        }

    def list_results(self, limit: int = 50) -> list[dict]:
        return list(reversed(self.storage.read_list(self.results_file)[-limit:]))

    def adapter_status(self) -> dict:
        """v43: expose the read-only adapter's opt-in state, allow-list, and sandbox.
        v100: adds a nested 'github' section for the GitHub adapter, if wired —
        the top-level (readonly) shape is unchanged for backward compatibility."""
        status = self.readonly_adapter.status()
        if self.github_adapter is not None:
            status["github"] = self.github_adapter.status()
        return status

    # ------------------------------------------------------------------
    # Summary + analytics
    # ------------------------------------------------------------------
    def summarize(self) -> dict:
        requests = self._requests()
        by_status = {status: sum(1 for r in requests if r.get("status") == status) for status in REQUEST_STATUSES}
        real_readonly_enabled = self.readonly_adapter.enabled()
        return {
            "total_requests": len(requests),
            "by_status": by_status,
            "pending_approval": by_status.get("pending_approval", 0),
            "executed": by_status.get("executed", 0),
            "blocked": by_status.get("blocked", 0),
            "execution_mode": EXECUTION_MODE,
            "real_readonly_enabled": real_readonly_enabled,
            "real_readonly_actions": list(self.readonly_adapter.status()["allowed_actions"]),
            "recent_requests": self.list_requests(limit=10),
            "safety_summary": {
                # Only the opt-in, sandboxed, read-only adapter can ever run for real.
                "real_execution_enabled": real_readonly_enabled,
                "real_execution_readonly_only": True,
                "secrets_used": False,
                "shell_used": False,
                "network_calls_made": False,
                "write_actions_require_approval": True,
            },
        }

    def analytics_summary(self) -> dict:
        requests = self._requests()
        results = self.storage.read_list(self.results_file)
        return {
            "mcp_execution_requests": len(requests),
            "mcp_executions_run": sum(1 for r in requests if r.get("status") == "executed"),
            "mcp_executions_pending": sum(1 for r in requests if r.get("status") == "pending_approval"),
            "mcp_executions_blocked": sum(1 for r in requests if r.get("status") == "blocked"),
            "mcp_executions_real_readonly": sum(1 for r in results if r.get("execution_mode") == "real_read_only"),
            "mcp_execution_mode": EXECUTION_MODE,
            "mcp_real_readonly_enabled": self.readonly_adapter.enabled(),
        }
