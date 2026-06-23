from datetime import UTC, datetime, timedelta

from app.services.compliance_service import ComplianceService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


def build_service(tmp_path):
    storage = StorageService(data_dir=str(tmp_path))
    governance = GovernanceService(storage)
    return storage, governance, ComplianceService(storage, governance)


def test_pii_scan_redacts_common_patterns(tmp_path):
    _, _, service = build_service(tmp_path)

    result = service.scan_pii("Email me at person@example.com or call 555-123-4567.")

    assert result["pii_detected"] is True
    assert result["redaction_count"] == 2
    assert "email" in result["detected_types"]
    assert "phone" in result["detected_types"]
    assert "person@example.com" not in result["redacted_text"]


def test_retention_review_is_review_only(tmp_path):
    storage, _, service = build_service(tmp_path)
    old_date = (datetime.now(UTC) - timedelta(days=500)).isoformat()
    storage.append("messages.json", {"message_id": "old", "content": "old message", "created_at": old_date})

    review = service.retention_review()

    messages = next(item for item in review["reviews"] if item["collection"] == "messages.json")
    assert review["review_only"] is True
    assert messages["records_needing_review"] == 1
    assert storage.read_list("messages.json")[0]["message_id"] == "old"


def test_compliance_report_contains_audit_and_pii_summary(tmp_path):
    storage, governance, service = build_service(tmp_path)
    storage.append("workspace_memory.json", {"memory_id": "mem", "content": "Contact a@b.com"})
    governance.log_event(
        {
            "action_type": "blocked_test",
            "blocked": True,
            "risk_score": 80,
            "reason": "test",
        }
    )

    report = service.compliance_report()

    assert report["summary"]["blocked_actions"] == 1
    assert report["summary"]["high_risk_events"] == 1
    assert report["summary"]["pii_findings"] >= 1
    assert report["admin"]["admin_recommendations"]

