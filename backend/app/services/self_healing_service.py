from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.safe_command_runner import SafeCommandRunner
from app.services.storage_service import StorageService

# Failure / dependency text signatures parsed from safe command output only.
_FAILURE_SIGNATURES = {
    "test_failure": ["failed", "assertionerror", "test session", "errors", "e   "],
    "build_failure": ["build failed", "npm err!", "error ts", "compilation error", "vite build"],
}
_DEPENDENCY_SIGNATURES = [
    "modulenotfounderror",
    "no module named",
    "cannot find module",
    "importerror",
    "no matching distribution",
    "unmet peer dependency",
    "npm warn deprecated",
    "deprecated",
]


class SelfHealingService:
    """v24.0 Self-Healing Project System.

    Monitors build/test health using ONLY the existing allowlisted
    SafeCommandRunner, parses failures into findings, drafts repair tasks, and
    verifies repairs by re-running allowlisted commands. It NEVER auto-applies
    patches, installs packages, or runs unrestricted shell. A mock mode lets
    callers supply command output (for demos/tests) without executing anything.
    Every action is governance-logged.
    """

    checks_file = "self_healing_checks.json"
    findings_file = "self_healing_findings.json"
    repairs_file = "self_healing_repairs.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, command_runner: SafeCommandRunner):
        self.storage = storage
        self.governance = governance_service
        self.runner = command_runner

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str, blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="self_healing",
                agent_name="Self-Healing Service",
                action_type=action_type,
                tool_used="SelfHealingService",
                permission_level="read_only",
                approved=not blocked,
                blocked=blocked,
                risk_score=10 if blocked else 5,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------
    def _resolve_result(self, command: str, mode: str, mock_stdout: str, mock_stderr: str, mock_exit_code: int) -> dict:
        if mode == "mock":
            success = mock_exit_code == 0
            return {
                "command": command,
                "exit_code": mock_exit_code,
                "stdout": (mock_stdout or "")[-4000:],
                "stderr": (mock_stderr or "")[-4000:],
                "success": success,
                "blocked": False,
                "mode": "mock",
            }
        # Real mode: ONLY the allowlisted runner executes. Unsafe commands are blocked.
        result = self.runner.run(command)
        return {
            "command": result.command,
            "exit_code": result.exit_code,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
            "success": result.success,
            "blocked": result.exit_code == 126,
            "mode": "run",
        }

    def create_check(
        self,
        command: str = "pytest",
        mode: str = "run",
        mock_stdout: str = "",
        mock_stderr: str = "",
        mock_exit_code: int = 0,
        workspace_id: str | None = None,
    ) -> dict:
        resolved_mode = "mock" if mode == "mock" else "run"
        result = self._resolve_result(command, resolved_mode, mock_stdout, mock_stderr, mock_exit_code)
        check = {
            "check_id": str(uuid4()),
            "workspace_id": workspace_id,
            "command": result["command"],
            "mode": result["mode"],
            "exit_code": result["exit_code"],
            "success": result["success"],
            "blocked": result["blocked"],
            "stdout_tail": result["stdout"][-1200:],
            "stderr_tail": result["stderr"][-1200:],
            "created_at": self._now(),
        }
        self.storage.append(self.checks_file, check)
        findings = []
        if not result["success"] and not result["blocked"]:
            findings = self._create_findings(check, result)
        self._log(
            "self_healing_check_run",
            f"Ran check '{command}' (mode={result['mode']}, success={result['success']}, blocked={result['blocked']}).",
            blocked=result["blocked"],
        )
        return {"check": check, "findings": findings, "blocked": result["blocked"]}

    def list_checks(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.checks_file)[-limit:]))

    # ------------------------------------------------------------------
    # Findings
    # ------------------------------------------------------------------
    def _create_findings(self, check: dict, result: dict) -> list[dict]:
        text = f"{result.get('stdout', '')}\n{result.get('stderr', '')}".lower()
        created: list[dict] = []

        finding_type = None
        for ftype, signatures in _FAILURE_SIGNATURES.items():
            if any(sig in text for sig in signatures):
                finding_type = ftype
                break
        if finding_type is None:
            finding_type = "build_failure" if "build" in check.get("command", "") else "test_failure"
        created.append(self._store_finding(check, finding_type, f"Command '{check['command']}' failed (exit {check['exit_code']}).", "high"))

        for signature in _DEPENDENCY_SIGNATURES:
            if signature in text:
                created.append(
                    self._store_finding(
                        check,
                        "dependency_warning",
                        f"Dependency signal detected: '{signature}'.",
                        "medium",
                    )
                )
                break  # one dependency finding per check is enough
        return created

    def _store_finding(self, check: dict, finding_type: str, message: str, severity: str) -> dict:
        finding = {
            "finding_id": str(uuid4()),
            "check_id": check["check_id"],
            "workspace_id": check.get("workspace_id"),
            "finding_type": finding_type,
            "message": message,
            "severity": severity,
            "source_command": check["command"],
            "status": "open",
            "created_at": self._now(),
        }
        self.storage.append(self.findings_file, finding)
        self._log("self_healing_finding_created", f"Finding ({finding_type}): {message}")
        return finding

    def list_findings(self, limit: int = 50) -> list[dict]:
        return list(reversed(self.storage.read_list(self.findings_file)[-limit:]))

    def get_finding(self, finding_id: str) -> dict | None:
        return next((f for f in self.storage.read_list(self.findings_file) if f.get("finding_id") == finding_id), None)

    # ------------------------------------------------------------------
    # Repair tasks (draft only — never auto-applied)
    # ------------------------------------------------------------------
    def create_repair_task(self, finding_id: str) -> dict:
        finding = self.get_finding(finding_id)
        if finding is None:
            raise ValueError("Finding not found")
        ftype = finding.get("finding_type")
        if ftype == "dependency_warning":
            plan = [
                "Identify the missing/deprecated dependency from the finding.",
                "Propose the version change in the manifest for human review (no install performed).",
                "Re-run the allowlisted build/test command to confirm after a human applies it.",
            ]
        elif ftype == "build_failure":
            plan = [
                "Open the failing build output and locate the first error.",
                "Draft a minimal source fix and route it through the approval workflow.",
                "Re-run `npm run build` to verify after approval.",
            ]
        else:
            plan = [
                "Open the failing test(s) named in the output.",
                "Draft a minimal code/test fix and route it through the approval workflow.",
                "Re-run `pytest` to verify after approval.",
            ]
        repair = {
            "repair_id": str(uuid4()),
            "finding_id": finding_id,
            "workspace_id": finding.get("workspace_id"),
            "title": f"Repair: {finding.get('message')}",
            "finding_type": ftype,
            "suggested_patch_plan": plan,
            "status": "draft",
            "requires_approval": True,
            "auto_apply": False,
            "verify_command": "npm run build" if ftype == "build_failure" else "pytest",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.repairs_file, repair)
        # Mark finding as having a repair drafted.
        findings = self.storage.read_list(self.findings_file)
        for item in findings:
            if item.get("finding_id") == finding_id:
                item["status"] = "repair_drafted"
        self.storage.write_list(self.findings_file, findings)
        self._log("self_healing_repair_task_created", f"Drafted repair task for finding {finding_id} (no auto-apply).")
        return repair

    def get_repair(self, repair_id: str) -> dict | None:
        return next((r for r in self.storage.read_list(self.repairs_file) if r.get("repair_id") == repair_id), None)

    def verify_repair(
        self,
        repair_id: str,
        mode: str = "run",
        mock_stdout: str = "",
        mock_stderr: str = "",
        mock_exit_code: int = 0,
    ) -> dict:
        repairs = self.storage.read_list(self.repairs_file)
        repair = next((r for r in repairs if r.get("repair_id") == repair_id), None)
        if repair is None:
            raise ValueError("Repair not found")
        command = repair.get("verify_command", "pytest")
        resolved_mode = "mock" if mode == "mock" else "run"
        result = self._resolve_result(command, resolved_mode, mock_stdout, mock_stderr, mock_exit_code)
        verification = {
            "command": result["command"],
            "exit_code": result["exit_code"],
            "success": result["success"],
            "blocked": result["blocked"],
            "verified_at": self._now(),
        }
        repair["verification"] = verification
        repair["status"] = "verified" if result["success"] else "verify_failed"
        repair["updated_at"] = self._now()
        self.storage.write_list(self.repairs_file, repairs)
        self._log("self_healing_repair_verified", f"Verified repair {repair_id}: {repair['status']}.")
        return repair

    def list_repairs(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.repairs_file)[-limit:]))

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self) -> dict:
        checks = self.storage.read_list(self.checks_file)
        findings = self.storage.read_list(self.findings_file)
        repairs = self.storage.read_list(self.repairs_file)
        return {
            "total_checks": len(checks),
            "failed_checks": sum(1 for c in checks if not c.get("success") and not c.get("blocked")),
            "blocked_checks": sum(1 for c in checks if c.get("blocked")),
            "open_findings": sum(1 for f in findings if f.get("status") == "open"),
            "total_findings": len(findings),
            "repair_drafts": sum(1 for r in repairs if r.get("status") == "draft"),
            "verified_repairs": sum(1 for r in repairs if r.get("status") == "verified"),
            "recent_findings": self.list_findings(limit=5),
            "auto_apply": False,
            "recommended_next_action": (
                "Run a build/test check to detect issues."
                if not checks
                else "Draft a repair task for an open finding, then verify after human approval."
            ),
        }
