"""v150 Autonomous Software Team — CodeWriterService's real write (write_and_commit):
off by default, only ever targets an explicitly allow-listed repo, writes exactly
one file on a brand-new branch, makes one local commit, never pushes. All git
calls run against a genuinely isolated throwaway repo under tmp_path — never the
real EvolveAgent repository."""

import subprocess

from app.services.code_writer_service import CodeWriterService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


def _init_repo(path) -> str:
    repo = str(path)
    subprocess.run(["git", "init", "-q", repo], check=True)
    subprocess.run(["git", "-C", repo, "config", "user.email", "test@example.com"], check=True)
    subprocess.run(["git", "-C", repo, "config", "user.name", "Test"], check=True)
    (path / "README.md").write_text("init\n")
    subprocess.run(["git", "-C", repo, "add", "."], check=True)
    subprocess.run(["git", "-C", repo, "commit", "-q", "-m", "initial"], check=True)
    return repo


def _service(tmp_path):
    s = StorageService(data_dir=str(tmp_path / "data"))
    return CodeWriterService(GovernanceService(s))


def test_declines_by_default_when_writes_disabled(tmp_path, monkeypatch):
    monkeypatch.delenv("CODE_WRITES_ENABLED", raising=False)
    repo = _init_repo(tmp_path / "repo")
    svc = _service(tmp_path)
    result = svc.write_and_commit(repo, "notes.txt", "hello", "add notes")
    assert result["wrote"] is False
    assert "CODE_WRITES_ENABLED" in result["note"]


def test_declines_when_repo_not_allow_listed(tmp_path, monkeypatch):
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.delenv("CODE_WRITER_ALLOWED_REPOS", raising=False)
    repo = _init_repo(tmp_path / "repo")
    svc = _service(tmp_path)
    result = svc.write_and_commit(repo, "notes.txt", "hello", "add notes")
    assert result["wrote"] is False
    assert "allow-list" in result["note"]


