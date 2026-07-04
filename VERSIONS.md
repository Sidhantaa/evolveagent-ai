# EvolveAgent AI Version History

EvolveAgent AI is a local-first, workspace-aware multi-agent AI operating system built with FastAPI + React, governed automation, JSON persistence, and a two-mode UI: Simple Mode and Developer Mode.

---

## Versioning Note

- This file documents the **implementation-track version map** — what actually shipped in code.
- The implementation track is **grounded in three concrete signals**: service docstrings (`backend/app/services/*.py`), the README checkpoint narrative, and the live API route groups (`backend/app/api/routes.py`).
- The repo also has a separate **official / vision roadmap track** used for planning (Linear milestone epics).
- **The planning-roadmap numbering may differ from this implementation-track numbering.** Where they diverge, the implementation track documented here is the source of truth.
- **Half-step checkpoints are preserved** — `v3.5`, `v7.5`, `v8.5`, `v11.5`, `v12.5`, and `v14.5` were real incremental polish/QA releases between the major numbered milestones and are listed as such.

## Project Scale

- **85** backend services
- **~480** API routes
- **48** service test modules
- **494** passing backend tests
- single-file React UI (~**10,300** lines)
- **58** implementation versions (v54 folded into v44.5; + the v44.5 / v45.1 passes)

## Architecture Pattern

Every feature follows the same governed path:

**Thin route → service → `StorageService` (JSON persistence) → `GovernanceService` logging → Simple Mode / Developer Mode UI.**

- **Thin route** (`backend/app/api/routes.py`) validates input via a Pydantic request model and delegates immediately.
- **Service** (`backend/app/services/<feature>_service.py`) holds all logic; no business logic lives in routes.
- **`StorageService`** persists every collection as local JSON — no external database.
- **`GovernanceService`** records every stateful action as a governance event (task type, agent, action, risk, approval/blocked state, reason).
- **Two-mode UI** — Simple Mode stays clean for end users; Developer Mode exposes a detailed panel per feature.

Each version is **additive**: it layers on top, removes no prior feature, and preserves existing API contracts.

## Safety Contract Across All Versions

Every version (from v2 onward) is built to the same contract:

- **Local-first** — all state lives on the local machine.
- **JSON persistence** — all persistent data goes through `StorageService`.
- **Mock / planning-first** — stateful and risky features draft, plan, or simulate by default rather than acting on the real world.
- **Permission-aware** — risky actions are gated behind approval and explicit permission profiles.
- **Governance-logged** — every stateful action is recorded as a governance event.
- **Simple Mode / Developer Mode** — clean for users, transparent for technical review.
- **Additive** — no feature removed; API contracts preserved.

Hard boundaries that always hold:

- **No unrestricted shell.**
- **No destructive autonomous file operations.**
- **No real sending/payment without approval.**
- **No production auth.**
- **Organization/team features are local records only.**
- **No real phone/hardware control.**
- **No mic recording or wake-word listener.**
- **No base-model self-training.**

> **v40 disclaimer:** This is not AGI. It is a governed orchestration layer across existing agents, workflows, tools, memory, simulations, and dashboards.

---

## Foundation Era — v1 to v14.5

The early era built the conversational core and the "Agent OS" beneath it, including several half-step checkpoints. A few intermediate integer versions (v4, v5, v7, v12) exist only on the planning/roadmap track and are intentionally not listed as separate implementation milestones.

### v1 — Base Conversational Agent
- **Purpose:** Original chat application — the spine everything else hangs off.
- **How it operates:** FastAPI + React; a ChatGPT-style UI calls a single `POST /api/run`. A Master Agent takes user input and returns a response. Chats and history are persisted as JSON.
- **Main API route groups:** `/api/run`, `/api/chats`, `/api/history`.
- **Safety boundary:** Conversational only; no autonomous file or system actions.

### v2 — Safe Planning & Approval-Gated Automation
- **Purpose:** Establish the governed safety posture.
- **How it operates:** The agent **plans** actions rather than executing them; risky operations become *planned* steps requiring approval. Blocks destructive edits, package installation, and unrestricted shell. Adds browser voice-command transcription.
- **Main API route groups:** `/api/run`, `/api/approvals`, `/api/transcription`.
- **Safety boundary:** No automatic file writes; destructive and shell operations blocked.

### v3 — Agent OS Foundation
- **Purpose:** The first operating-system layer beneath the UI.
- **How it operates:** Adds a **Project Brain** knowledge base (cross-session links + memory ranking), **Assistant Tools**, a governed **Tool Router** + local **plugin manifest loader**, **Approval Workflow 2.0**, **Agent Jobs**, a **System Prompt Registry**, and a thin **Kernel Service** around request orchestration.
- **Main API route groups:** `/api/tools`, `/api/agent-jobs`, `/api/system-prompts`, `/api/plugins`, `/api/assistant`.
- **Safety boundary:** Tools run through a governed router; plugins load from local manifests only.

### v3.5 — UI/UX Polish
- **Purpose:** Professional presentation pass.
- **How it operates:** Jarvis-style Simple Mode command center, responsive Developer Mode sidebar, light/dark theme tokens, onboarding walkthrough, accessibility labels, reduced-motion handling.
- **Main API route groups:** (frontend-focused; no new API surface.)
- **Safety boundary:** Presentation only; no behavioral change.

### v6 — Memory Intelligence
- **Purpose:** Make workspace memory smart and self-maintaining.
- **How it operates:** Memories are scored, tiered, and indexed in a **local sparse vector-style index** (no external infrastructure), retrieved semantically, and **consolidated through tracked jobs**. Developer Mode surfaces quality reasons, retention actions, and tier history.
- **Main API route groups:** `/api/memory`.
- **Safety boundary:** Local indexing only; no external vector database.

### v7.5 — Governed Tool Layer 2.0
- **Purpose:** Harden the tool subsystem.
- **How it operates:** Tool selections are stored as **execution history**, read-only runs carry success/quality metadata, plugin manifests get stricter validation. Tool internals stay hidden in Simple Mode.
- **Main API route groups:** `/api/tools`.
- **Safety boundary:** Read-only tool runs metadata-tracked; stricter manifest validation.

### v8 / v8.5 — Demo Readiness & Provider QA
- **Purpose:** Make the platform demoable anywhere and verify providers safely.
- **How it operates:** v8 turns Simple Mode into a focused Speak/Type console while Developer Mode keeps the full workbench. v8.5 adds `/api/providers/status` reporting readiness, configured models, fallback info, and status messages via **safe dry checks** (no paid calls by default).
- **Main API route groups:** `/api/providers`.
- **Safety boundary:** Dry provider checks by default; no paid API calls without opt-in.

### v9 — Real Image API Path
- **Purpose:** First real paid-capability path (images).
- **How it operates:** `IMAGE_MODE=real` + `IMAGE_PROVIDER=openai` route image requests through OpenAI when configured, save generated images locally, and expose image-provider readiness checks — with **mock preview fallback** if the provider is unavailable.
- **Main API route groups:** `/api/images`.
- **Safety boundary:** Opt-in real calls; mock fallback always available.

### v10 — Unified Real-API Control Layer
- **Purpose:** One control surface for all paid capabilities.
- **How it operates:** Unified readiness for **text, image, and transcription** via safe dry checks; real calls remain opt-in and every capability keeps mock fallback for local demos and tests.
- **Main API route groups:** `/api/real-api`, `/api/transcription`, `/api/images`.
- **Safety boundary:** All real capabilities opt-in with mock fallback.

