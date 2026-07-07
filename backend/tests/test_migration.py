"""JSON -> Postgres migration tests.

Dry-run works without a DB. The real migrate/verify tests require Postgres and
**skip** without TEST_DATABASE_URL (CI provides it). Each run uses a fresh temp
JSON dir; collections are unique to stay isolated in the shared DB.
"""

import json
import os
import uuid

import pytest

from app.storage.migrate import migrate_json_to_postgres, collections

TEST_DB = os.environ.get("TEST_DATABASE_URL")


def _seed(tmp_path, mapping):
    for name, items in mapping.items():
        (tmp_path / name).write_text(json.dumps(items))


def test_dry_run_needs_no_database(tmp_path):
    _seed(tmp_path, {"a.json": [{"x": 1}, {"x": 2}], "b.json": [{"y": 1}]})
    rep = migrate_json_to_postgres(str(tmp_path), None, dry_run=True)
    assert rep["mode"] == "dry_run"
    assert rep["collections"] == 2
    assert rep["total_documents"] == 3
    assert {r["collection"] for r in rep["rows"]} == {"a.json", "b.json"}


def test_migrate_requires_url_when_not_dry_run(tmp_path):
    with pytest.raises(ValueError):
        migrate_json_to_postgres(str(tmp_path), None, dry_run=False)


def test_collections_lists_json_files(tmp_path):
    _seed(tmp_path, {"z.json": [], "a.json": []})
    (tmp_path / "notjson.txt").write_text("x")
    assert collections(str(tmp_path)) == ["a.json", "z.json"]


@pytest.mark.skipif(not TEST_DB, reason="TEST_DATABASE_URL not set")
def test_migrate_then_verify_roundtrip(tmp_path):
    u = uuid.uuid4().hex
    c1, c2 = f"mig_{u}_a.json", f"mig_{u}_b.json"
    _seed(tmp_path, {c1: [{"n": 1}, {"n": 2}, {"n": 3}], c2: [{"m": 9}]})

    mig = migrate_json_to_postgres(str(tmp_path), TEST_DB)
    assert mig["mode"] == "migrate" and mig["total_documents"] == 4

    ver = migrate_json_to_postgres(str(tmp_path), TEST_DB, verify=True)
    assert ver["all_match"] is True
    by = {r["collection"]: r for r in ver["rows"]}
    assert by[c1]["json"] == by[c1]["postgres"] == 3
    assert by[c2]["json"] == by[c2]["postgres"] == 1

    # idempotent: migrating again keeps counts identical
    migrate_json_to_postgres(str(tmp_path), TEST_DB)
    ver2 = migrate_json_to_postgres(str(tmp_path), TEST_DB, verify=True)
    assert ver2["all_match"] is True
    assert {r["collection"]: r["postgres"] for r in ver2["rows"]}[c1] == 3
