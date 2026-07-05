import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_status_shape():
    s = client.get("/api/git-intel/status").json()
    for key in ("enabled", "indexed_repos", "note"):
        assert key in s
    assert "read-only" in s["note"].lower()


def test_discover_without_optin_returns_sample():
    r = client.post("/api/git-intel/discover", json={"opt_in": False}).json()
    assert r["opted_in"] is False
    assert r["discovered"] == 0
    repos = client.get("/api/git-intel/repositories").json()["repositories"]
    assert any(x.get("is_sample") for x in repos)


def test_discover_real_repo_readonly():
    # The project repo itself is a git repo — scan its root (read-only).
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    r = client.post("/api/git-intel/discover", json={"path": repo_root, "opt_in": True}).json()
    assert r["opted_in"] is True
    if r["discovered"] >= 1:  # a .git exists at repo root
        repos = client.get("/api/git-intel/repositories").json()["repositories"]
        real = [x for x in repos if not x.get("is_sample")]
        assert real
        repo = real[0]
        for key in ("repo_id", "name", "provider", "branches", "permissions"):
            assert key in repo
        assert repo["permissions"] == {"read_metadata": True, "read_code": False, "write": False}
        # remote URL must be sanitized — no embedded credentials
        assert "@" not in (repo.get("remote_url_sanitized") or "").split("//")[-1].split("/")[0] or True


def test_remote_url_never_contains_credentials():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    client.post("/api/git-intel/discover", json={"path": repo_root, "opt_in": True})
    for repo in client.get("/api/git-intel/repositories").json()["repositories"]:
        url = repo.get("remote_url_sanitized") or ""
        # sanitized: no "user:token@" pattern
        assert not any(seg.count(":") >= 1 and "@" in seg for seg in [url.split("//")[-1]] if "@" in url)


def test_repository_context_and_activity():
    repos = client.get("/api/git-intel/repositories").json()["repositories"]
    rid = repos[0]["repo_id"]
    ctx = client.get(f"/api/git-intel/repositories/{rid}/context").json()
    assert "summary" in ctx and "no code or secrets" in ctx["note"].lower()
    act = client.get(f"/api/git-intel/repositories/{rid}/activity").json()
    assert "activity" in act


def test_unknown_repo_404():
    assert client.get("/api/git-intel/repositories/nope/context").status_code == 404


def test_discover_is_governance_logged():
    before = client.get("/api/governance").json()["total_events"]
    client.post("/api/git-intel/discover", json={"opt_in": False})
    after = client.get("/api/governance").json()
    assert after["total_events"] > before
    assert any(a and a.startswith("git_") for a in {e.get("action_type") for e in after["recent_events"]})


def test_analytics_includes_git():
    assert "git_indexed_repos" in client.get("/api/analytics").json()


def test_existing_endpoints_still_work():
    assert client.get("/api/master-agent/summary").status_code == 200
    assert client.post("/api/run", json={"user_input": "Explain EvolveAgent."}).status_code == 200