### v11 / v11.5 — Cost Control & Research Agent Foundation
- **Purpose:** Add cost visibility and a safe research capability.
- **How it operates:** v11 adds a Real-API Control panel with paid-capability readiness, dry-check defaults, live-call warnings, and cost-estimate guidance. v11.5 adds the **Autonomous Research Agent**: approval-gated research sessions, sources with **local credibility scores**, and claims linked to citations.
- **Main API route groups:** `/api/real-api`, `/api/research`.
- **Safety boundary:** No unrestricted web browsing; research artifacts stored and evaluated locally.

### v12.5 — Digital Twin Work Style Engine
- **Purpose:** Model the user's working style/preferences.
- **How it operates:** Stores a local profile of work-style signals the agents reference when planning and responding.
- **Main API route groups:** `/api/digital-twin`.
- **Safety boundary:** Local profile only; no external data sharing.

### v13 — Enterprise Governance & Compliance (early layer)
- **Purpose:** Strengthen governance and quality gates.
- **How it operates:** Expands governance logging and quality checks across requests, surfacing them in Developer Mode.
- **Main API route groups:** `/api/quality`, `/api/governance`.
- **Safety boundary:** Governance-logged; quality-gated.

### v14 — Full AI Project Manager
- **Purpose:** Plan and track projects, tasks, and goals.
- **How it operates:** Manages projects with tasks and goals through structured records and dashboards.
- **Main API route groups:** `/api/project-manager`, `/api/goals`.
- **Safety boundary:** Planning/tracking only; no autonomous execution.

### v14.5 — Portfolio Mode
- **Purpose:** Roll multiple projects into a portfolio view.
- **How it operates:** Aggregates project records into a portfolio dashboard with cross-project metrics.
- **Main API route groups:** `/api/portfolio`.
- **Safety boundary:** Read/aggregate view; no autonomous changes.

---

## Platform Era — v15 to v40

From v15 onward every version follows the governed architecture above: a service, JSON persistence via `StorageService`, thin routes, a Developer-Mode panel, and **every stateful action governance-logged**. All are **local-first and mock/planning-first**, and each release is **additive**.

### v15 — EvolveAgent OS
- **Purpose:** Platform-readiness layer that rebrands the system as an operating system.
- **How it operates:** `GET /api/os/summary` combines installer readiness, plugin SDK summary, SLA rating, scheduler health, and safety notes; Developer Mode shows an EvolveAgent OS panel. Added no hosting/auth/payments.
- **Main API route groups:** `/api/os`.
- **Safety boundary:** Not autonomous without approval; no self-training, no hosted SaaS, no unrestricted shell.

### v16 — Multi-Agent Organization
- **Purpose:** Structure agents into an organization.
- **How it operates:** AI **departments** with manager/worker/reviewer/auditor roles, department dashboards, and cross-agent collaboration planning.
- **Main API route groups:** `/api/departments`.
- **Safety boundary:** Planning/structure only; governance-logged.

### v17 — Agent Workforce Marketplace
- **Purpose:** Reusable, shareable agent teams.
- **How it operates:** Agent-team **templates**, import/export, workflow packs, ratings, benchmark metadata, and safe permission profiles.
- **Main API route groups:** `/api/agent-marketplace`.
- **Safety boundary:** Permission profiles enforced; local templates only.

### v18 — Real Business Automation Layer
- **Purpose:** Business operator for leads, support, documents, and proposals.
- **How it operates:** Manages business records as **draft-only** entities. (Later extended — not duplicated — by v33.)
- **Main API route groups:** `/api/business`.
- **Safety boundary:** Draft-only; no real sending or payment.

### v19 — AI Chief of Staff
- **Purpose:** Personal executive assistant.
- **How it operates:** Captures priorities, generates daily planning, and produces briefings.
- **Main API route groups:** `/api/chief-of-staff`.
- **Safety boundary:** Planning/advisory only; governance-logged.

### v20 — Autonomous Business Simulator
- **Purpose:** Model business outcomes.
- **How it operates:** Runs simulations over scenarios and stores results (distinct from the v37 simulation world).
- **Main API route groups:** `/api/business-simulator`.
- **Safety boundary:** Simulation only; no real-world actions.

### v21 — Multi-Modal Real-World Agent
- **Purpose:** Coordinate text, image, and audio in one workflow.
- **How it operates:** Orchestrates multi-modal inputs/outputs through the existing safe provider layer with mock fallback.
- **Main API route groups:** `/api/multimodal`.
- **Safety boundary:** Mock fallback preserved; real calls opt-in.

### v22 — Industry Workflow Modes
- **Purpose:** Pre-built workflow templates per industry.
- **How it operates:** Provides industry-tuned workflow modes the user can select and apply.
- **Main API route groups:** `/api/industry-modes`.
- **Safety boundary:** Template-driven planning; governance-logged.

### v23 — Agent-to-Agent Network
- **Purpose:** Let agents collaborate and hand off work.
- **How it operates:** Foundation for agent contracts, negotiated handoffs, and structured debate between agents.
- **Main API route groups:** `/api/agent-network`, `/api/debate`.
- **Safety boundary:** Planning/coordination only; governance-logged.

### v24 — Self-Healing Project System
- **Purpose:** Detect and propose fixes for project issues.
- **How it operates:** Runs health checks on projects and records proposed/applied fixes.
- **Main API route groups:** `/api/self-healing`.
- **Safety boundary:** Proposes fixes; no destructive autonomous changes.

### v25 — AI Company Brain
- **Purpose:** Central knowledge and decision hub.
- **How it operates:** Aggregates organization-wide context and decisions into a shared brain.
- **Main API route groups:** `/api/company-brain`.
- **Safety boundary:** Local knowledge store; governance-logged.

### v26 — Personal Device Operator / Phone Autopilot
- **Purpose:** Plan phone/device automations.
- **How it operates:** **Mock, planning-first** — drafts device-automation plans and autopilot sequences without controlling any real device.
- **Main API route groups:** `/api/device-operator`, `/api/autopilot`.
- **Safety boundary:** No real device control; mock/planning only.

### v27 — Private Training Lab
- **Purpose:** Prepare local datasets.
- **How it operates:** **Dataset preparation only** — assemble and clean local datasets.
- **Main API route groups:** `/api/training-lab`.
- **Safety boundary:** No base-model training; dataset prep only.

### v28 — Personal AI Avatar / Voice Twin
- **Purpose:** Avatar and voice persona configuration.
- **How it operates:** **Settings + shell only** — avatar/voice configuration plus a generated stylized avatar via the existing (mock-by-default) Image Agent.
- **Main API route groups:** `/api/avatar`.
- **Safety boundary:** No real voice cloning; settings/shell only.

### v29 — Real-Time Life Operating System
- **Purpose:** Personal life-planning layer.
- **How it operates:** Local planning for tasks, routines, and priorities across personal life.
- **Main API route groups:** `/api/life-os`.
- **Safety boundary:** Local planning only; governance-logged.

### v30 — Universal App Operator
- **Purpose:** Plan app automations and scaffold apps.
- **How it operates:** **Mock, planning-first** app automation plus an app-builder scaffolding studio that drafts plans rather than live integrations.
- **Main API route groups:** `/api/universal-operator`, `/api/app-builder`.
- **Safety boundary:** No live app automation; drafts/plans only.

---

