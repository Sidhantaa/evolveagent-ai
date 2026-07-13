"""Capability Directory -- the "feature/control center" the v200 strategy
doc's Current Execution Priority #2 asks for. Every classification reads a
real field from an already-existing status() method; these tests cover both
the pure classification helpers and the full app wiring."""

from fastapi.testclient import TestClient

from app.main import app
from app.services.capability_directory_service import (
    CapabilityDirectoryService,
    STATUS_LOCAL,
    STATUS_MOCK,
    STATUS_NEEDS_CONFIG,
    STATUS_REAL,
    STATUS_UNKNOWN,
    classify_available,
    classify_key_gated_per_call,
    classify_mode_string,
    classify_optin_global,
    classify_static,
)
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService

client = TestClient(app)


# ------------------------------------------------------------------
# Pure classification helpers
# ------------------------------------------------------------------
def test_classify_optin_global_real_when_enabled():
    assert classify_optin_global({"enabled": True}, "enabled")["status"] == STATUS_REAL


def test_classify_optin_global_mock_when_disabled():
    assert classify_optin_global({"enabled": False}, "enabled")["status"] == STATUS_MOCK


def test_classify_optin_global_needs_config_when_not_configured():
    result = classify_optin_global({"enabled": True, "configured": False}, "enabled", "configured")
    assert result["status"] == STATUS_NEEDS_CONFIG


def test_classify_key_gated_per_call():
    assert classify_key_gated_per_call({"key_configured": True}, "key_configured")["status"] == STATUS_REAL
    assert classify_key_gated_per_call({"key_configured": False}, "key_configured")["status"] == STATUS_NEEDS_CONFIG


def test_classify_mode_string():
    assert classify_mode_string({"mode": "mock"}, "mode", {"real"}, "configured")["status"] == STATUS_MOCK
    assert classify_mode_string({"mode": "real", "configured": True}, "mode", {"real"}, "configured")["status"] == STATUS_REAL
    assert classify_mode_string({"mode": "real", "configured": False}, "mode", {"real"}, "configured")["status"] == STATUS_NEEDS_CONFIG


def test_classify_available():
    assert classify_available({"available": True})["status"] == STATUS_REAL
    assert classify_available({"available": True}, real_status=STATUS_LOCAL)["status"] == STATUS_LOCAL
    assert classify_available({"available": False})["status"] == "blocked"


def test_classify_static():
    result = classify_static(STATUS_LOCAL, "always local")
    assert result == {"status": STATUS_LOCAL, "detail": "always local"}


# ------------------------------------------------------------------
# Service-level: isolated, using a fake registry (no dependency on the app's
# real ~20 services).
# ------------------------------------------------------------------
def _isolated_service(tmp_path, capabilities):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    return CapabilityDirectoryService(storage, GovernanceService(storage), capabilities)


def test_list_capabilities_normalizes_and_sorts(tmp_path):
    caps = [
        {"name": "Zeta", "category": "B", "route": "/api/zeta", "safety_level": "read_only", "tool_used": None,
         "classify": lambda: {"status": STATUS_REAL, "detail": "ok"}},
        {"name": "Alpha", "category": "A", "route": "/api/alpha", "safety_level": "read_only", "tool_used": None,
         "classify": lambda: {"status": STATUS_MOCK, "detail": "off"}},
    ]
    service = _isolated_service(tmp_path, caps)
    entries = service.list_capabilities()
    assert [e["name"] for e in entries] == ["Alpha", "Zeta"]  # sorted by (category, name)
    assert entries[0]["status"] == STATUS_MOCK
    assert entries[1]["status"] == STATUS_REAL


def test_broken_classify_degrades_to_unknown_not_a_crash(tmp_path):
    def _boom():
        raise RuntimeError("underlying status() failed")
    caps = [{"name": "Broken", "category": "A", "route": "/api/broken", "safety_level": "read_only",
             "tool_used": None, "classify": _boom}]
    service = _isolated_service(tmp_path, caps)
    entries = service.list_capabilities()
    assert entries[0]["status"] == STATUS_UNKNOWN
    assert "RuntimeError" in entries[0]["detail"]


def test_filter_by_category_and_status(tmp_path):
    caps = [
        {"name": "A", "category": "Cat1", "route": "/api/a", "safety_level": "read_only", "tool_used": None,
         "classify": lambda: {"status": STATUS_REAL, "detail": ""}},
        {"name": "B", "category": "Cat2", "route": "/api/b", "safety_level": "read_only", "tool_used": None,
         "classify": lambda: {"status": STATUS_MOCK, "detail": ""}},
    ]
    service = _isolated_service(tmp_path, caps)
    assert len(service.list_capabilities(category="Cat1")) == 1
    assert len(service.list_capabilities(status=STATUS_MOCK)) == 1
    assert len(service.list_capabilities(category="Cat1", status=STATUS_MOCK)) == 0


