from __future__ import annotations

import re
from datetime import UTC, datetime
from uuid import uuid4

from app.models.response_models import GovernanceEvent
from app.services.governance_service import GovernanceService
from app.services.secret_scanner import SecretScanner
from app.services.storage_service import StorageService

EXAMPLE_STATUSES = ["pending", "approved", "rejected"]

# Local PII patterns (redaction is local/heuristic; the existing SecretScanner
# handles secrets/API keys/passwords).
_PII_PATTERNS = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")),
    ("phone", re.compile(r"\b(?:\+?\d{1,2}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("credit_card", re.compile(r"\b(?:\d[ -]*?){13,16}\b")),
]


class TrainingLabService:
    """v27.0 Private Training Lab (dataset preparation only).

    Builds APPROVED, SANITIZED fine-tuning datasets. It does NOT train or
    fine-tune the base LLM automatically. Secrets (via SecretScanner) and PII
    (via local patterns) are redacted before an example is stored; only approved
    examples are exportable. Training runs are mock metadata records. Every
    stateful action is governance-logged.
    """

    datasets_file = "training_datasets.json"
    examples_file = "training_examples.json"
    exports_file = "training_exports.json"
    runs_file = "training_runs.json"
    comparisons_file = "training_comparisons.json"

    def __init__(self, storage: StorageService, governance_service: GovernanceService, secret_scanner: SecretScanner | None = None):
        self.storage = storage
        self.governance = governance_service
        self.secret_scanner = secret_scanner or SecretScanner()

    def _now(self) -> str:
        return datetime.now(UTC).isoformat()

    def _clean(self, value, max_length: int, default: str = "") -> str:
        return str(value if value is not None else default).strip()[:max_length]

    def _log(self, action_type: str, reason: str) -> None:
        self.governance.log_event(
            GovernanceEvent(
                task_type="training_lab",
                agent_name="Private Training Lab",
                action_type=action_type,
                tool_used="TrainingLabService",
                permission_level="read_only",
                approved=True,
                blocked=False,
                risk_score=5,
                reason=reason,
            )
        )

    # ------------------------------------------------------------------
    # Redaction
    # ------------------------------------------------------------------
    def _sanitize(self, text: str) -> dict:
        redacted_secrets, secret_result = self.secret_scanner.redact(text or "")
        pii_types: list[str] = []
        pii_count = 0
        redacted = redacted_secrets
        for label, pattern in _PII_PATTERNS:
            matches = pattern.findall(redacted)
            if matches:
                pii_types.append(label)
                pii_count += len(matches)
                redacted = pattern.sub(f"[REDACTED_{label.upper()}]", redacted)
        return {
            "redacted_text": redacted,
            "secrets_detected": secret_result.secrets_detected,
            "secret_types": secret_result.detected_types,
            "secret_redaction_count": secret_result.redaction_count,
            "pii_detected": pii_count > 0,
            "pii_types": pii_types,
            "pii_redaction_count": pii_count,
        }

    # ------------------------------------------------------------------
    # Datasets
    # ------------------------------------------------------------------
    def list_datasets(self) -> list[dict]:
        return self.storage.read_list(self.datasets_file)

    def get_dataset(self, dataset_id: str) -> dict | None:
        return next((d for d in self.storage.read_list(self.datasets_file) if d.get("dataset_id") == dataset_id), None)

    def create_dataset(self, data: dict) -> dict:
        dataset = {
            "dataset_id": str(uuid4()),
            "name": self._clean(data.get("name"), 160) or "Training dataset",
            "description": self._clean(data.get("description"), 2000),
            "purpose": self._clean(data.get("purpose"), 200) or "fine_tuning_preparation",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.datasets_file, dataset)
        self._log("training_dataset_created", f"Created training dataset: {dataset['name']}.")
        return dataset

    # ------------------------------------------------------------------
    # Examples
    # ------------------------------------------------------------------
    def add_example(self, dataset_id: str, prompt: str, completion: str, approved: bool = False) -> dict:
        dataset = self.get_dataset(dataset_id)
        if dataset is None:
            raise ValueError("Dataset not found")
        prompt_scan = self._sanitize(prompt or "")
        completion_scan = self._sanitize(completion or "")
        example = {
            "example_id": str(uuid4()),
            "dataset_id": dataset_id,
            # Only the redacted/sanitized text is ever stored.
            "prompt": prompt_scan["redacted_text"],
            "completion": completion_scan["redacted_text"],
            "redaction": {
                "secrets_detected": prompt_scan["secrets_detected"] or completion_scan["secrets_detected"],
                "pii_detected": prompt_scan["pii_detected"] or completion_scan["pii_detected"],
                "secret_types": sorted(set(prompt_scan["secret_types"]) | set(completion_scan["secret_types"])),
                "pii_types": sorted(set(prompt_scan["pii_types"]) | set(completion_scan["pii_types"])),
                "total_redactions": (
                    prompt_scan["secret_redaction_count"]
                    + completion_scan["secret_redaction_count"]
                    + prompt_scan["pii_redaction_count"]
                    + completion_scan["pii_redaction_count"]
                ),
            },
            "status": "approved" if approved else "pending",
            "created_at": self._now(),
            "updated_at": self._now(),
        }
        self.storage.append(self.examples_file, example)
        self._log("training_example_added", f"Added example to dataset {dataset_id} (redactions: {example['redaction']['total_redactions']}).")
        return example

    def list_examples(self, dataset_id: str | None = None) -> list[dict]:
        examples = self.storage.read_list(self.examples_file)
        if dataset_id:
            return [e for e in examples if e.get("dataset_id") == dataset_id]
        return examples

    def update_example(self, example_id: str, updates: dict) -> dict:
        examples = self.storage.read_list(self.examples_file)
        example = next((e for e in examples if e.get("example_id") == example_id), None)
        if example is None:
            raise ValueError("Example not found")
        if updates.get("status") in EXAMPLE_STATUSES:
            example["status"] = updates["status"]
        # Editing text re-runs sanitization so nothing unsafe slips in.
        if updates.get("prompt") is not None:
            example["prompt"] = self._sanitize(updates["prompt"])["redacted_text"]
        if updates.get("completion") is not None:
            example["completion"] = self._sanitize(updates["completion"])["redacted_text"]
        example["updated_at"] = self._now()
        self.storage.write_list(self.examples_file, examples)
        self._log("training_example_updated", f"Updated example {example_id} → {example['status']}.")
        return example

    # ------------------------------------------------------------------
    # Export (approved-only, JSONL-style)
    # ------------------------------------------------------------------
    def export_dataset(self, dataset_id: str) -> dict:
        dataset = self.get_dataset(dataset_id)
        if dataset is None:
            raise ValueError("Dataset not found")
        approved = [e for e in self.list_examples(dataset_id) if e.get("status") == "approved"]
        lines = [
            {"messages": [{"role": "user", "content": e["prompt"]}, {"role": "assistant", "content": e["completion"]}]}
            for e in approved
        ]
        export = {
            "export_id": str(uuid4()),
            "dataset_id": dataset_id,
            "format": "jsonl_chat",
            "approved_example_count": len(approved),
            "excluded_non_approved": len(self.list_examples(dataset_id)) - len(approved),
            "jsonl_lines": lines,
            "safety_note": "Approved + sanitized examples only. Secrets and PII were redacted before inclusion. Not used to auto-train the base model.",
            "created_at": self._now(),
        }
        self.storage.append(self.exports_file, export)
        self._log("training_dataset_exported", f"Exported {len(approved)} approved example(s) from dataset {dataset_id}.")
        return export

    def lora_checklist(self, dataset_id: str | None = None) -> list[str]:
        return [
            "Confirm all included examples are status=approved.",
            "Confirm secret/PII redaction passed on every example.",
            "Choose a small open base model and a LoRA rank/alpha locally.",
            "Run LoRA training locally/offline — the app does not train automatically.",
            "Evaluate the candidate adapter against a baseline before any use.",
        ]

    # ------------------------------------------------------------------
    # Mock training runs + comparisons
    # ------------------------------------------------------------------
    def create_run(self, data: dict) -> dict:
        run = {
            "run_id": str(uuid4()),
            "dataset_id": self._clean(data.get("dataset_id"), 120) or None,
            "base_model": self._clean(data.get("base_model"), 120) or "open-base-model (mock)",
            "method": self._clean(data.get("method"), 60) or "lora",
            "status": "mock_prepared",
            "lora_checklist": self.lora_checklist(),
            "note": "Mock run record — no real training was executed by the app.",
            "created_at": self._now(),
        }
        self.storage.append(self.runs_file, run)
        self._log("training_run_created", f"Created mock training run {run['run_id']}.")
        return run

    def list_runs(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.runs_file)[-limit:]))

    def create_comparison(self, data: dict) -> dict:
        comparison = {
            "comparison_id": str(uuid4()),
            "baseline_model": self._clean(data.get("baseline_model"), 120) or "baseline (mock)",
            "candidate_model": self._clean(data.get("candidate_model"), 120) or "candidate (mock)",
            "metric": self._clean(data.get("metric"), 80) or "win_rate",
            "baseline_score": float(data.get("baseline_score") or 0),
            "candidate_score": float(data.get("candidate_score") or 0),
            "verdict": "candidate_better"
            if float(data.get("candidate_score") or 0) > float(data.get("baseline_score") or 0)
            else "baseline_better_or_equal",
            "note": "Mock metadata comparison only.",
            "created_at": self._now(),
        }
        self.storage.append(self.comparisons_file, comparison)
        self._log("training_comparison_created", f"Created model comparison {comparison['comparison_id']}.")
        return comparison

    def list_comparisons(self, limit: int = 25) -> list[dict]:
        return list(reversed(self.storage.read_list(self.comparisons_file)[-limit:]))

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    def dashboard(self) -> dict:
        datasets = self.storage.read_list(self.datasets_file)
        examples = self.storage.read_list(self.examples_file)
        return {
            "total_datasets": len(datasets),
            "total_examples": len(examples),
            "approved_examples": sum(1 for e in examples if e.get("status") == "approved"),
            "rejected_examples": sum(1 for e in examples if e.get("status") == "rejected"),
            "pending_examples": sum(1 for e in examples if e.get("status") == "pending"),
            "examples_with_redactions": sum(1 for e in examples if (e.get("redaction") or {}).get("total_redactions", 0) > 0),
            "total_exports": len(self.storage.read_list(self.exports_file)),
            "total_runs": len(self.storage.read_list(self.runs_file)),
            "total_comparisons": len(self.storage.read_list(self.comparisons_file)),
            "safety_notes": [
                "The app does not train or fine-tune the base LLM automatically.",
                "Only approved and sanitized data is exportable.",
                "Secrets/PII are redacted before export.",
            ],
        }