## v31 to v35 Series

### v31 — AI Team Lead / Manager Mode
- **Purpose:** Manage a team of agents/people as a lead.
- **How it operates:** **Team members** (with roles), **assignments** (work routed to members), **standups** (status capture), and **sprint review**; a dashboard rolls up workload and progress.
- **Main API route groups:** `/api/team-manager`.
- **Safety boundary:** Planning/coordination only; governance-logged.

### v32 — Autonomous SaaS Builder
- **Purpose:** Planning/drafting studio for a SaaS product.
- **How it operates:** Drafts **projects**, **specs**, **scaffolding plans**, and **feedback items** — all drafts; no code deployment.
- **Main API route groups:** `/api/saas-builder`, `/api/app-builder`.
- **Safety boundary:** Drafting only; no deployment or live build.

### v33 — AI Business Operator Advanced
- **Purpose:** Extend the v18 business layer with advanced operations.
- **How it operates:** A separate `/api/business-operator/*` surface adds operations **workflows** (lead_pipeline / support_triage / invoice_processing / custom with suggested next steps), **reports** (computes KPIs such as conversion rate and open cases), **KPI snapshots**, **approvals** (external_send / payment / high_risk / data_share), and an **audit** log. Reads v18 data read-only; does not duplicate it.
- **Main API route groups:** `/api/business-operator`.
- **Safety boundary:** Draft-only — approving records a decision but performs no real send/payment/CRM action.

### v34 — Legal / Compliance Intelligence Layer
- **Purpose:** Compliance checklists, sensitive-data scanning, and contract review.
- **How it operates:** **Policies**; a **sensitive-data scanner** (reuses the existing SecretScanner plus PII/PHI patterns → risk level + HIPAA warning); **contract review** (flags indemnity / auto-renew / termination / governing-law, etc.); framework **checklists** (HIPAA / GDPR / SOC2 presets); and **audit packages** assembled from governance events and findings.
- **Main API route groups:** `/api/compliance` (distinct from the pre-existing compliance admin routes).
- **Safety boundary:** Always labeled "not legal advice"; produces checklists/warnings/audit material for human review.

### v35 — AI Executive Board
- **Purpose:** Review decisions from multiple executive perspectives.
- **How it operates:** Create a **session** → generate a **review** from 8 roles (CEO / CTO / CFO / COO / Legal / Product / Marketing / Security) with risks/opportunities/costs/technical/compliance + a recommendation → cast role **votes** → produce a **report** with vote tally and board lean.
- **Main API route groups:** `/api/executive-board`.
- **Safety boundary:** Advisory only — the board reviews and recommends; it does not execute actions.

---

## v36 to v40 Capstone Series

### v36 — Autonomous Research + Innovation Lab
- **Purpose:** Local R&D workbench for research, ideas, experiments, and prototypes.
- **How it operates:** **Research items** (source + credibility + tags), **competitors** (strengths/weaknesses), **trends** (direction + evidence), **idea scoring** (impact/feasibility/novelty/risk → composite `(I+F+N)×2 − risk×1.5`, sorted high-to-low), **experiment plans** (hypothesis/method/metrics), **prototype plans** (phases/features/risks), and **reports** (top-5 ideas + counts).
- **Main API route groups:** `/api/innovation-lab`.
- **Safety boundary:** Local/manual research only — no web browsing or external scraping.

### v37 — AI Simulation World
- **Purpose:** Safe sandbox to model decisions before acting.
- **How it operates:** Create a **world** → add **personas** (user/customer/stakeholder) → create a **scenario** (business/product/project/bug/risk/launch) → **run** it with **deterministic mock scoring** (base 60, +5 per assumption, −8 per risk keyword) yielding a likely result plus risks/opportunities/failure modes. **Compare** ranks scenarios by score; **reports** average outcomes.
- **Main API route groups:** `/api/simulation-world`.
- **Safety boundary:** Deterministic mock simulation only — no real-world actions; same input → same score.

### v38 — Multi-User Organization OS
- **Purpose:** Local organization/team/workspace structure.
- **How it operates:** **Organizations**, **member profiles** (roles owner/admin/manager/contributor/viewer, each mapped to a default permission set), **member updates** (changing role re-derives permissions), **custom roles**, **workspace links**, and an **activity log**; the dashboard shows role distribution. Records are flagged as local (`is_local_record` / `is_local_profile`).
- **Main API route groups:** `/api/organization-os`.
- **Safety boundary:** Local organization records only — no production authentication or real user login.

### v39 — AI Hardware / Always-On Companion
- **Purpose:** Device-readiness and session-planning layer.
- **How it operates:** **Device profiles** (mic/speaker/local-processing flags), **companion-mode settings** (disabled / push_to_talk_ready / local_only_ready), **readiness checks** (checklist → ready/partial/not_ready), and **sessions** (always `user_activated`). The settings endpoint **locks safety invariants** — `background_listening`, `wake_word_listener`, and `microphone_recording` are forced `False` regardless of input.
- **Main API route groups:** `/api/hardware-companion`.
- **Safety boundary:** Readiness/planning only — no mic recording, no wake-word listener, no hardware access; always requires explicit user activation.

### v40 — EvolveAgent Operating Layer
- **Purpose:** Capstone governed-orchestration dashboard across all systems (v15–v39).
- **How it operates:** A **capability map** of 10 groups (Platform / Organization / Business / Personal / Agents / Automation / Intelligence / Research / Compliance / Companion), each marked active by whether its data exists; **readiness snapshots** (% of active groups + governance/blocked counts); cross-system **recommendations**; **safety boundaries**; a **final report**; and an **audit** trail.
- **Main API route groups:** `/api/operating-layer`.
- **Safety boundary / disclaimer:**

  > This is not AGI. It is a governed orchestration layer across existing agents, workflows, tools, memory, simulations, and dashboards.

### v41 — MCP Connector Hub
- **Purpose:** Register, configure, inspect, and safely **plan** tool connections through MCP-style connector records.
- **How it operates:** A local **connector registry** with 9 default templates (Filesystem, Git, GitHub, Linear, Context7, Playwright, Slack, Notion, Desktop Commander). Each connector has a **category**, **risk level** (low/medium/high), **mode** (read_only / approval_required / disabled), allowed/blocked actions, and required env-key *names*. **Status checks are dry/mock** and report only whether required env keys are set (true/false) — never their values. **Action planning** enforces risk/approval rules: read-only low-risk actions are auto-allowed; everything else requires approval; blocked-list and not-in-allow-list actions are refused. Every stateful action is governance-logged and recorded as a connector event. The Master Agent lightly classifies MCP/tool-connection queries (`mcp_connector_management`); analytics and a learning hook surface connector counts, planned/blocked actions, and recommendations.
- **Main API route groups:** `/api/mcp`.
- **Safety boundary:** The EvolveAgent MCP Connector Hub prepares and governs tool connections through local connector records, dry checks, approval boundaries, and audit logs. **No real MCP execution by default, no secrets exposed, no unrestricted shell, no full desktop control.** High-risk connectors (Filesystem, Playwright, Desktop Commander) stay approval-required or disabled by default.

