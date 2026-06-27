from __future__ import annotations

PERMISSION_LEVELS = [
    "read_only",
    "plan_only",
    "approve_to_edit",
    "approve_to_run",
    "blocked",
]

ALLOWED_TOOL_TYPES = ["query", "analysis", "automation", "integration", "notification"]


class PluginSDKService:
    """EVO-321 Plugin Ecosystem SDK.

    Exposes a safe, declarative SDK/spec for building EvolveAgent plugins and a
    validator for plugin manifests. It never loads remote plugins, executes
    plugin code, or installs packages — it only describes the schema and checks
    that a submitted manifest conforms to it.
    """

    def sdk(self) -> dict:
        return {
            "sdk_version": "1.0",
            "manifest_schema": {
                "name": "string (required, 1-80 chars)",
                "version": "string (required, semver-like)",
                "description": "string (required, 1-500 chars)",
                "author": "string (optional)",
                "tool_type": f"string (optional, one of {ALLOWED_TOOL_TYPES})",
                "tools": "array (required, at least one tool)",
            },
            "tool_schema": {
                "name": "string (required)",
                "description": "string (required)",
                "permission_level": f"string (required, one of {PERMISSION_LEVELS})",
            },
            "permission_levels": PERMISSION_LEVELS,
            "allowed_tool_types": ALLOWED_TOOL_TYPES,
            "required_metadata": ["name", "version", "description", "tools"],
            "example_manifest": {
                "name": "summarizer-plugin",
                "version": "1.0.0",
                "description": "Summarizes workspace documents on request.",
                "author": "EvolveAgent Community",
                "tool_type": "analysis",
                "tools": [
                    {
                        "name": "summarize_document",
                        "description": "Return a concise summary of a provided document.",
                        "permission_level": "read_only",
                    },
                    {
                        "name": "apply_summary_note",
                        "description": "Attach a summary note to a workspace item.",
                        "permission_level": "approve_to_edit",
                    },
                ],
            },
            "safety_rules": [
                "Plugins are declarative manifests only; EvolveAgent OS does not execute plugin code.",
                "Every tool must declare a permission level; default to the least privilege needed.",
                "approve_to_edit and approve_to_run tools always require human approval before acting.",
                "blocked tools are documented but never executed.",
                "No plugin may request unrestricted shell, destructive file operations, or network exfiltration.",
            ],
        }

    def validate(self, manifest: dict | None) -> dict:
        errors: list[str] = []
        warnings: list[str] = []
        manifest = manifest or {}

        if not isinstance(manifest, dict):
            return {
                "valid": False,
                "errors": ["manifest must be an object"],
                "warnings": [],
                "normalized_manifest": {},
            }

        name = str(manifest.get("name", "")).strip()
        version = str(manifest.get("version", "")).strip()
        description = str(manifest.get("description", "")).strip()
        tools = manifest.get("tools")

        if not name:
            errors.append("name is required")
        elif len(name) > 80:
            errors.append("name must be 80 characters or fewer")
        if not version:
            errors.append("version is required")
        if not description:
            errors.append("description is required")
        elif len(description) > 500:
            errors.append("description must be 500 characters or fewer")

        normalized_tools: list[dict] = []
        if not isinstance(tools, list) or not tools:
            errors.append("tools must be a non-empty array")
        else:
            for index, tool in enumerate(tools):
                label = f"tools[{index}]"
                if not isinstance(tool, dict):
                    errors.append(f"{label} must be an object")
                    continue
                tool_name = str(tool.get("name", "")).strip()
                tool_desc = str(tool.get("description", "")).strip()
                permission = str(tool.get("permission_level", "")).strip()
                if not tool_name:
                    errors.append(f"{label}.name is required")
                if not tool_desc:
                    errors.append(f"{label}.description is required")
                if not permission:
                    errors.append(f"{label}.permission_level is required")
                elif permission not in PERMISSION_LEVELS:
                    errors.append(
                        f"{label}.permission_level '{permission}' is invalid; must be one of {PERMISSION_LEVELS}"
                    )
                normalized_tools.append(
                    {
                        "name": tool_name,
                        "description": tool_desc,
                        "permission_level": permission,
                    }
                )

        tool_type = str(manifest.get("tool_type", "")).strip()
        if tool_type and tool_type not in ALLOWED_TOOL_TYPES:
            warnings.append(
                f"tool_type '{tool_type}' is not a known type; expected one of {ALLOWED_TOOL_TYPES}"
            )
        if not str(manifest.get("author", "")).strip():
            warnings.append("author is recommended for plugin attribution")

        normalized_manifest: dict = {}
        if not errors:
            normalized_manifest = {
                "name": name,
                "version": version,
                "description": description,
                "author": str(manifest.get("author", "")).strip(),
                "tool_type": tool_type or "analysis",
                "tools": normalized_tools,
            }

        return {
            "valid": not errors,
            "errors": errors,
            "warnings": warnings,
            "normalized_manifest": normalized_manifest,
        }

    def summary(self) -> dict:
        sdk = self.sdk()
        return {
            "sdk_version": sdk["sdk_version"],
            "permission_levels": PERMISSION_LEVELS,
            "allowed_tool_types": ALLOWED_TOOL_TYPES,
            "required_metadata": sdk["required_metadata"],
            "safety_rules": sdk["safety_rules"],
        }
