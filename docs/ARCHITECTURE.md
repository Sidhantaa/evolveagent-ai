# EvolveAgent AI — Architecture

EvolveAgent AI is a local-first, workspace-aware multi-agent AI operating system built with FastAPI + React, featuring governed automation, JSON persistence, workspace memory, agent orchestration, project/business/personal operating layers, MCP connector planning, and Developer Mode observability.

> **Current scale (through v44):** 44 implementation versions · 85 backend services · ~480 API routes · 48 test modules · 494 passing backend tests · ~10,200-line React UI.

This document collects the system's architecture diagrams. All diagrams use Mermaid and render directly in GitHub markdown.

---

## 1. High-Level System Diagram

```mermaid
flowchart TD
    A[User / File / Recording / Linear / Workspace Input] --> B[Master Orchestrator Agent]
    B --> C[Specialist Agents + Tools]
    C --> D[Governance + Permission Layer]
    D --> E[LLM / File / Recording / Automation Workflow]
    E --> F[Judge Agent + Evaluation Lab]
    F --> G[Memory + Analytics + Learning]
    G --> H[Final Answer / Project Update / Export / Report]
```

The Master Orchestrator Agent classifies each request, routes it through the correct workflow, coordinates specialist agents under the governance layer, evaluates the result, stores memory and analytics, and returns one clean response. Simple Mode shows only the answer; Developer Mode exposes every layer.

---

## 2. Agent Workflow Diagram

```mermaid
flowchart TD
    IN[Request + Workspace Context] --> DET[Task Type Detection]

    DET -->|Text| RES[Research Agent]
    DET -->|File| FILE[File Analysis Agent]
    DET -->|Recording| REC[Recording Analysis Agent]
    DET -->|Image| IMG[Image Agent]
    DET -->|Goal| GOAL[Goal Planner Agent]
    DET -->|Automation| AUTO[Project Scanner + Planner]

    FILE --> RES
    REC --> RES
    RES --> LOGIC[Logic Agent]
    LOGIC --> RISK[Risk Agent]
    RISK --> STRAT[Strategy Agent]
    STRAT --> WRITE[Writing Agent]
    WRITE --> JUDGE[Judge Agent]
    JUDGE --> EVAL[Per-Agent Evaluation]
    EVAL --> EVO[Evolution Agent]
    EVO --> MEM[Memory Agent]
    MEM --> OUT[Final Response]

    IMG --> JUDGE
    GOAL --> OUT
    AUTO --> APPROVE[Approval Gate]
    APPROVE --> OUT
```

Specialist agents run in a pipeline: research → logic → risk → strategy → writing, then judge and evolution feedback, then memory. File, recording, image, goal, and automation tasks branch into the pipeline at the right point.

---

## 3. Governance Workflow Diagram

```mermaid
flowchart TD
    REQ[Incoming Request or Tool/Edit/Command] --> FIRE[Prompt Injection Firewall]
    FIRE --> SCAN[Secret Scanner]
    SCAN --> PERM[Permission System]
    PERM -->|read_only / plan_only| RUN[Execute or Plan]
    PERM -->|approve_to_edit / approve_to_run| QUEUE[Approval Queue]
    PERM -->|blocked| DENY[Blocked + Logged]
    QUEUE --> DECISION{Human Decision}
    DECISION -->|Approve| RUN
    DECISION -->|Reject| REJECT[Rejected + Audit Record]
    RUN --> LOG[Governance Log]
    DENY --> LOG
    REJECT --> LOG
```

Every risky action passes the prompt-injection firewall and secret scanner, then the permission system. Edit/run actions require human approval; blocked actions are denied. All decisions are written to the governance log with an audit trail.

---

## 4. Linear / Codex Workflow Diagram

```mermaid
flowchart TD
    L[Linear Issue moved to In Progress] --> POLL[Linear Poller]
    POLL --> BRANCH[Create linear/evo-* branch]
    BRANCH --> HANDOFF[Write handoff file in docs/linear-handoffs/]
    HANDOFF --> CODEX[Guarded Codex Worker Job]
    CODEX --> VERIFY[Run tests + frontend build]
    VERIFY -->|Pass| COMMENT[Post success comment to Linear]
    VERIFY -->|Fail| FAILCOMMENT[Post failure comment to Linear]
    COMMENT --> REVIEW[Issue ready for In Review]
    FAILCOMMENT --> REVIEW
```

The Linear/Codex worker is optional and server-side only. Keys live in `backend/.env` and are never exposed to the frontend. Full autonomous mode is disabled by default; verification (tests + build) gates every completion.

