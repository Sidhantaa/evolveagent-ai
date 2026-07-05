import os

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# The repository root (parent of backend/) is a git work tree in dev and CI.
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def test_read_status():
    s = client.get("/api/git-intel/read-status").json()
    assert s["read_only"] is True
    assert "log" in s["allowed_subcommands"] and "commit" not in s["allowed_subcommands"]


def test_log_returns_commits():
    r = client.get("/api/git-intel/log", params={"path": REPO, "limit": 5}).json()
    assert r["count"] >= 1
    top = r["commits"][0]
    assert len(top["sha"]) >= 7 and top["subject"]


def test_branches_has_current():
    r = client.get("/api/git-intel/branches", params={"path": REPO}).json()
    assert r["count"] >= 1
    assert any(b["current"] for b in r["branches"])
    assert r["current"]


def test_commit_stat_head():
    r = client.get("/api/git-intel/commit-stat", params={"path": REPO, "ref": "HEAD"}).json()
    assert r["sha"]
    assert "files" in r  # may be empty for a merge/empty commit, but the key exists


def test_invalid_path_rejected():
    assert client.get("/api/git-intel/log", params={"path": "/definitely/not/here"}).status_code == 400


def test_non_repo_path_rejected():
    assert client.get("/api/git-intel/branches", params={"path": "/tmp"}).status_code == 400


def test_malicious_ref_rejected():
    # argv is injection-proof already, but refs are still validated to hex/HEAD.
    bad = client.get("/api/git-intel/commit-stat", params={"path": REPO, "ref": "; rm -rf /"})
    assert bad.status_code == 400


def test_analytics_and_existing_endpoints():
    assert "git_reader_available" in client.get("/api/analytics").json()
    assert client.get("/api/git-intel/status").status_code == 200
    assert client.get("/api/design-agent/status").status_code == 200