### v42 — MCP Execution Adapter
- **Purpose:** Add a governed execution loop on top of the v41 connector planning layer.
- **How it operates:** A **request → approve → run → record** flow. `request_execution` reuses the v41 `plan_connector_action` rules to validate (blocked-list, allow-list, risk/approval): blocked actions create a non-runnable `blocked` request; read-only low-risk actions are auto-`approved`; everything else stays `pending_approval`. Approving moves a request to `approved`; running it invokes a **mock executor** that returns a simulated result and records it. Running re-validates the connector (a since-disabled connector is blocked at run time). Stored under `mcp_execution_requests.json` / `mcp_execution_results.json`; every step is governance-logged and reflected in analytics.
- **Main API route groups:** `/api/mcp/executions`, `/api/mcp/connectors/{id}/execute`.
- **Safety boundary:** Execution is always simulated (`EXECUTION_MODE = "mock"`) — **no real MCP server, network call, shell command, or device action, and no secrets used or returned**. Write actions always require explicit approval; blocked/disabled connectors never execute.

### v43 — MCP Read-Only Adapter
- **Purpose:** Add a real, opt-in, read-only execution path to the v42 loop — the project's first genuinely real tool execution, kept strictly safe.
- **How it operates:** A sandboxed adapter (`mcp_readonly_adapter.py`) that the execution service consults during `run_execution`. It executes for real **only when all hold**: env opt-in `MCP_REAL_READONLY` is set, the connector is enabled, the request is approved, and the action is on the allow-list (`git_current_branch`, `git_list_branches`, `fs_list_directory`, `fs_file_metadata`). Git actions read `.git/HEAD` and `refs/heads` as plain files (no subprocess); filesystem actions return directory listings / file metadata (names and sizes only, never contents). Anything else falls back to the v42 mock. `GET /api/mcp/adapter/status` exposes the opt-in state, allow-list, and sandbox root.
- **Main API route groups:** `/api/mcp/adapter/status` (plus the v42 execution routes).
- **Safety boundary:** **Standard-library only — no shell/subprocess, no network, no writes/deletes, no secrets, and never returns file contents.** Sandboxed to the repo root with traversal + absolute-path blocking and a sensitive-name denylist (`.env`, keys, `.ssh`, `.git/config`, …); dotfiles and sensitive names are hidden from listings. Opt-in defaults off, so default behaviour is identical to v42 (mock).

### v44 — MCP Approvals Inbox
- **Purpose:** A single, prioritized place to review and act on everything on the MCP surface awaiting human approval.
- **How it operates:** Aggregates the v42 execution requests in `pending_approval` status, enriches each with connector name, risk level, and age, and sorts them **high-risk first, then oldest first** (with a risk-level filter). Approve/reject **delegate to `MCPExecutionService`** (which does the governance logging and status transitions), so the inbox holds no independent execution power. Derives entirely from existing execution state — no new storage.
- **Main API route groups:** `/api/mcp/inbox` (+ `/summary`, `/{item_id}/approve`, `/{item_id}/reject`).
- **Safety boundary:** Read/triage + delegated decisions only — it can approve or reject an existing pending request but adds no new action, execution, or bypass; all decisions flow through the governed execution service and are logged.

### v45 — MCP Policy Engine
- **Purpose:** Declarative, tighten-only guardrails over which connector actions may even be planned.
- **How it operates:** **Deny** policies (the only effect) match on connector slug / action / risk level — each supporting a `*` wildcard — plus an optional `except_actions` carve-out (e.g. "deny all Filesystem actions except `fs_list_directory`"). The engine is injected into `MCPConnectorService.plan_connector_action` and evaluated *first*: a match returns a blocked plan and a governance-logged denial; a non-match falls through to the existing v41 checks. With no policies (default), behavior is identical to v44. CRUD + `evaluate` at `/api/mcp/policies`.
- **Main API route groups:** `/api/mcp/policies` (+ `/summary`, `/evaluate`, `/{policy_id}`).
- **Safety boundary:** **Tighten-only** — policies can only add blocks, never grant access (no "allow" effect exists). Local records; evaluated before planning; denials governance-logged.

### v46 — MCP Audit & Replay
- **Purpose:** A read-only, auditable view of the MCP surface plus a safe dry replay.
- **How it operates:** `MCPAuditService` builds a unified timeline from connector events, execution requests/results, and MCP-tagged governance events (filter by connector / event type / since), and exports it as markdown or JSON. **Replay** re-derives what a past execution request would do today via `plan_connector_action` (dry) — it never executes, stores a replay record, and logs a governance event.
- **Main API route groups:** `/api/mcp/audit` (+ `/summary`, `/export`, `/replays`, `/replay`).
- **Safety boundary:** Read-only aggregation + dry replay; no real execution, no secrets. Only write is the stored replay artifact.

### v71 — Smart Context Engine
- **Purpose:** Better context selection before every answer.
- **How it operates:** `SmartContextService` is a read-only **context planner**: given a query + workspace, it scores candidate **memory / files / goals** by keyword overlap, gives a **selection reason** per item, enforces a **context budget** (character cap), **removes duplicate** context, and **filters out sensitive content** (emails, card-like numbers, key-like tokens, secret assignments) so it never enters the context. It returns a Developer-Mode **context trace** of what was included and excluded and why. It previews/plans context — it does not change the run pipeline. Governance-logged.
- **Main API route groups:** `/api/context` (+ `/context/plan`, `/context/summary`).
- **Safety boundary:** Read-only planning; sensitive content is filtered out and never included; nothing is executed; governance-logged.

### v70 — Workspace Operating System 2.0
- **Purpose:** Make each workspace feel like its own AI OS.
- **How it operates:** `WorkspaceOSService` builds a **per-workspace, read-only overview**: a workspace **dashboard**, a **memory graph** (memory nodes + knowledge-link edges), **feature-usage** counts across the workspace's collections, its **agents**, its **reports**, a recent **timeline** (via the v63 Activity Timeline scoped to the workspace), and a derived **health score** (completeness of goals/memory/agents → healthy/developing/sparse). It reads existing local state only, scoped to one workspace, and is governance-logged.
- **Main API route groups:** `/api/workspace-os` (+ `/{workspace_id}/dashboard`, `/summary`).
- **Safety boundary:** Read-only, workspace-scoped aggregation; no writes/actions; governance-logged.

### v69 — Unified Notifications Inbox 2.0
- **Purpose:** Make alerts actionable.
- **How it operates:** `NotificationsInboxService` aggregates live signals into one actionable inbox — **approval alerts**, **failed/blocked run alerts** (from the governance log), **provider-fallback alerts**, **scheduled-task reminders**, and **health warnings**. Each item has a **severity**, a **link to its source route**, and a stable key so **generation is idempotent** (an unresolved item is never duplicated). Items can be **marked resolved** and are **grouped by severity**. It is **additive** to the v56 Notifications Center (distinct `/api/notifications-inbox`), read-only against source data; generation/resolution are governance-logged.
- **Main API route groups:** `/api/notifications-inbox` (+ `/generate`, `/summary`, `/{id}/resolve`).
- **Safety boundary:** Read-only aggregation; idempotent generation; additive to v56; governance-logged.

### v68 — Real Provider Control Center 2.0
- **Purpose:** Cleanly manage OpenAI / Claude / Gemini / Mistral / local providers.
- **How it operates:** `ProviderControlService` gives a **read-only readiness dashboard** per provider (is a required env key set? boolean only), editable **model-per-task** and **real/mock-per-capability** preferences, a **fallback policy** (real when key set + mode real, else local/mock), a **cost estimate** aggregated from the v50 usage ledger, and per-provider **latency** estimates. **API key safety checks report booleans only** — a key's value is never read, logged, or returned. Preference changes are governance-logged; real calls remain env-gated.
- **Main API route groups:** `/api/provider-control` (+ `/dashboard`, `/summary`, `/key-check`, PATCH).
- **Safety boundary:** Boolean-only key readiness (no secret values); preferences are local; real calls stay env-gated; governance-logged.

