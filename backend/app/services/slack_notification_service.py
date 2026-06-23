from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import httpx

from app.config import settings
from app.models.response_models import GovernanceEvent, RunResponse
from app.services.governance_service import GovernanceService
from app.services.secret_scanner import SecretScanner
from app.services.storage_service import StorageService


class SlackNotificationService:
    filename = "slack_notifications.json"

    def __init__(
        self,
        storage: StorageService,
        governance: GovernanceService,
        secret_scanner: SecretScanner | None = None,
    ):
        self.storage = storage
        self.governance = governance
        self.secret_scanner = secret_scanner or SecretScanner()

    def status(self) -> dict[str, Any]:
        return {
            "enabled": settings.slack_notifications_enabled,
            "configured": bool(settings.slack_webhook_url),
            "default_channel_set": bool(settings.slack_default_channel),
            "recent_notifications": self.list_notifications(limit=10),
        }

    def list_notifications(self, limit: int = 50) -> list[dict[str, Any]]:
        return list(reversed(self.storage.read_list(self.filename)[-limit:]))

    def notify_run_completed(self, response: RunResponse, channel: str | None = None) -> dict[str, Any]:
        summary = self._summarize_run(response)
        text = (
            f"EvolveAgent AI run completed: {response.task_type} "
            f"(score {response.judge_result.overall_score}, run {response.run_id[:8]})."
        )
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*EvolveAgent AI run completed*\n"
                        f"*Task:* `{response.task_type}`\n"
                        f"*Score:* {response.judge_result.overall_score}\n"
                        f"*Run:* `{response.run_id}`"
                    ),
                },
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": summary}},
        ]
        return self.send_message(
            text=text,
            event_type="run_completed",
            channel=channel,
            blocks=blocks,
            run_id=response.run_id,
            session_id=response.session_id,
            workspace_id=response.workspace_id,
            task_type=response.task_type,
        )

    def send_test_message(
        self,
        text: str = "EvolveAgent AI Slack notification test.",
        channel: str | None = None,
        workspace_id: str | None = None,
    ) -> dict[str, Any]:
        return self.send_message(
            text=text,
            event_type="test_notification",
            channel=channel,
            workspace_id=workspace_id,
            task_type="integration_test",
        )

    def send_message(
        self,
        *,
        text: str,
        event_type: str,
        channel: str | None = None,
        blocks: list[dict[str, Any]] | None = None,
        run_id: str | None = None,
        session_id: str | None = None,
        workspace_id: str | None = None,
        task_type: str | None = None,
    ) -> dict[str, Any]:
        safe_text, secret_scan = self.secret_scanner.redact(text)
        payload: dict[str, Any] = {"text": safe_text}
        selected_channel = channel or settings.slack_default_channel
        if selected_channel:
            payload["channel"] = selected_channel
        if blocks:
            safe_blocks, block_scan = self.secret_scanner.redact(json.dumps(blocks))
            secret_scan = secret_scan.model_copy(
                update={
                    "redaction_count": secret_scan.redaction_count + block_scan.redaction_count,
                    "secrets_detected": secret_scan.secrets_detected or block_scan.secrets_detected,
                    "detected_types": sorted(set(secret_scan.detected_types + block_scan.detected_types)),
                    "status": "redacted" if (secret_scan.secrets_detected or block_scan.secrets_detected) else secret_scan.status,
                }
            )
            payload["blocks"] = json.loads(safe_blocks)

        base_record = {
            "notification_id": str(uuid4()),
            "event_type": event_type,
            "run_id": run_id,
            "session_id": session_id,
            "workspace_id": workspace_id,
            "task_type": task_type,
            "channel": selected_channel,
            "enabled": settings.slack_notifications_enabled,
            "configured": bool(settings.slack_webhook_url),
            "redaction_count": secret_scan.redaction_count,
            "created_at": datetime.now(UTC).isoformat(),
        }

        if not settings.slack_notifications_enabled:
            return {**base_record, "sent": False, "skipped": True, "reason": "Slack notifications are disabled."}

        if not settings.slack_webhook_url:
            record = {**base_record, "sent": False, "skipped": True, "reason": "Slack webhook URL is not configured."}
            self._persist(record)
            self._log_governance(record)
            return record

        try:
            response = httpx.post(settings.slack_webhook_url, json=payload, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            record = {**base_record, "sent": False, "skipped": False, "error": str(exc)}
            self._persist(record)
            self._log_governance(record, blocked=True)
            return record

        record = {**base_record, "sent": True, "skipped": False, "status_code": response.status_code}
        self._persist(record)
        self._log_governance(record)
        return record

    def _persist(self, record: dict[str, Any]) -> None:
        self.storage.append(self.filename, record)

    def _log_governance(self, record: dict[str, Any], blocked: bool = False) -> None:
        self.governance.log_event(
            GovernanceEvent(
                run_id=record.get("run_id"),
                session_id=record.get("session_id"),
                workspace_id=record.get("workspace_id"),
                task_type=record.get("task_type"),
                agent_name="Slack Notification Service",
                action_type="slack_notification",
                tool_used="SlackNotificationService",
                permission_level="read_only",
                approved=False,
                blocked=blocked,
                risk_score=35 if blocked else 5,
                reason=record.get("error") or record.get("reason") or "Slack notification processed.",
            )
        )

    @staticmethod
    def _summarize_run(response: RunResponse) -> str:
        clean = " ".join(response.final_output.split())
        if len(clean) > 600:
            clean = f"{clean[:597]}..."
        return clean or "Run completed without a text summary."
