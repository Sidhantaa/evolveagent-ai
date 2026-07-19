from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.governance_service import GovernanceService
from app.services.storage_retention_service import StorageRetentionService
from app.services.storage_service import StorageService

client = TestClient(app)


def _isolated(tmp_path) -> tuple[StorageService, StorageRetentionService]:
    storage = StorageService(data_dir=str(tmp_path / "data"))
    return storage, StorageRetentionService(storage, GovernanceService(storage))


def _iso(days_ago: int) -> str:
    return (datetime.now(UTC) - timedelta(days=days_ago)).isoformat()


def test_prunable_collections_lists_only_the_scoped_five(tmp_path):
    _, retention = _isolated(tmp_path)
    result = retention.prunable_collections()
    assert set(result["collections"]) == {
        "governance_log.json", "chat_sessions.json", "messages.json", "tasks.json", "audit_packages.json",
    }


def test_preview_never_writes_anything(tmp_path):
    storage, retention = _isolated(tmp_path)
    storage.write_list("governance_log.json", [
        {"event_id": "old", "created_at": _iso(100)},
        {"event_id": "new", "created_at": _iso(1)},
    ])

    preview = retention.preview("governance_log.json", older_than_days=90)

    assert preview["dry_run"] is True
    assert preview["total_records"] == 2
    assert preview["records_to_prune"] == 1
    assert preview["records_to_keep"] == 1
    # nothing was actually removed
    assert len(storage.read_list("governance_log.json")) == 2


def test_prune_removes_only_records_older_than_the_cutoff(tmp_path):
    storage, retention = _isolated(tmp_path)
    storage.write_list("governance_log.json", [
        {"event_id": "very-old", "created_at": _iso(200)},
        {"event_id": "old", "created_at": _iso(100)},
        {"event_id": "recent", "created_at": _iso(5)},
    ])

    result = retention.prune("governance_log.json", older_than_days=90)

    assert result["dry_run"] is False
    assert result["pruned_count"] == 2
    assert result["remaining_count"] == 1  # computed inside update_list(), before the action's own log entry lands
    # prune() logs its own action into governance_log.json (the same collection),
    # so read_list() afterward also picks up that fresh "storage_pruned" entry --
    # filter to the original test-seeded records by event_id.
    remaining = [item for item in storage.read_list("governance_log.json") if item.get("event_id") in {"very-old", "old", "recent"}]
    assert [item["event_id"] for item in remaining] == ["recent"]


def test_prune_archives_pruned_records_before_removing_them(tmp_path):
    import json
    import os

    storage, retention = _isolated(tmp_path)
    storage.write_list("governance_log.json", [{"event_id": "old-1", "created_at": _iso(200)}])

    result = retention.prune("governance_log.json", older_than_days=90)

    assert result["archive_path"] is not None
    assert os.path.exists(result["archive_path"])
    with open(result["archive_path"]) as file:
        archived = json.load(file)
    assert len(archived) == 1
    assert archived[0]["event_id"] == "old-1"


def test_prune_with_nothing_to_prune_writes_no_archive(tmp_path):
    storage, retention = _isolated(tmp_path)
    storage.write_list("governance_log.json", [{"event_id": "recent", "created_at": _iso(1)}])

    result = retention.prune("governance_log.json", older_than_days=90)

    assert result["pruned_count"] == 0
    assert result["archive_path"] is None


def test_prune_never_removes_a_record_with_a_missing_timestamp(tmp_path):
    """Fail safe: a record with no/malformed timestamp is never eligible for
    pruning, even if it would otherwise be very old by position."""
    storage, retention = _isolated(tmp_path)
    storage.write_list("governance_log.json", [
        {"event_id": "no-timestamp"},
        {"event_id": "old", "created_at": _iso(200)},
    ])

    result = retention.prune("governance_log.json", older_than_days=90)

    assert result["pruned_count"] == 1
    # prune() logs its own action into this same collection -- filter to the
    # original test-seeded records (which have no action_type field).
    remaining_ids = {item["event_id"] for item in storage.read_list("governance_log.json") if "action_type" not in item}
    assert remaining_ids == {"no-timestamp"}


def test_prune_uses_the_correct_timestamp_field_per_collection(tmp_path):
    """audit_packages.json uses generated_at, not created_at -- confirm the
    per-collection field mapping is actually applied, not a uniform assumption."""
    storage, retention = _isolated(tmp_path)
    storage.write_list("audit_packages.json", [
        {"package_id": "old", "generated_at": _iso(200)},
        {"package_id": "recent", "generated_at": _iso(1)},
    ])

    result = retention.prune("audit_packages.json", older_than_days=90)

    assert result["pruned_count"] == 1
    remaining = storage.read_list("audit_packages.json")
    assert [item["package_id"] for item in remaining] == ["recent"]


def test_unknown_collection_is_rejected(tmp_path):
    _, retention = _isolated(tmp_path)
    with pytest.raises(ValueError, match="not a prunable collection"):
        retention.preview("some_random_file.json", older_than_days=90)


def test_older_than_days_below_the_floor_is_rejected(tmp_path):
    _, retention = _isolated(tmp_path)
    with pytest.raises(ValueError, match="older_than_days must be"):
        retention.preview("governance_log.json", older_than_days=0)


def test_prune_is_logged_to_governance(tmp_path):
    storage, retention = _isolated(tmp_path)
    storage.write_list("governance_log.json", [{"event_id": "old", "created_at": _iso(200)}])

    retention.prune("governance_log.json", older_than_days=90)

    events = storage.read_list("governance_log.json")  # the prune's own log entry lands in the same file
    assert any(e.get("action_type") == "storage_pruned" for e in events)


# ------------------------------------------------------------------
# Routes -- dry_run defaults to True, so an accidental call never deletes.
# ------------------------------------------------------------------
def test_prune_endpoint_defaults_to_dry_run():
    r = client.post("/api/system/storage-prune", json={"collection": "governance_log.json", "older_than_days": 90}).json()
    assert r["dry_run"] is True


def test_prune_endpoint_explicit_dry_run_false_routes_to_the_real_prune_path():
    # 3650-day cutoff against real, recent dev data prunes nothing -- this
    # only proves the endpoint calls prune() (dry_run: false in the
    # response) rather than preview(), not that real deletion happened
    # (that's covered by the isolated service-level tests above).
    r = client.post(
        "/api/system/storage-prune",
        json={"collection": "governance_log.json", "older_than_days": 3650, "dry_run": False},
    ).json()
    assert r["dry_run"] is False
    assert "pruned_count" in r  # prune()'s response shape, not preview()'s


def test_prune_endpoint_rejects_an_unknown_collection():
    r = client.post("/api/system/storage-prune", json={"collection": "not_a_real_file.json", "older_than_days": 90})
    assert r.status_code == 400


def test_prunable_collections_endpoint():
    r = client.get("/api/system/storage-prune/collections").json()
    assert "governance_log.json" in r["collections"]