### v67 — Settings Center
- **Purpose:** A central place for local configuration.
- **How it operates:** `SettingsService` stores user **preferences** as a single local document across categories — **provider** (default model, prefer-mock), **modes** (developer/deep defaults), **feature toggles**, a **safety preference**, **workspace defaults**, **voice** (spoken answers, push-to-talk), and **theme**. Every update is validated against an allow-list; unknown categories/keys and **any secret-like key** (containing key/token/secret/password/credential) are **rejected**. The hard safety boundaries are surfaced as **read-only/enforced** and cannot be disabled. Supports **export/import** (secrets excluded) and **reset-to-defaults**. Changes are governance-logged.
- **Main API route groups:** `/api/settings` (+ `/settings/reset`, `/settings/export`, `/settings/import`).
- **Safety boundary:** Preferences only — **no secret values are ever stored**; hard safety boundaries stay enforced and read-only; a safety preference can only tighten; governance-logged.

### v66 — Demo Mode / Portfolio Mode 2.0
- **Purpose:** Make the app impressive for interviews and GitHub, and safe to demo.
- **How it operates:** `DemoService` provides a **one-click demo script** (ordered beats with the prompt/route to show), a **guided walkthrough**, an **auto-open feature sequence**, a refreshed **resume-bullet** set, and a **project case-study export** (markdown) — all read-only, generated content. It can **seed a demo-safe sample workspace** (a workspace + goals + an idea, every record tagged `demo_seed=true` and tracked in a seed log) and **reset demo data** — reset removes **only** demo-tagged records it created and leaves user data untouched. Seeding/reset are explicit and governance-logged.
- **Main API route groups:** `/api/demo` (+ `/script`, `/walkthrough`, `/feature-sequence`, `/resume-bullets`, `/case-study`, `/summary`, `/seed`, `/reset`).
- **Safety boundary:** Demo content is read-only; sample data is **scoped and reversible** — reset never deletes user data, only `demo_seed`-tagged records; governance-logged.

### v65 — Feature Registry + Capability Map 3.0
- **Purpose:** Make all 60+ versions discoverable.
- **How it operates:** `FeatureRegistryService` holds a **canonical registry** of every major feature with its owning **service**, primary **route**, **category**, and **status tags** (active / demo-safe / mock / needs-config). It supports **feature search**, status/category filters, a **route → feature map** (Developer-Mode route map), a **summary** (counts by category/status), and a **"try this feature"** descriptor that hands back the route to open. Read-only; governance-logged.
- **Main API route groups:** `/api/features` (+ `/features/route-map`, `/features/summary`, `/features/{key}/try`).
- **Safety boundary:** Read-only discovery; no writes; governance-logged.

### v64 — Dashboard Home 2.0
- **Purpose:** Replace scattered panels with one professional homepage.
- **How it operates:** `DashboardHomeService` assembles a single read-only overview: a **Today** snapshot (events today, pending approvals, upcoming tasks, health status), the **active workspace** summary, **pending approvals** (business + MCP), **recent runs/routes**, **system health** (reusing the v49 monitor + top recommendations), **upcoming tasks** (scheduled + Life OS), rule-based **suggested next actions**, and **quick-launch cards** to every major surface. It only reads existing local state — nothing is created or executed — and is governance-logged.
- **Main API route groups:** `/api/home`.
- **Safety boundary:** Read-only aggregation; no writes/actions; governance-logged.

### v63 — Unified Activity Timeline
- **Purpose:** Show everything the OS has done, in one place.
- **How it operates:** `ActivityTimelineService` merges events from the governance log, Master Agent routes, goals, files, reports (portfolio + business), memory, MCP tool executions, and approvals into a single **chronological** timeline (newest first). Filterable by **workspace, type, actor, status, and date**; each event can be **expanded** for detail (title, status, actor, source collection, timestamp); governance events are flagged as **governance-linked**. The whole timeline can be **exported** as markdown or JSON. Strictly read-only, no secrets. Views are governance-logged.
- **Main API route groups:** `/api/activity` (+ `/activity/summary`, `/activity/export`).
- **Safety boundary:** Read-only aggregation of existing local events; no writes; secrets excluded; governance-logged.

### v62 — Global Search Across Everything
- **Purpose:** One search bar for the whole OS.
- **How it operates:** `GlobalSearchService` runs a **read-only** keyword search across a curated set of local collections — chats, messages, files, goals, agents, memory, workflows (playbooks), reports (portfolio + business), simulations, schedules, ideas, and documents — scoring by keyword overlap and returning ranked results with a short **preview**, the **source collection** (a Developer-Mode source trace), workspace, and timestamp. Results can be **filtered by type, workspace, and date (`since`)**, and any result can seed the composer via **"use as context."** It never mutates data and excludes secrets, governance logs, and analytics. Searches are governance-logged.
- **Main API route groups:** `/api/search` (+ `/search/sources`).
- **Safety boundary:** Strictly read-only local search; no writes; secrets/governance/analytics excluded; governance-logged.

### v61 — Unified Command Router 2.0
- **Purpose:** Make the Master Agent route every request more reliably, and make each routing decision explainable and measurable.
- **How it operates:** `MasterAgentService` now scores each candidate domain and derives a normalized **confidence**, an explicit **"why this route"** explanation (the keywords that matched), and a **suggested workflow/tool to reach for before execution**. When no capability matches strongly (confidence below a threshold), it uses a **safe fallback route** (Research & Retrieval) instead of silently guessing a specific system. Users can rate a route (correct / wrong) via feedback, which drives **route-accuracy analytics** (accuracy %, rated count, average confidence, fallback count). All additions are backward-compatible — the existing route response only gains fields. A **"Why this route?"** view is surfaced in the Simple-Mode hero and the Developer-Mode Master Agent panel.
- **Main API route groups:** `/api/master-agent` (+ `/route/{run_id}/feedback`; existing `/route`, `/capabilities`, `/summary` extended).
- **Safety boundary:** Read-only routing + planning-first (unchanged v60.1 contract — risky actions still always require approval); feedback is a rating only and takes no action; governance-logged.

### v60.1 — Master Agent Voice Console
- **Purpose:** Turn the whole platform into a single AI you talk to — one top-level surface that routes any request across v1–v60.
- **How it operates:** `MasterAgentService` classifies a spoken or typed request against a capability registry (11 domains spanning coding, research, project, business, compliance, personal, innovation, MCP, approvals, health, and playbooks), produces an answer via the existing run pipeline, and returns **Answer + Sources + Follow-ups** alongside **task-aware MCP suggestions** with key-readiness (booleans only — never secret values). The UI is a clean **AI-native hero**: **push-to-talk voice input** (user-activated, no wake word / no recording), **spoken answers** via the browser's speech synthesis, a **`mcp:` prefix** that routes tool-connection requests to the connector hub, and a **CLI palette** of governed `/`-commands for command-style interaction. It is **planning-first and approval-gated** — risky action classes (send / pay / delete / deploy / external post) are always held for human approval and can never be auto-executed by a client flag. Every route is governance-logged.
- **Main API route groups:** `/api/master-agent` (+ `/route`, `/capabilities`, `/summary`).
- **Safety boundary:** Read-only routing + planning-first orchestration; no unrestricted shell; risky actions require approval; secret key readiness is boolean-only; not AGI and not a retrained model — its "tuning" is an explicit capability registry over the existing systems.

