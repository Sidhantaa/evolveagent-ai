from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_analyze_flags_high_risk():
    code = "import os\ndef run(x):\n    eval(x)\n    password = 'hunter2'\n    os.system('ls')\n"
    r = client.post("/api/code-intel/analyze", json={"code": code, "language": "python"}).json()
    assert r["risk_level"] == "high"
    messages = " ".join(f["message"] for f in r["bug_risks"]).lower()
    assert "eval" in messages
    assert "secret" in messages or "hard-coded" in messages
    assert r["suggested_refactors"]


def test_analyze_clean_code_low_risk():
    code = "def add(a, b):\n    return a + b\n"
    r = client.post("/api/code-intel/analyze", json={"code": code}).json()
    assert r["risk_level"] == "low"
    assert r["metrics"]["functions"] == 1


def test_route_map_extraction():
    code = '@router.get("/api/thing")\ndef thing(): pass\n@router.post("/api/thing/create")\ndef create(): pass\n'
    r = client.post("/api/code-intel/routes", json={"code": code}).json()
    assert r["count"] == 2
    paths = {rt["path"] for rt in r["routes"]}
    assert "/api/thing" in paths


def test_dependencies_extraction():
    code = "import os\nfrom fastapi import FastAPI\nimport re\n"
    r = client.post("/api/code-intel/dependencies", json={"code": code}).json()
    assert "os" in r["dependencies"] and "fastapi" in r["dependencies"]


def test_test_coverage_count():
    code = "def test_a(): pass\ndef test_b(): pass\ndef helper(): pass\n"
    r = client.post("/api/code-intel/test-coverage", json={"code": code}).json()
    assert r["test_count"] == 2


def test_summary_and_analytics():
    summary = client.get("/api/code-intel/summary").json()
    assert "capabilities" in summary and "risk_patterns" in summary
    assert "code_intel_risk_patterns" in client.get("/api/analytics").json()


def test_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/code-intel/analyze", json={"code": "def f(): pass"})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert "code_analyzed" in {e.get("action_type") for e in after["recent_events"]}


def test_existing_endpoints_still_work():
    assert client.get("/api/doc-intel/summary").status_code == 200
    assert client.get("/api/productivity/summary").status_code == 200