def test_real_commit_on_new_branch_when_opted_in(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "repo")
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    svc = _service(tmp_path)

    original_branch = subprocess.run(
        ["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True,
    ).stdout.strip()

    result = svc.write_and_commit(repo, "src/hello.py", "print('hi')\n", "add hello", branch_name="feature/hello")
    assert result["wrote"] is True
    assert result["branch"] == "feature/hello"
    assert len(result["commit_sha"]) == 40
    assert result["file_path"] == "src/hello.py"

    # The file is really on disk, on the new branch.
    assert (tmp_path / "repo" / "src" / "hello.py").read_text() == "print('hi')\n"
    log = subprocess.run(["git", "-C", repo, "log", "--oneline", "-1"], capture_output=True, text=True, check=True).stdout
    assert "add hello" in log

    # The original branch is untouched — this file doesn't exist there.
    subprocess.run(["git", "-C", repo, "checkout", "-q", original_branch], check=True)
    assert not (tmp_path / "repo" / "src" / "hello.py").exists()


def test_path_traversal_is_rejected(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "repo")
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    svc = _service(tmp_path)
    result = svc.write_and_commit(repo, "../../etc/passwd", "evil", "escape")
    assert result["wrote"] is False
    assert "inside the repo" in result["note"]
    branches = subprocess.run(["git", "-C", repo, "branch"], capture_output=True, text=True, check=True).stdout
    assert len(branches.strip().splitlines()) == 1  # no new branch was ever created


def test_content_too_large_is_rejected(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "repo")
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    svc = _service(tmp_path)
    huge = "x" * (200_000 + 1)
    result = svc.write_and_commit(repo, "big.txt", huge, "too big")
    assert result["wrote"] is False
    assert "limit" in result["note"]


def test_failure_mid_sequence_rolls_back_to_original_branch(tmp_path, monkeypatch):
    repo_path = tmp_path / "repo"
    repo = _init_repo(repo_path)
    # Create a FILE named "blocker" so os.makedirs(".../blocker") fails —
    # forces an OSError after the new branch has already been checked out.
    (repo_path / "blocker").write_text("i am a file, not a directory")
    subprocess.run(["git", "-C", repo, "add", "blocker"], check=True)
    subprocess.run(["git", "-C", repo, "commit", "-q", "-m", "add blocker"], check=True)

    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    svc = _service(tmp_path)
    original_branch = subprocess.run(
        ["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True,
    ).stdout.strip()

    result = svc.write_and_commit(repo, "blocker/nested.txt", "content", "should fail", branch_name="feature/fails")
    assert result["wrote"] is False

    current_branch = subprocess.run(
        ["git", "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert current_branch == original_branch  # rolled back, not stranded on the half-finished branch


def test_status_reports_secret_safe_configuration(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path / "repo")
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    svc = _service(tmp_path)
    status = svc.status()
    assert status["writes_enabled"] is True
    assert repo in status["allowed_repos"]
    assert status["push_enabled"] is False  # separate opt-in, off here
    # push is narrowly allowed (git push origin <branch> only); nothing
    # destructive or remote-arbitrary is ever on the allow-list.
    assert "push" in status["allowed_git_subcommands"]
    assert "reset" not in status["allowed_git_subcommands"]
    assert "clean" not in status["allowed_git_subcommands"]


def test_endpoints_still_work():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    status = client.get("/api/code-writer/status").json()
    assert status["available"] is True
    assert client.get("/api/code-writer/summary").status_code == 200
    assert "code_writer_writes_enabled" in client.get("/api/analytics").json()
    assert "code_writer_push_enabled" in client.get("/api/analytics").json()


# ------------------------------------------------------------------
# v150 task 2 — push_branch: a bigger escalation than a local commit, gated by
# its OWN opt-in flag (CODE_WRITER_PUSH_ENABLED) on top of writes_enabled().
# Pushes to a genuine local bare repo standing in for "origin" — real git
# network protocol, zero actual network access.
# ------------------------------------------------------------------
def _init_repo_with_bare_origin(tmp_path):
    bare = str(tmp_path / "origin.git")
    subprocess.run(["git", "init", "-q", "--bare", bare], check=True)
    repo = _init_repo(tmp_path / "repo")
    subprocess.run(["git", "-C", repo, "remote", "add", "origin", bare], check=True)
    return repo, bare


def test_push_declines_when_writes_disabled(tmp_path, monkeypatch):
    repo, _ = _init_repo_with_bare_origin(tmp_path)
    monkeypatch.delenv("CODE_WRITES_ENABLED", raising=False)
    monkeypatch.setenv("CODE_WRITER_PUSH_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    svc = _service(tmp_path)
    result = svc.push_branch(repo, "feature/x")
    assert result["pushed"] is False
    assert "CODE_WRITES_ENABLED" in result["note"]


def test_push_declines_when_push_not_separately_enabled(tmp_path, monkeypatch):
    repo, _ = _init_repo_with_bare_origin(tmp_path)
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.delenv("CODE_WRITER_PUSH_ENABLED", raising=False)
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    svc = _service(tmp_path)
    result = svc.push_branch(repo, "feature/x")
    assert result["pushed"] is False
    assert "CODE_WRITER_PUSH_ENABLED" in result["note"]


def test_push_declines_when_repo_not_allow_listed(tmp_path, monkeypatch):
    repo, _ = _init_repo_with_bare_origin(tmp_path)
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_PUSH_ENABLED", "true")
    monkeypatch.delenv("CODE_WRITER_ALLOWED_REPOS", raising=False)
    svc = _service(tmp_path)
    result = svc.push_branch(repo, "feature/x")
    assert result["pushed"] is False
    assert "allow-list" in result["note"]


def test_real_push_to_origin_when_both_opted_in(tmp_path, monkeypatch):
    repo, bare = _init_repo_with_bare_origin(tmp_path)
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_PUSH_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    svc = _service(tmp_path)

    write_result = svc.write_and_commit(repo, "src/x.py", "x = 1\n", "add x", branch_name="feature/x")
    assert write_result["wrote"] is True

    push_result = svc.push_branch(repo, "feature/x")
    assert push_result["pushed"] is True
    assert push_result["branch"] == "feature/x"

    # The bare "origin" really has the branch now.
    branches = subprocess.run(["git", "-C", bare, "branch"], capture_output=True, text=True, check=True).stdout
    assert "feature/x" in branches


def test_push_of_nonexistent_branch_fails_safely(tmp_path, monkeypatch):
    repo, _ = _init_repo_with_bare_origin(tmp_path)
    monkeypatch.setenv("CODE_WRITES_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_PUSH_ENABLED", "true")
    monkeypatch.setenv("CODE_WRITER_ALLOWED_REPOS", repo)
    svc = _service(tmp_path)
    result = svc.push_branch(repo, "branch/does-not-exist")
    assert result["pushed"] is False
    assert result["note"]


def test_branch_name_sanitization_strips_leading_dashes():
    # A caller-supplied name that looks like a git flag (e.g. "--force") must
    # never be passed to git as-is — leading dashes/dots are stripped so it can
    # only ever be interpreted as a literal ref, never a flag.
    assert CodeWriterService._safe_branch_name("--force") == "force"
    assert CodeWriterService._safe_branch_name("-x") == "x"
    assert CodeWriterService._safe_branch_name("...weird") == "weird"
    assert CodeWriterService._safe_branch_name("feature/normal") == "feature/normal"
    assert CodeWriterService._safe_branch_name("").startswith("eva/auto-")
    assert CodeWriterService._safe_branch_name("---").startswith("eva/auto-")
