"""v120 task 4 — multi-step approval pipelines: a workflow step naming 2+
approvers is backed by a real ApprovalService sign-off chain instead of a
single boolean gate. Steps with 0-1 approvers are unaffected."""

from app.services.approval_service import ApprovalService
from app.services.durable_workflow_service import DurableWorkflowService
from app.services.governance_service import GovernanceService
from app.services.storage_service import StorageService


def _services(tmp_path):
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    approvals = ApprovalService(s, g)
    workflows = DurableWorkflowService(s, g, approvals=approvals)
    return s, g, workflows, approvals


def test_single_approver_step_is_unaffected(tmp_path):
    """0-1 named approvers => the original single boolean gate, no chain created."""
    _, _, workflows, approvals = _services(tmp_path)
    definition = workflows.create_definition({"name": "One", "steps": [
        {"name": "send it", "action": "send", "approvers": ["finance"]},
    ]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "waiting_approval"
    assert run["steps"][0]["approval_chain_id"] is None
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"


def test_no_approvers_step_unaffected_by_approvals_collaborator(tmp_path):
    _, _, workflows, _ = _services(tmp_path)
    definition = workflows.create_definition({"name": "Plain", "steps": [{"name": "x"}]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "completed"
    assert run["steps"][0]["approval_chain_id"] is None


def test_two_approvers_creates_a_real_chain_and_requires_both(tmp_path):
    _, _, workflows, approvals = _services(tmp_path)
    definition = workflows.create_definition({"name": "Payment", "steps": [
        {"name": "wire the payment", "action": "pay", "approvers": ["finance", "security"]},
    ]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "waiting_approval"
    chain_id = run["steps"][0]["approval_chain_id"]
    assert chain_id
    chain = approvals.get_chain(chain_id)
    assert chain["status"] == "pending"
    assert [s["title"] for s in chain["steps"]] == ["Approval from finance", "Approval from security"]

    # First sign-off: chain still pending, run stays gated on the SAME step.
    after_first = workflows.approve_step(run["run_id"], approved=True, approver="finance")
    assert after_first["status"] == "waiting_approval"
    assert after_first["cursor"] == 0
    assert after_first["steps"][0]["approval_progress"]["status"] == "pending"

    # Second sign-off: chain fully approved, run advances/completes.
    after_second = workflows.approve_step(run["run_id"], approved=True, approver="security")
    assert after_second["status"] == "completed"
    assert after_second["steps"][0]["status"] == "done"


def test_any_rejection_in_the_chain_skips_the_step_immediately(tmp_path):
    _, _, workflows, approvals = _services(tmp_path)
    definition = workflows.create_definition({"name": "Payment2", "steps": [
        {"name": "wire the payment", "action": "pay", "approvers": ["finance", "security"]},
    ]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    rejected = workflows.approve_step(run["run_id"], approved=False, approver="finance", note="too risky")
    assert rejected["status"] == "completed"  # only step is skipped, run still finishes
    assert rejected["steps"][0]["status"] == "skipped"
    chain = approvals.get_chain(run["steps"][0]["approval_chain_id"])
    assert chain["status"] == "rejected"


def test_multi_approver_gate_visible_via_existing_approvals_api():
    from fastapi.testclient import TestClient
    from app.main import app
    client = TestClient(app)
    d = client.post("/api/durable-workflows/definitions", json={
        "name": "E2E-Multi", "steps": [{"name": "pay vendor", "action": "pay", "approvers": ["finance", "security"]}],
    }).json()
    run = client.post("/api/durable-workflows/runs", json={"definition_id": d["definition_id"]}).json()
    assert run["status"] == "waiting_approval"
    chain_id = run["steps"][0]["approval_chain_id"]
    fetched = client.get(f"/api/approvals/{chain_id}").json()
    assert fetched["approval_id"] == chain_id
    assert len(fetched["steps"]) == 2

    r1 = client.post(f"/api/durable-workflows/runs/{run['run_id']}/approve",
                      json={"approved": True, "approver": "finance"}).json()
    assert r1["status"] == "waiting_approval"
    r2 = client.post(f"/api/durable-workflows/runs/{run['run_id']}/approve",
                      json={"approved": True, "approver": "security"}).json()
    assert r2["status"] == "completed"


def test_without_approvals_wired_multi_approver_field_is_inert(tmp_path):
    """Backward compatibility: no ApprovalService collaborator => a step with
    approvers behaves like a plain single-gate step (approvers field is inert)."""
    s = StorageService(data_dir=str(tmp_path))
    g = GovernanceService(s)
    workflows = DurableWorkflowService(s, g)  # no approvals collaborator
    definition = workflows.create_definition({"name": "NoApprovals", "steps": [
        {"name": "pay", "action": "pay", "approvers": ["finance", "security"]},
    ]})
    run = workflows.start_run({"definition_id": definition["definition_id"]})
    assert run["status"] == "waiting_approval"
    assert run["steps"][0]["approval_chain_id"] is None
    finished = workflows.approve_step(run["run_id"], approved=True)
    assert finished["status"] == "completed"