### v60 — EvolveAgent OS 2.0 (capstone)
- **Purpose:** A single unified command center over every system built across v1–v59, plus a final platform scorecard and report.
- **How it operates:** `EvolveAgentOS2Service` indexes ~30 major systems grouped by domain (Core, Project & Portfolio, Business, Personal & Org, Research & Simulation, MCP Arc, Ops & Observability), marking each active-by-data with its API route and record count. It reuses the v55 Operating Layer 2.0 scorecard and the v49 health monitor for a live grade, exposes milestone stats (60 versions), and can persist a governance-logged snapshot or generate a final platform report. It reads existing local state only and takes no action beyond storing the snapshot/report. It is explicitly **not AGI** — a governed orchestration layer, not an autonomous general intelligence.
- **Main API route groups:** `/api/os2` (+ `/dashboard`, `/command-center`, `/snapshots`, `/report`).
- **Safety boundary:** Read-only aggregation of local data; no shell, no external sending, no destructive actions; risky operations across the platform still require human approval and stay governance-logged.

### v59 — Data Export & Backup
- **Purpose:** Portable local backup of your content, with safe restore.
- **How it operates:** `DataExportService` reads a curated allow-list of content collections into one JSON bundle for download. Import merges the bundle back in non-destructively — appending only items whose id is not already present, never overwriting or deleting. Secret values, governance logs, and analytics are excluded. Exports and imports are governance-logged.
- **Main API route groups:** `/api/data-export` (+ `/bundle`, `/import`, `/summary`).
- **Safety boundary:** Local only — no external upload; import is non-destructive (merge, never overwrite/delete); no secrets in the bundle.

### v58 — Scheduled Tasks
- **Purpose:** Register recurring tasks without any real background execution.
- **How it operates:** `ScheduledTasksService` stores tasks (schedule + action type). There is no daemon and nothing runs on a timer; triggering a task performs a planning-first mock run (plan / note / hold-for-approval) and records the outcome. `due_tasks` computes which tasks would be due, purely informationally. Creation and triggers are governance-logged.
- **Main API route groups:** `/api/scheduled-tasks` (+ `/{id}/trigger`, `/runs`, `/summary`).
- **Safety boundary:** Planning-first — no real background scheduler or execution; risky steps require approval.

### v57 — Workspace Templates & Cloning
- **Purpose:** Reusable, preconfigured workspace setups you can clone on demand.
- **How it operates:** `WorkspaceTemplatesService` stores templates (name, description, default tags, a preset of local settings). Instantiating a template calls the existing `WorkspaceService.create_workspace` to spin up a real local workspace preconfigured from it, and increments the template's instantiation count. Creation and instantiation are governance-logged.
- **Main API route groups:** `/api/workspace-templates` (+ `/summary`, `/{id}/instantiate`).
- **Safety boundary:** Local records only — no production provisioning, no authentication.

### v56 — Notifications & Alerts Center
- **Purpose:** A local, in-app place to see and clear important platform alerts.
- **How it operates:** `NotificationsCenterService` scans signals — blocked governance actions, degraded health (from the v49 monitor), and pending-approval backlog — and turns them into notifications with a severity and a signature. Generation is idempotent (an unacknowledged notification with the same signature is not duplicated); users acknowledge to clear. Generation and acknowledgement are governance-logged.
- **Main API route groups:** `/api/notifications` (+ `/summary`, `/generate`, `/{id}/ack`).
- **Safety boundary:** In-app digest only — nothing is sent externally (no email, SMS, or push).

### v55 — EvolveAgent Operating Layer 2.0
- **Purpose:** A refreshed capstone dashboard covering the v41–v53 additions with a platform readiness & governance scorecard.
- **How it operates:** `OperatingLayerV2Service` builds an expanded 19-group capability map (each active by data presence) and a scorecard across four dimensions — capability coverage, governance (blocked ratio), health (from the v49 monitor), and approvals backlog — each graded A–F with an overall grade. Snapshots and a final report are persisted and governance-logged. The original v40 operating layer is left untouched (distinct `/api/operating-layer-2` prefix).
- **Main API route groups:** `/api/operating-layer-2` (+ `/dashboard`, `/capabilities`, `/scorecard`, `/snapshots`, `/report`).
- **Safety boundary:** Read-only aggregation + persisted snapshot; carries the "not AGI" disclaimer and the full safety-boundary list. *(v54 was folded into the v44.5 portfolio pass.)*

### v53 — Playbook Library
- **Purpose:** Save and re-run governed multi-step action sequences without executing anything.
- **How it operates:** `PlaybookLibraryService` stores playbooks of steps (plan / note / approval_required). Running a playbook is planning-first: plan steps are drafted (mock), note steps are informational, and approval_required steps are held for explicit human approval — the run records a per-step outcome and never executes. Creation and runs are governance-logged.
- **Main API route groups:** `/api/playbooks` (+ `/{id}/run`, `/runs`, `/summary`).
- **Safety boundary:** Planning-first — nothing is executed; risky steps always require approval.

### v52 — Evaluation Harness 2.0
- **Purpose:** Repeatable, regression-aware quality evaluation for agent behavior.
- **How it operates:** `EvalHarnessService` stores suites of cases (prompt, reference answer, expected keywords). Running a suite scores each case deterministically by expected-keyword coverage over its reference answer — no real LLM call — producing a scorecard with per-case scores, pass counts, and a delta vs the previous run for regression detection. Suite creation and runs are governance-logged.
- **Main API route groups:** `/api/eval-harness` (+ `/suites`, `/suites/{id}/run`, `/runs`, `/suites/{id}/regression`, `/summary`).
- **Safety boundary:** Deterministic and mock-safe — no real LLM/provider call; scores are stable and reproducible.

### v51 — Local Retrieval Layer
- **Purpose:** Ground answers in workspace documents using purely local retrieval.
- **How it operates:** `LocalRetrievalService` chunks indexed documents on sentence boundaries, tokenizes each chunk (stopword-filtered), and answers queries by keyword-overlap scoring — returning the top chunks with a citation and matched terms. Standard library only; queries are workspace-scoped. Indexing and queries are governance-logged.
- **Main API route groups:** `/api/retrieval` (+ `/documents`, `/query`, `/summary`).
- **Safety boundary:** Local-first — no external vector database, no network; chunks and scores are computed locally.

### v50 — Cost & Usage Ledger
- **Purpose:** Track API usage estimates and budgets per workspace — visibility only, never billing.
- **How it operates:** `UsageLedgerService` records usage entries (capability, units, estimated cost derived from illustrative rates when not supplied), stores per-workspace budgets, and computes an under/near/over status with warnings and a by-capability breakdown. Recording and budget changes are governance-logged.
- **Main API route groups:** `/api/usage-ledger` (+ `/summary`, `/entries`, `/budgets`).
- **Safety boundary:** Estimates and planning only — extends v11 cost visibility; no billing, charging, or payment is performed.

