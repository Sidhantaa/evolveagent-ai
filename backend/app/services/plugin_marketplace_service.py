from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

# Declarable permissions and their risk weight.
PERMISSION_RISK = {"read": 0, "memory_read": 0, "analyze": 0, "network": 2, "write": 2, "execute": 3, "shell": 3}
_HIGH_RISK = {"execute", "shell", "network", "write"}


class PluginMarketplaceService:
    """v86.0 Plugin Marketplace 3.0 — make plugins safer and easier.

    A local plugin **catalog** with **validation** (required fields + declared
    permissions), a **permission review** (flags high-risk permissions), **enable /
    disable** toggles, a **plugin activity log**, a **plugin test runner** (dry / mock —
    nothing executed), and a **plugin health score**. It is additive and separate from
    the core plugin-manifest loader (dedicated ``marketplace_plugins`` collection);
    high-risk permissions keep a plugin disabled until explicitly enabled. Registration
    and toggles are governance-logged; the test runner never executes real code.
    """

    plugins_file = "marketplace_plugins.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService):
        self.storage = storage
        self.governance = governance_service

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _log(self, action_type: str, reason: str, blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="plugin_marketplace",
                agent_name="Plugin Marketplace",
                action_type=action_type,
                tool_used="PluginMarketplaceService",
                permission_level="read_only",
                approved=not blocked,
                blocked=blocked,
                risk_score=2,
                reason=reason,
            )
        )

    @staticmethod
    def _validate(name: str, permissions: list[str]) -> dict:
        errors = []
        if not name.strip():
            errors.append("Plugin name is required.")
        unknown = [p for p in permissions if p not in PERMISSION_RISK]
        if unknown:
            errors.append(f"Unknown permission(s): {', '.join(unknown)}.")
        high_risk = [p for p in permissions if p in _HIGH_RISK]
        return {"valid": not errors, "errors": errors, "high_risk_permissions": high_risk}

    @staticmethod
    def _health(plugin: dict) -> dict:
        validation = plugin.get("validation", {})
        risk = sum(PERMISSION_RISK.get(p, 0) for p in plugin.get("permissions", []))
        score = 100
        if not validation.get("valid"):
            score -= 50
        score -= min(risk * 8, 40)
        if not plugin.get("enabled"):
            score -= 5
        score = max(score, 0)
        return {"score": score, "status": "healthy" if score >= 70 else "review" if score >= 40 else "risky"}

    def register(self, name: str, description: str, permissions: list[str]) -> dict:
        permissions = [p for p in (permissions or []) if isinstance(p, str)][:12]
        validation = self._validate(name, permissions)
        plugin = {
            "plugin_id": str(uuid4()),
            "name": name[:120],
            "description": (description or "")[:1000],
            "permissions": permissions,
            "validation": validation,
            # High-risk plugins stay disabled until explicitly enabled.
            "enabled": validation["valid"] and not validation["high_risk_permissions"],
            "created_at": self._now(),
        }
        self.storage.append(self.plugins_file, plugin)
        self._log("plugin_registered", f"Registered plugin '{name}' (valid={validation['valid']}, high-risk={bool(validation['high_risk_permissions'])}).")
        return {**plugin, "health": self._health(plugin)}

    def catalog(self) -> dict:
        plugins = self.storage.read_list(self.plugins_file)
        return {"plugins": [{**p, "health": self._health(p)} for p in plugins], "count": len(plugins)}

    def toggle(self, plugin_id: str, enabled: bool) -> dict:
        plugins = self.storage.read_list(self.plugins_file)
        target = next((p for p in plugins if p.get("plugin_id") == plugin_id), None)
        if target is None:
            raise ValueError("Plugin not found")
        if enabled and (not target.get("validation", {}).get("valid") or target.get("validation", {}).get("high_risk_permissions")):
            self._log("plugin_enable_blocked", f"Blocked enabling high-risk/invalid plugin '{target['name']}'.", blocked=True)
            return {"plugin_id": plugin_id, "enabled": False,
                    "blocked": True, "reason": "High-risk or invalid plugins require review before enabling."}
        target["enabled"] = bool(enabled)
        target["updated_at"] = self._now()
        self.storage.write_list(self.plugins_file, plugins)
        self._log("plugin_toggled", f"{'Enabled' if enabled else 'Disabled'} plugin '{target['name']}'.")
        return {"plugin_id": plugin_id, "enabled": target["enabled"], "blocked": False}

    def test_run(self, plugin_id: str) -> dict:
        plugins = self.storage.read_list(self.plugins_file)
        target = next((p for p in plugins if p.get("plugin_id") == plugin_id), None)
        if target is None:
            raise ValueError("Plugin not found")
        self._log("plugin_test_run", f"Dry test-run of plugin '{target['name']}' (mock).")
        return {
            "plugin_id": plugin_id,
            "name": target["name"],
            "result": "dry_ok" if target.get("validation", {}).get("valid") else "validation_failed",
            "would_use_permissions": target.get("permissions", []),
            "note": "Mock/dry test — nothing is executed; validates structure and declared permissions only.",
        }

    def activity_log(self, limit: int = 20) -> dict:
        events = [e for e in self.storage.read_list("governance_log.json")
                  if isinstance(e, dict) and e.get("task_type") == "plugin_marketplace"]
        return {"events": [{"action": e.get("action_type"), "reason": e.get("reason"), "at": e.get("created_at")} for e in list(reversed(events))[:limit]],
                "count": len(events)}

    def analytics_summary(self) -> dict:
        plugins = self.storage.read_list(self.plugins_file)
        return {"marketplace_plugins": len(plugins), "marketplace_plugins_enabled": sum(1 for p in plugins if p.get("enabled"))}

    def summary(self) -> dict:
        plugins = self.storage.read_list(self.plugins_file)
        return {
            "total_plugins": len(plugins),
            "enabled": sum(1 for p in plugins if p.get("enabled")),
            "permissions": list(PERMISSION_RISK.keys()),
            "note": "Additive to core plugin loader; high-risk plugins stay disabled until reviewed; test runner is mock.",
        }