---

## 5. Workspace Memory Flow

```mermaid
flowchart TD
    START[Run starts in active workspace] --> RETR[Retrieve relevant memory]
    RETR --> SCORE[Local sparse vector-style scoring]
    SCORE --> CAP[Cap context size]
    CAP --> USE[Inject capped memory into agents]
    USE --> RESP[Agents produce answer]
    RESP --> STORE[Store new memory entries]
    STORE --> TIER[Quality scoring + hot/warm/archived tiers]
    TIER --> IDX[Update local JSON vector index]
    IDX --> CONS[Consolidation jobs dedupe + archive]
```

Workspace memory is scoped per project. Before each run, a small capped set of high-value memories is retrieved using local semantic-style scoring. New results are scored, tiered, indexed, and periodically consolidated — all JSON-backed, with no external vector database.

---

## 6. Evaluation / Analytics Flow

```mermaid
flowchart TD
    RUN[Completed Run] --> JUDGE[Judge Agent Scores]
    JUDGE --> PERAGENT[Per-Agent Usefulness + Clarity]
    PERAGENT --> ANALYTICS[Analytics Storage]
    ANALYTICS --> LEARN[Adaptive Learning Engine]
    LEARN --> PROMPTS[Prompt Versions + Workflow Strategy]
    LEARN --> ROUTING[Model Routing Suggestions]
    LEARN --> PREFS[User Preference Patterns]
    ANALYTICS --> LAB[AI Evaluation Lab]
    LAB --> BENCH[Benchmarks + A/B Tests + Regression Checks]
    BENCH --> REPORT[Evaluation + Learning Reports]
    PROMPTS --> APPROVAL[Approval-gated prompt changes]
```

Judge and per-agent scores feed analytics, which drives the Adaptive Learning Engine and the AI Evaluation Lab. The learning layer self-optimizes the orchestration layer — prompt versions, workflow strategy, model routing, and user preferences — and proposed prompt changes are approval-gated. The base LLM is never retrained.

---

## Safety Boundaries (Architecture-Level)

- No unrestricted shell execution — only an allowlist of build/test commands.
- No silent file edits — edits require explicit approval.
- Approval required for all risky (edit/run) actions.
- Secrets are redacted by the secret scanner.
- Prompt injection is checked by the firewall on every request.
- Governance logs are stored for every decision.
- The base LLM is not self-trained; only the orchestration layer self-optimizes.

## v41 — MCP Connector Hub

The MCP Connector Hub (`backend/app/services/mcp_connector_service.py`, routes under `/api/mcp`) follows the standard pattern: thin route → service → `StorageService` JSON (`mcp_connectors.json`, `mcp_connector_events.json`) → `GovernanceService` logging → Developer-Mode UI panel.

It maintains a local registry of MCP-style connectors with 9 default templates (Filesystem, Git, GitHub, Linear, Context7, Playwright, Slack, Notion, Desktop Commander). Connectors carry a risk level, a mode (read_only / approval_required / disabled), allowed/blocked action lists, and the *names* of required environment keys. Status checks are dry/mock and expose only booleans for env-key readiness — never values. Action planning enforces approval and risk rules and never executes real external/MCP calls in this version. Every stateful action is governance-logged and recorded as a connector event.

**Boundaries:** no real MCP execution by default, no secrets exposed to frontend/logs/API, no unrestricted shell, no full desktop control; high-risk connectors stay approval-required or disabled by default.

## v42 — MCP Execution Adapter

The MCP Execution Adapter (`backend/app/services/mcp_execution_service.py`, routes under `/api/mcp/executions` and `/api/mcp/connectors/{id}/execute`) layers a governed execution loop on top of the v41 planning service. It reuses `MCPConnectorService.plan_connector_action` for all risk/block/allow validation, then drives a request → approve → run → record state machine persisted in `mcp_execution_requests.json` and `mcp_execution_results.json`.

Read-only low-risk actions are auto-approved; every other action waits for explicit human approval; blocked or disabled connectors never produce a runnable request. Running an approved request re-validates the connector and then invokes a mock executor — `EXECUTION_MODE = "mock"` guarantees no real MCP server, network call, shell command, or device action, and no secrets are read or returned. Every step is governance-logged and surfaced in analytics.

## v43 — MCP Read-Only Adapter

The MCP Read-Only Adapter (`backend/app/services/mcp_readonly_adapter.py`) extends the v42 execution loop with the platform's first real tool-execution path — deliberately the safest possible one. `MCPExecutionService.run_execution` consults the adapter before falling back to the mock executor.