### v49 — Health & Readiness Monitor
- **Purpose:** One scored, read-only view of platform health and readiness.
- **How it operates:** `HealthMonitorService` derives checks from local collections — governance blocked ratio, approvals backlog, secret-key readiness, MCP connectors, and policy posture — each with an ok/warn/critical/info status, rolled into an overall score and recommendations. Snapshots are persisted and governance-logged.
- **Main API route groups:** `/api/health-monitor` (+ `/dashboard`, `/snapshots`).
- **Safety boundary:** Read-only aggregation; performs no actions, changes no state except a stored snapshot.

### v48 — Unified Approvals Center
- **Purpose:** One prioritized place to review and act on everything awaiting human approval, across every source.
- **How it operates:** `UnifiedApprovalsService` aggregates pending MCP execution requests (v42) and business-operator approval items (v33), normalizes each with a source/title/risk/age, and sorts high-risk then oldest first (with a source filter). Approve/reject delegate to the owning service (`MCPExecutionService` / `BusinessOperatorAdvancedService`), which do the logging.
- **Main API route groups:** `/api/approvals-center` (+ `/summary`, `/approve`, `/reject`) — a distinct prefix from the pre-existing `/approvals` workflow.
- **Safety boundary:** Triage + delegated decisions only; no new execution power, no bypass; each decision flows through its owning governed service.

### v47 — Secret Reference Registry
- **Purpose:** Know which secrets each connection needs and whether they are ready — without ever touching the values.
- **How it operates:** `MCPSecretRegistryService` stores references (key name, label, owner, category, optional connector slug, rotation interval). Readiness is computed from `os.environ` as a boolean; a rotation-due flag is derived from `rotation_days` + `last_rotated_at`. Registration, update, and rotate are governance-logged.
- **Main API route groups:** `/api/mcp/secrets` (+ `/summary`, `/{ref_id}`, `/{ref_id}/rotate`).
- **Safety boundary:** References only — it never stores, reads, logs, or returns a secret value; a defensive presenter strips any `value` field and exposes only key name + `is_set` boolean.

### v45.1 — MCP Hub UI
- **Purpose:** Make the multi-version MCP Hub panel usable.
- **How it operates:** Reorganized the panel into internal tabs (Connectors · Policies · Approvals · Executions · Audit) with live counts, and added CSS for the tab bar and risk badges. Frontend-only.
- **Main API route groups:** none.
- **Safety boundary:** Presentation only; no behavior change.

### v44.5 — Portfolio & Demo Pack
- **Purpose:** A consolidation and presentation pass to make the repo portfolio- and demo-ready before the v45–v55 arc.
- **How it operates:** Documentation only — synced scale numbers and the canonical one-line description across the docs; added a portfolio pack (`docs/PORTFOLIO_PACK.md`), a refreshed screenshot guide, a 5–7 minute demo script, `docs/RELEASE_NOTES_v44.md`, and `docs/DEMO_DATA_CHECKLIST.md`.
- **Main API route groups:** none — **no new execution surface**; no backend/frontend behavior change.
- **Safety boundary:** Unchanged. No code, no runtime data, no secrets — presentation and documentation only.

---

## Summary Table