def test_last_verified_reads_real_governance_events(tmp_path):
    storage = StorageService(data_dir=str(tmp_path / "data"))
    storage.append("governance_log.json", {"tool_used": "MyTool", "created_at": "2026-01-01T00:00:00+00:00"})
    storage.append("governance_log.json", {"tool_used": "MyTool", "created_at": "2026-06-01T00:00:00+00:00"})
    storage.append("governance_log.json", {"tool_used": "OtherTool", "created_at": "2026-12-01T00:00:00+00:00"})
    caps = [{"name": "A", "category": "Cat1", "route": "/api/a", "safety_level": "read_only",
             "tool_used": "MyTool", "classify": lambda: {"status": STATUS_REAL, "detail": ""}}]
    service = CapabilityDirectoryService(storage, GovernanceService(storage), caps)
    entries = service.list_capabilities()
    assert entries[0]["last_verified"] == "2026-06-01T00:00:00+00:00"  # the later of the two MyTool events


def test_last_verified_none_when_tool_never_used(tmp_path):
    caps = [{"name": "A", "category": "Cat1", "route": "/api/a", "safety_level": "read_only",
             "tool_used": "NeverUsedTool", "classify": lambda: {"status": STATUS_REAL, "detail": ""}}]
    service = _isolated_service(tmp_path, caps)
    assert service.list_capabilities()[0]["last_verified"] is None


def test_summary_counts_by_status(tmp_path):
    caps = [
        {"name": "A", "category": "Cat1", "route": "/api/a", "safety_level": "read_only", "tool_used": None,
         "classify": lambda: {"status": STATUS_REAL, "detail": ""}},
        {"name": "B", "category": "Cat1", "route": "/api/b", "safety_level": "read_only", "tool_used": None,
         "classify": lambda: {"status": STATUS_REAL, "detail": ""}},
        {"name": "C", "category": "Cat1", "route": "/api/c", "safety_level": "read_only", "tool_used": None,
         "classify": lambda: {"status": STATUS_MOCK, "detail": ""}},
    ]
    service = _isolated_service(tmp_path, caps)
    summary = service.summary()
    assert summary["total"] == 3
    assert summary["by_status"][STATUS_REAL] == 2
    assert summary["by_status"][STATUS_MOCK] == 1


# ------------------------------------------------------------------
# Full app wiring -- the real ~20-capability registry built in routes.py.
# ------------------------------------------------------------------
def test_endpoint_lists_real_registry():
    data = client.get("/api/capability-directory").json()
    assert data["count"] >= 15
    names = {c["name"] for c in data["capabilities"]}
    assert "LLM Router (multi-provider text generation)" in names
    assert "Code Writer (real commits + PRs)" in names
    for entry in data["capabilities"]:
        assert entry["status"] in ("real", "local", "mock", "needs_config", "blocked", "unknown")
        assert entry["category"]
        assert entry["route"].startswith("/api/")


def test_adaptive_learning_entry_reflects_real_tick_wiring():
    """The entry used to be a hardcoded static string ('local retrieval only; never
    trains a model') that undersold real round-10/11 wiring: learn() runs every
    scheduler tick, and completed Kaggle job output gets ingested. Detail text must
    now reflect the live recall_engine + last-tick-ingested count, not a frozen string."""
    data = client.get("/api/capability-directory").json()
    entry = next(c for c in data["capabilities"] if c["name"] == "Adaptive Learning (retrieval memory + few-shot)")
    assert entry["status"] == "local"
    assert "auto-learns every scheduler tick" in entry["detail"]
    assert "recall_engine=" in entry["detail"]
    assert "last_tick_ingested=" in entry["detail"]


def test_summary_endpoint_shape():
    data = client.get("/api/capability-directory/summary").json()
    assert "total" in data and "by_status" in data and "categories" in data
    assert data["total"] == len(data["capabilities"])


def test_category_filter_endpoint():
    data = client.get("/api/capability-directory", params={"category": "Code & Git"}).json()
    assert data["count"] >= 1
    assert all(c["category"] == "Code & Git" for c in data["capabilities"])


def test_status_filter_endpoint():
    data = client.get("/api/capability-directory", params={"status": "mock"}).json()
    assert all(c["status"] == "mock" for c in data["capabilities"])


def test_governance_logged_on_summary_view():
    before = client.get("/api/governance").json()["total_events"]
    client.get("/api/capability-directory/summary")
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "capability_directory_viewed" in {e.get("action_type") for e in after["recent_events"]}


def test_analytics_includes_capability_directory():
    analytics = client.get("/api/analytics").json()
    for key in ("capability_directory_total", "capability_directory_real", "capability_directory_needs_config"):
        assert key in analytics


def test_existing_endpoints_still_work():
    assert client.get("/api/os2/command-center").status_code == 200
    assert client.get("/api/durable-workflows/summary").status_code == 200