The adapter executes for real only when every condition holds: the `MCP_REAL_READONLY` env opt-in is set, the connector is enabled, the request is approved, and the action is on a fixed allow-list (`git_current_branch`, `git_list_branches`, `fs_list_directory`, `fs_file_metadata`). Git actions read `.git/HEAD` and `refs/heads` as plain files (no subprocess); filesystem actions return directory listings and file metadata (names and sizes only). It is standard-library only — no shell, no network, no writes/deletes, no secrets, and it never returns file contents. Every real path is sandboxed to the repo root with traversal + absolute-path blocking and a sensitive-name denylist, and `GET /api/mcp/adapter/status` reports the opt-in state, allow-list, and sandbox root. With the opt-in off (default), behaviour is identical to v42.

## v44 — MCP Approvals Inbox

The MCP Approvals Inbox (`backend/app/services/mcp_approvals_inbox_service.py`, routes under `/api/mcp/inbox`) aggregates every MCP item awaiting human approval into one prioritized queue. It reads the v42 execution requests in `pending_approval` status, enriches each with the connector name (via the connector service), risk level, and age, and sorts them high-risk first then oldest first, with an optional risk-level filter.

Approve and reject delegate to `MCPExecutionService.approve_execution` / `reject_execution`, which perform the status transition and governance logging. The inbox therefore holds no independent execution power — it is a read/triage layer plus delegated decisions. It adds no new storage (it derives from existing execution state) and contributes pending-count and high-risk metrics to the analytics summary.

## v45 — MCP Policy Engine

The MCP Policy Engine (`backend/app/services/mcp_policy_service.py`, routes under `/api/mcp/policies`) adds declarative, tighten-only guardrails over the MCP surface. Policies are deny rules (the only effect) that match on connector slug, action, and risk level — each supporting a `*` wildcard — plus an optional `except_actions` carve-out.

The engine is injected into `MCPConnectorService.plan_connector_action` (optional dependency; `None` by default) and evaluated before any other check: a match returns a blocked plan with a governance-logged denial, and a non-match falls through to the existing v41 rules. Because planning gates execution, a denial also blocks v42 execution. Crucially it is tighten-only — there is no allow effect, so policies can only add blocks and never widen access; with no policies defined the system behaves exactly as it did at v44.

## v46 — MCP Audit & Replay

The MCP Audit & Replay service (`backend/app/services/mcp_audit_service.py`, routes under `/api/mcp/audit`) provides a read-only unified timeline across connector events (v41), execution requests/results (v42/v43), and MCP-tagged governance events, with filtering and markdown/JSON export. Its replay endpoint re-derives what a past execution request would do today via `plan_connector_action` (dry) — it never executes, records a stored replay artifact, and logs a governance event. Paired with the v45.1 frontend pass that reorganized the MCP Hub into internal tabs (Connectors/Policies/Approvals/Executions/Audit).

## v47 — Secret Reference Registry

The Secret Reference Registry (`backend/app/services/mcp_secret_registry_service.py`, routes under `/api/mcp/secrets`) is a local catalog of the secret/env keys the MCP connectors and other integrations require. It stores the key name, an owner/label/category, and an optional rotation interval — never the value. Readiness is computed from `os.environ` as a boolean, and a rotation-due flag is derived from the interval and last-rotated timestamp. A defensive presenter strips any value field, so the API and UI only ever expose the key name and an is_set boolean. Registration, update, and rotation are governance-logged, and a Secrets tab surfaces it in the MCP Hub.

## v48 — Unified Approvals Center

The Unified Approvals Center (`backend/app/services/unified_approvals_service.py`, routes under `/api/approvals-center`) generalizes the v44 MCP inbox across every approval source. It aggregates pending MCP execution requests and business-operator approval items into one normalized, prioritized queue (high-risk then oldest first, with a source filter). Approve and reject delegate to the owning service, which performs the state transition and governance logging, so the center holds no independent execution power. It uses a distinct /approvals-center prefix to avoid colliding with the pre-existing /approvals workflow.

## v49 — Health & Readiness Monitor

The Health & Readiness Monitor (`backend/app/services/health_monitor_service.py`, routes under `/api/health-monitor`) aggregates read-only health signals from local state — governance blocked ratio, approvals backlog, secret-key readiness, MCP connectors, and policy posture — into per-check statuses and an overall score with recommendations. It performs no actions; the only write is a governance-logged health snapshot.
