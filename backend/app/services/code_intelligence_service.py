from __future__ import annotations

import re
from datetime import UTC, datetime

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Bug-risk heuristics: (regex, severity, message). Deterministic, static, read-only.
_RISK_PATTERNS = [
    (re.compile(r"\beval\s*\(|\bexec\s*\("), "high", "Use of eval/exec — avoid dynamic code execution."),
    (re.compile(r"except\s*:"), "medium", "Bare except — catch specific exceptions."),
    (re.compile(r"except\s+Exception\s*:(?!\s*#)"), "low", "Broad Exception catch — consider narrowing."),
    (re.compile(r"==\s*None|!=\s*None"), "low", "Compare to None with 'is' / 'is not'."),
    (re.compile(r"\bprint\s*\("), "low", "Leftover print() — use logging."),
    (re.compile(r"#\s*(TODO|FIXME|HACK|XXX)"), "low", "Unresolved TODO/FIXME marker."),
    (re.compile(r"\bpassword\b\s*=\s*['\"]|\bapi_key\b\s*=\s*['\"]|\bsecret\b\s*=\s*['\"]"), "high", "Hard-coded secret-like literal — move to env."),
    (re.compile(r"subprocess|os\.system|shell=True"), "high", "Shell/subprocess usage — validate and avoid shell=True."),
]

_IMPORT_RE = re.compile(r"^\s*(?:import\s+([a-zA-Z0-9_.]+)|from\s+([a-zA-Z0-9_.]+)\s+import)", re.MULTILINE)
_ROUTE_RE = re.compile(r"@router\.(get|post|patch|put|delete)\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
_DEF_RE = re.compile(r"^\s*(?:async\s+)?def\s+(\w+)", re.MULTILINE)
_TEST_RE = re.compile(r"^\s*def\s+(test_\w+)", re.MULTILINE)


class CodeIntelligenceService:
    """v76.0 Code Intelligence 2.0 — better code understanding without unsafe edits.

    A deterministic, read-only static analyzer that operates on **submitted code text**
    (it never reads the filesystem or edits code). It produces a **bug-risk scan**
    (eval/exec, bare except, hard-coded secrets, shell usage, TODOs, style), a
    **suggested refactor plan**, basic **complexity metrics**, an **API route map**
    (from FastAPI-style decorators), a **dependency list** (imports), and a **test
    coverage summary** (test-function count). Governance-logged.
    """

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="code_intelligence",
                agent_name="Code Intelligence",
                action_type=action_type,
                tool_used="CodeIntelligenceService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=1,
                reason=reason,
            )
        )

    def analyze(self, code: str, language: str = "python") -> dict:
        code = code or ""
        lines = code.splitlines()
        findings = []
        for pattern, severity, message in _RISK_PATTERNS:
            for match in pattern.finditer(code):
                line_no = code[:match.start()].count("\n") + 1
                findings.append({"severity": severity, "message": message, "line": line_no})
        findings.sort(key=lambda f: {"high": 0, "medium": 1, "low": 2}[f["severity"]])

        defs = _DEF_RE.findall(code)
        long_functions = self._long_functions(code)
        metrics = {
            "lines": len(lines),
            "functions": len(defs),
            "max_line_length": max((len(ln) for ln in lines), default=0),
            "long_functions": long_functions,
        }

        refactor_plan = self._refactor_plan(findings, metrics)
        risk_level = "high" if any(f["severity"] == "high" for f in findings) else "medium" if findings else "low"

        self._log("code_analyzed", f"Analyzed {len(lines)} lines of {language} — {len(findings)} risk finding(s).")
        return {
            "language": language,
            "risk_level": risk_level,
            "bug_risks": findings[:40],
            "risk_count": len(findings),
            "metrics": metrics,
            "suggested_refactors": refactor_plan,
            "note": "Static, deterministic analysis of submitted code — read-only, no edits, no filesystem access.",
        }

    @staticmethod
    def _long_functions(code: str) -> int:
        # Count functions whose body spans > 50 lines (rough, indentation-based).
        count = 0
        lines = code.splitlines()
        starts = [i for i, ln in enumerate(lines) if re.match(r"\s*(async\s+)?def\s+\w+", ln)]
        for idx, start in enumerate(starts):
            end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
            if end - start > 50:
                count += 1
        return count

    @staticmethod
    def _refactor_plan(findings: list[dict], metrics: dict) -> list[str]:
        plan = []
        if any(f["severity"] == "high" for f in findings):
            plan.append("Address high-severity findings first (eval/exec, hard-coded secrets, shell usage).")
        if metrics["long_functions"] > 0:
            plan.append(f"Split {metrics['long_functions']} long function(s) (>50 lines) into smaller units.")
        if metrics["max_line_length"] > 120:
            plan.append("Wrap long lines (>120 chars) for readability.")
        if any("except" in f["message"].lower() for f in findings):
            plan.append("Replace broad/bare excepts with specific exception handling.")
        if not plan:
            plan.append("No structural refactors indicated by static analysis.")
        return plan

    def route_map(self, code: str) -> dict:
        routes = [{"method": m.upper(), "path": p} for m, p in _ROUTE_RE.findall(code or "")]
        self._log("code_route_map", f"Extracted {len(routes)} route(s) from submitted code.")
        return {"routes": routes, "count": len(routes)}

    def dependencies(self, code: str) -> dict:
        modules = set()
        for imp, frm in _IMPORT_RE.findall(code or ""):
            name = (imp or frm).split(".")[0]
            if name:
                modules.add(name)
        deps = sorted(modules)
        self._log("code_dependencies", f"Extracted {len(deps)} top-level dependency/dependencies.")
        return {"dependencies": deps, "count": len(deps)}

    def test_coverage(self, code: str) -> dict:
        tests = _TEST_RE.findall(code or "")
        return {"test_count": len(tests), "tests": tests[:50], "note": "Counts test_ functions in submitted test code."}

    def analytics_summary(self) -> dict:
        return {"code_intel_risk_patterns": len(_RISK_PATTERNS)}

    def summary(self) -> dict:
        return {
            "capabilities": ["analyze", "route_map", "dependencies", "test_coverage"],
            "risk_patterns": len(_RISK_PATTERNS),
            "note": "Static, deterministic, read-only code analysis of submitted text — never reads the filesystem or edits code.",
        }