| Version | Name | Main API Surface | What It Does | Safety Boundary |
|---|---|---|---|---|
| v1 | Base Conversational Agent | `/api/run`, `/api/chats` | ChatGPT-style chat core | Conversational only |
| v2 | Safe Planning & Approval-Gated Automation | `/api/approvals` | Plans, not auto-executes | No auto file writes; shell blocked |
| v3 | Agent OS Foundation | `/api/tools`, `/api/agent-jobs`, `/api/plugins` | Project Brain, tool router, jobs, kernel | Governed tool router; local plugins |
| v3.5 | UI/UX Polish | (frontend) | Jarvis-style UI, themes, onboarding | Presentation only |
| v6 | Memory Intelligence | `/api/memory` | Scored/tiered/semantic local memory | Local index, no external vector DB |
| v7.5 | Governed Tool Layer 2.0 | `/api/tools` | Tool execution history + validation | Read-only metadata; strict manifests |
| v8 / v8.5 | Demo Readiness & Provider QA | `/api/providers` | Speak/Type console; dry provider checks | Dry checks; no paid calls by default |
| v9 | Real Image API Path | `/api/images` | Real OpenAI image path + mock fallback | Opt-in; mock fallback |
| v10 | Unified Real-API Control Layer | `/api/real-api`, `/api/transcription` | Text/image/transcription readiness | Opt-in real calls; mock fallback |
| v11 / v11.5 | Cost Control & Research Agent | `/api/real-api`, `/api/research` | Cost visibility + governed research | No unrestricted browsing |
| v12.5 | Digital Twin Work Style Engine | `/api/digital-twin` | Local work-style profile | Local profile only |
| v13 | Enterprise Governance & Compliance (early) | `/api/quality`, `/api/governance` | Governance + quality gates | Governance-logged |
| v14 | Full AI Project Manager | `/api/project-manager`, `/api/goals` | Projects, tasks, goals | Planning/tracking only |
| v14.5 | Portfolio Mode | `/api/portfolio` | Multi-project portfolio view | Aggregate view only |
| v15 | EvolveAgent OS | `/api/os` | Platform-readiness/branding layer | No hosting/auth/payments |
| v16 | Multi-Agent Organization | `/api/departments` | AI departments + roles | Planning/structure only |
| v17 | Agent Workforce Marketplace | `/api/agent-marketplace` | Reusable agent-team templates | Permission profiles enforced |
| v18 | Real Business Automation Layer | `/api/business` | Leads/support/docs/proposals | Draft-only; no real sending |
| v19 | AI Chief of Staff | `/api/chief-of-staff` | Priorities, daily plan, briefings | Advisory only |
| v20 | Autonomous Business Simulator | `/api/business-simulator` | Business outcome simulations | Simulation only |
| v21 | Multi-Modal Real-World Agent | `/api/multimodal` | Text/image/audio orchestration | Mock fallback; opt-in real |
| v22 | Industry Workflow Modes | `/api/industry-modes` | Industry-tuned workflow templates | Template-driven planning |
| v23 | Agent-to-Agent Network | `/api/agent-network`, `/api/debate` | Agent contracts/handoffs/debate | Coordination planning only |
| v24 | Self-Healing Project System | `/api/self-healing` | Health checks + proposed fixes | No destructive auto-changes |
| v25 | AI Company Brain | `/api/company-brain` | Org-wide knowledge/decision hub | Local knowledge store |
| v26 | Personal Device Operator / Phone Autopilot | `/api/device-operator`, `/api/autopilot` | Device-automation plans | No real device control |
| v27 | Private Training Lab | `/api/training-lab` | Local dataset preparation | No base-model training |
| v28 | Personal AI Avatar / Voice Twin | `/api/avatar` | Avatar/voice configuration | No real voice cloning |
| v29 | Real-Time Life Operating System | `/api/life-os` | Personal life planning | Local planning only |
| v30 | Universal App Operator | `/api/universal-operator`, `/api/app-builder` | App automation plans + scaffolding | No live app automation |
| v31 | AI Team Lead / Manager Mode | `/api/team-manager` | Members/assignments/standups/sprint | Planning/coordination only |
| v32 | Autonomous SaaS Builder | `/api/saas-builder`, `/api/app-builder` | Projects/specs/scaffolding drafts | Drafting only; no deployment |
| v33 | AI Business Operator Advanced | `/api/business-operator` | Workflows/reports/KPIs/approvals/audit | Draft-only; no real send/payment |
| v34 | Legal / Compliance Intelligence Layer | `/api/compliance` | Policies/scans/contracts/checklists/audits | "Not legal advice"; human review |
| v35 | AI Executive Board | `/api/executive-board` | Multi-role decision review + votes | Advisory only; no execution |
| v36 | Autonomous Research + Innovation Lab | `/api/innovation-lab` | Research/competitors/ideas/experiments | No web browsing/scraping |
| v37 | AI Simulation World | `/api/simulation-world` | Personas/scenarios/deterministic runs | Mock simulation; no real actions |
| v38 | Multi-User Organization OS | `/api/organization-os` | Orgs/members/roles/workspaces/activity | Local records; no production auth |
| v39 | AI Hardware / Always-On Companion | `/api/hardware-companion` | Device readiness + session planning | No mic/wake-word/hardware access |
| v40 | EvolveAgent Operating Layer | `/api/operating-layer` | Capability map/snapshots/recs/report | Not AGI — governed orchestration |
| v41 | MCP Connector Hub | `/api/mcp` | Connector registry/templates/dry checks/action planning | No real MCP exec; no secrets; no shell; no desktop control |
| v42 | MCP Execution Adapter | `/api/mcp/executions` | Approval-gated request→approve→run→record loop | Mock executor only; no real exec/network/shell; no secrets |
| v43 | MCP Read-Only Adapter | `/api/mcp/adapter/status` | Opt-in real read-only exec (git/fs), mock fallback | Stdlib only; no shell/network/writes/secrets; sandboxed; opt-in |
| v44 | MCP Approvals Inbox | `/api/mcp/inbox` | Prioritized queue of pending approvals; approve/reject | Triage + delegated decisions only; no new execution power |
| v45 | MCP Policy Engine | `/api/mcp/policies` | Deny-only policies evaluated before planning | Tighten-only; never grants access; governance-logged |
| v45.1 | MCP Hub UI | (frontend) | Tabbed MCP Hub panel + risk badges | Presentation only; no behavior change |
| v46 | MCP Audit & Replay | `/api/mcp/audit` | Read-only timeline + export + dry replay | No real execution; read-only; stored replay artifact only |
| v47 | Secret Reference Registry | `/api/mcp/secrets` | Key-reference catalog + readiness + rotation | References only; never stores/returns secret values |
| v48 | Unified Approvals Center | `/api/approvals-center` | One prioritized queue across all approval sources | Triage + delegated decisions only; no new execution power |
| v49 | Health & Readiness Monitor | `/api/health-monitor` | Read-only scored health dashboard + snapshots | Read-only aggregation; no actions taken |
| v50 | Cost & Usage Ledger | `/api/usage-ledger` | Usage estimates + per-workspace budgets | Estimates only; no billing/charge/payment |
| v51 | Local Retrieval Layer | `/api/retrieval` | Local chunking + keyword retrieval with citations | Local-first; no external vector DB or network |
| v52 | Evaluation Harness 2.0 | `/api/eval-harness` | Repeatable suites/scorecards + regression tracking | Deterministic, mock-safe; no real LLM call |
| v53 | Playbook Library | `/api/playbooks` | Reusable multi-step playbooks, run planning-first | Nothing executed; risky steps require approval |
| v55 | Operating Layer 2.0 | `/api/operating-layer-2` | Expanded capability map + readiness/governance scorecard | Read-only; not AGI; v40 layer untouched |
| v56 | Notifications & Alerts Center | `/api/notifications` | Local digest of platform alerts; acknowledge | In-app only; no email/SMS/push |
| v57 | Workspace Templates & Cloning | `/api/workspace-templates` | Reusable workspace presets + instantiate | Local records only; no production provisioning/auth |
| v58 | Scheduled Tasks | `/api/scheduled-tasks` | Local scheduled-task registry; planning-first triggers | No daemon/timer execution; risky steps need approval |
| v59 | Data Export & Backup | `/api/data-export` | Local JSON bundle export + non-destructive import | Local only; no upload; merge-only; no secrets in bundle |
| v60 | EvolveAgent OS 2.0 (capstone) | `/api/os2` | Unified command center over v1–v59 + platform scorecard/report | Read-only local aggregation; not AGI; approvals + governance preserved |
| v60.1 | Master Agent Voice Console | `/api/master-agent` | Single top-level AI routing across v1–v60; AI-native hero, push-to-talk voice, spoken answers, `mcp:`/CLI palette, task-aware MCP suggestions | Planning-first; approval-gated risky actions; boolean-only key readiness; governance-logged; not AGI |
| v61 | Unified Command Router 2.0 | `/api/master-agent` | Route confidence + "why this route" explanation, suggested workflow before execution, safe fallback when uncertain, route-accuracy feedback/analytics | Read-only routing; planning-first unchanged; feedback is rating-only; governance-logged |
| v62 | Global Search Across Everything | `/api/search` | One read-only keyword search across chats/files/goals/agents/memory/workflows/reports/simulations/schedules; type/workspace/date filters; preview; source trace; use-as-context | Strictly read-only; no writes; secrets/governance/analytics excluded; governance-logged |
| v63 | Unified Activity Timeline | `/api/activity` | Chronological merge of runs/approvals/tool-executions/memory/files/reports/goals; type/workspace/actor/status/date filters; expandable detail; markdown/JSON export; governance-linked | Read-only aggregation; no writes; secrets excluded; governance-logged |
| v64 | Dashboard Home 2.0 | `/api/home` | One homepage: Today overview, active workspace, pending approvals, recent runs, system health, upcoming tasks, suggested actions, quick-launch cards | Read-only aggregation; no writes/actions; governance-logged |
| v65 | Feature Registry + Capability Map 3.0 | `/api/features` | Canonical searchable registry of every feature (service/route/category/status), route→feature map, "try this feature" launcher | Read-only discovery; no writes; governance-logged |
| v66 | Demo Mode / Portfolio Mode 2.0 | `/api/demo` | One-click demo script, walkthrough, feature sequence, resume bullets, case-study export; demo-safe seed + scoped reset | Read-only content; sample data scoped/reversible; reset only removes demo-tagged records; governance-logged |
| v67 | Settings Center | `/api/settings` | Central local preferences (provider/modes/features/safety/workspace/voice/theme), allow-list validated, export/import, reset | No secret values stored; secret-like keys rejected; hard safety enforced read-only; governance-logged |
| v68 | Real Provider Control Center 2.0 | `/api/provider-control` | Provider readiness dashboard, model-per-task + real/mock-per-capability prefs, cost estimate, latency stats, fallback policy, boolean-only key checks | Boolean-only key readiness; real calls env-gated; no secrets exposed; governance-logged |
| v69 | Unified Notifications Inbox 2.0 | `/api/notifications-inbox` | Actionable inbox: approval/failed-run/provider-fallback/reminder/health alerts, severity grouping, mark-resolved, source links, idempotent generation | Read-only aggregation; additive to v56; governance-logged |
| v70 | Workspace Operating System 2.0 | `/api/workspace-os` | Per-workspace dashboard: memory graph, feature usage, agents, reports, timeline, health score | Read-only workspace-scoped aggregation; no writes; governance-logged |
| v71 | Smart Context Engine | `/api/context` | Context planner: memory/file/goal selection with reasons, budget control, dedup, sensitive-content filtering, context trace | Read-only preview; sensitive content filtered out; nothing executed; governance-logged |
| v44.5 | Portfolio & Demo Pack | (docs only) | Consolidation: portfolio pack, screenshots, demo, release notes | No new code/exec surface; docs only; safety unchanged |
