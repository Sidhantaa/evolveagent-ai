# EvolveAgent AI — Final Checklist (current completed: v81 Permission System 3.0 · v45.1 MCP Hub UI)

EvolveAgent OS is a local-first, workspace-aware multi-agent AI platform with governed automation, plugins, analytics, evaluation, and portfolio management.

## v36–v40 checklist

- [x] **v36 — Innovation Lab:** research/competitors/trends/ideas/experiments/prototypes/reports; local-only; governance-logged.
- [x] **v37 — Simulation World:** worlds/personas/scenarios/run/compare/reports; deterministic mock; no real-world actions.
- [x] **v38 — Organization OS:** orgs/members/roles/permissions/workspace-links/activity; local records only, **no production auth**.
- [x] **v39 — Hardware Companion:** devices/settings/readiness/sessions; **no mic recording, no wake-word, no hardware access**.
- [x] **v40 — Operating Layer:** capability map / snapshots / recommendations / report / audit; **disclaimer visible (not AGI)**; safety boundaries surfaced.
- [x] **v41 — MCP Connector Hub:** connector registry / 9 default templates / risk levels / read-only vs approval-required modes / env-key readiness (booleans only) / dry status checks / action planning / governance + connector-event logs; **no real MCP execution, no secrets exposed, no unrestricted shell, no full desktop control**; high-risk connectors approval-required or disabled by default.
- [x] **v42 — MCP Execution Adapter:** request → approve → run → record loop / reuses v41 planning for validation / read-only low-risk auto-approved / writes require approval / **mock executor only (`EXECUTION_MODE = "mock"`, no real MCP/network/shell/device, no secrets)** / run-time re-validation / governance-logged / analytics.
- [x] **v43 — MCP Read-Only Adapter:** opt-in (`MCP_REAL_READONLY`) real read-only executor / allow-list (git_current_branch, git_list_branches, fs_list_directory, fs_file_metadata) / **stdlib only — no shell/network/writes/secrets, never returns file contents** / sandboxed to repo root with traversal + denylist / mock fallback when opt-in off / approval-gated / governance-logged; v42 mock behaviour unchanged by default.
- [x] **v44 — MCP Approvals Inbox:** unified prioritized queue of pending MCP approvals / enriched with connector name + risk + age / sorted high-risk & oldest first / risk filter / approve+reject **delegate to the governed execution service** (no new execution power) / analytics / MCP Hub panel section.
- [x] **v45 — MCP Policy Engine:** declarative **deny-only** policies evaluated before planning / match connector slug + action + risk with `*` wildcards + `except_actions` carve-out / **tighten-only (never grants access)** / wired into plan_connector_action / no-policy default is unchanged behavior / CRUD + evaluate + summary / governance-logged / analytics / MCP Hub Policies section.
- [x] **v45.1 — MCP Hub UI:** MCP Hub panel reorganized into internal tabs (Connectors/Policies/Approvals/Executions/Audit) with live counts + styled risk badges; frontend-only, no behavior change.
- [x] **v46 — MCP Audit & Replay:** read-only unified timeline (connector events + executions + MCP governance) / filters / markdown+JSON export / **dry replay** re-derives a request's plan today without executing / stored replay record + governance-logged / analytics / MCP Hub Audit tab.
- [x] **v47 — Secret Reference Registry:** catalog of required secret/env keys / readiness (set/unset booleans) / owner + category + rotation reminders / **never stores/reads/logs/returns secret values** / register + update + rotate / governance-logged / analytics / MCP Hub Secrets tab.
- [x] **v48 — Unified Approvals Center:** aggregates MCP-execution + business-operator pending approvals into one prioritized queue / source filter / high-risk & oldest first / approve+reject **delegate to owning service** (no new execution power) / `/api/approvals-center` (distinct from existing `/approvals`) / analytics / own Developer-Mode panel.
- [x] **v49 — Health & Readiness Monitor:** read-only scored dashboard (governance/approvals-backlog/secret-readiness/connectors/policies) / per-check ok/warn/critical + overall score + recommendations / persisted snapshots / governance-logged / analytics / Health & Readiness panel; **no actions taken**.
- [x] **v50 — Cost & Usage Ledger:** usage estimate entries (mock/real) / per-workspace budgets / under/near/over status + warnings / by-capability breakdown / governance-logged / analytics / Cost & Usage panel; **estimates only, no billing/charge/payment**.
- [x] **v51 — Local Retrieval Layer:** local chunking of workspace docs / keyword-overlap query scoring / citations + matched terms / workspace isolation / **stdlib only — no external vector DB, no network** / governance-logged / analytics / Local Retrieval panel.
- [x] **v52 — Evaluation Harness 2.0:** repeatable eval suites + scorecards / **deterministic mock-safe scoring (no real LLM)** / per-case matched-keyword scores / pass counts / **regression tracking across runs** / governance-logged / analytics / Evaluation Harness panel.
- [x] **v53 — Playbook Library:** reusable multi-step playbooks (plan/note/approval_required steps) / **planning-first runs — nothing executed** / risky steps held for approval / per-step outcome records / governance-logged / analytics / Playbook Library panel.
- [x] **v55 — Operating Layer 2.0:** expanded 19-group capability map across v41–v53 / **readiness & governance scorecard** (coverage/governance/health/approvals → grades + overall) / snapshots + final report / disclaimer (not AGI) / v40 layer untouched / governance-logged / analytics / Operating Layer 2.0 panel. *(v54 folded into v44.5.)*
- [x] **v56 — Notifications & Alerts Center:** local digest of governance-block/health/approvals-backlog signals / severity + type / **idempotent generation** / acknowledge / summary / governance-logged / analytics / Notifications panel; **no email/SMS/push — in-app only**.
- [x] **v57 — Workspace Templates & Cloning:** reusable workspace templates (name/tags/preset) / **instantiate → creates a real local workspace** / instantiation count / governance-logged / analytics / Workspace Templates panel; **local records only, no production provisioning/auth**.
- [x] **v58 — Scheduled Tasks:** local scheduled-task registry (manual/hourly/daily/weekly) / **planning-first triggers — no daemon, no timer execution** / risky steps held for approval / due = informational / enable-disable / run history / governance-logged / analytics / Scheduled Tasks panel.
- [x] **v59 — Data Export & Backup:** export curated content collections to a downloadable JSON bundle / import back **non-destructively (merge by id)** / **local only, no external upload** / excludes secrets/governance/analytics / in-browser download / governance-logged / analytics / Data Export panel.
- [x] **v60 — EvolveAgent OS 2.0 (capstone):** unified command center indexing every system across v1–v59 (grouped by domain, active-by-data with route + record counts) / live platform scorecard (reuses v55 grade + v49 health) / milestone stats / governance-logged snapshot + final report / **read-only aggregation, not AGI** / analytics / EvolveAgent OS 2.0 panel.
- [x] **v60.1 — Master Agent Voice Console:** Master Agent is the single top-level routing surface across v1–v60 / clean AI-native hero / **push-to-talk voice input** (user-activated, no wake word/recording) / **spoken answers** via browser speech synthesis / **`mcp:` prefix** routes tool-connection requests / **CLI palette** of governed `/`-commands / **task-aware MCP suggestions** (key-readiness booleans, never values) / Answer + Sources + Follow-ups / **planning-first, approval-gated** (risky send/pay/delete/deploy always held for approval; client flag can't bypass) / governance-logged / analytics / `/api/master-agent`.
- [x] **v61 — Unified Command Router 2.0:** Master Agent route **confidence** + **"why this route"** explanation (matched keywords) / **suggested workflow before execution** / **safe fallback route when uncertain** (no silent guessing) / **route-accuracy feedback** (correct/wrong) + analytics (accuracy %, avg confidence, fallback count) / **backward-compatible** (response only gains fields) / hero + Developer-Mode panel surfacing / **planning-first & approval-gate unchanged** / governance-logged / `/api/master-agent/route/{id}/feedback`.
- [x] **v62 — Global Search Across Everything:** one **read-only** keyword search across 13 local collections (chats/messages/files/goals/agents/memory/workflows/reports/simulations/schedules/ideas/documents) / **type + workspace + date filters** / ranked results with **preview** + **source-collection trace** / **"use as context"** seeds the composer / **excludes secrets/governance/analytics** / no writes / governance-logged / analytics / Global Search Developer-Mode panel / `/api/search`.
- [x] **v63 — Unified Activity Timeline:** chronological merge (newest-first) of governance events, routes, goals, files, reports, memory, tool executions, and approvals / **type + workspace + actor + status + date filters** / **expandable** event detail / **governance-linked** flag / **markdown + JSON export** / read-only, secrets excluded / governance-logged / analytics / Activity Timeline Developer-Mode panel / `/api/activity`.
- [x] **v64 — Dashboard Home 2.0:** one homepage overview — **Today** snapshot (events/approvals/upcoming/health) / active workspace summary / pending approvals (business + MCP) / recent runs / **system health** (reuses v49) / upcoming tasks (scheduled + Life OS) / rule-based **suggested next actions** / **quick-launch cards** / read-only, no writes / governance-logged / analytics / Dashboard Home Developer-Mode panel / `/api/home`.
- [x] **v65 — Feature Registry + Capability Map 3.0:** canonical registry of every feature (name/version/**service**/**route**/**category**/**status tags**: active/demo-safe/mock/needs-config) / **feature search** + status/category filters / **route → feature map** / **summary** (counts by category & status) / **"try this feature"** launcher returning the route to open / read-only / governance-logged / analytics / Feature Registry Developer-Mode panel / `/api/features`.
- [x] **v66 — Demo / Portfolio Mode 2.0:** **one-click demo script** / guided walkthrough / auto-open **feature sequence** / refreshed **resume bullets** / **case-study export** (markdown) / **demo-safe sample workspace** seed (records tagged `demo_seed=true`, tracked in seed log) / **scoped reset** removing only demo-tagged records (**user data untouched**) / read-only content / governance-logged / analytics / Demo/Portfolio Developer-Mode panel / `/api/demo`.
- [x] **v67 — Settings Center:** central local **preferences** (provider / modes / features / safety / workspace defaults / voice / theme) as one document / **allow-list validation** (unknown categories/keys + **secret-like keys rejected**) / **no secret values stored** / hard safety boundaries surfaced **enforced read-only** / **export/import** (secrets excluded) + **reset-to-defaults** / governance-logged / analytics / Settings Center Developer-Mode panel / `/api/settings`.
- [x] **v68 — Real Provider Control Center 2.0:** **readiness dashboard** for OpenAI/Claude/Gemini/Mistral/local (env-key set? **boolean only**) / **model-per-task** + **real/mock-per-capability** preferences / **cost estimate** (from v50 ledger) / **latency** stats / **fallback policy** / **API key safety checks report booleans only — values never read/logged/returned** / real calls remain env-gated / governance-logged / analytics / Provider Control Developer-Mode panel / `/api/provider-control`.
- [x] **v69 — Unified Notifications Inbox 2.0:** actionable inbox aggregating **approval / failed-run / provider-fallback / scheduled-reminder / health** alerts / **severity** grouping / **mark-resolved** / **source-route links** / **idempotent generation** (no unresolved duplicates) / **additive to v56** (distinct `/api/notifications-inbox`) / read-only source scan / governance-logged / analytics / Notifications Inbox Developer-Mode panel.
- [x] **v70 — Workspace Operating System 2.0:** per-workspace **dashboard** / **memory graph** (nodes + knowledge-link edges) / **feature-usage** counts / workspace **agents** / workspace **reports** / scoped **timeline** (via v63) / derived **health score** (healthy/developing/sparse) / read-only, workspace-scoped / governance-logged / analytics / Workspace OS Developer-Mode panel / `/api/workspace-os`.
- [x] **v71 — Smart Context Engine:** read-only **context planner** scoring memory/files/goals by keyword overlap / **selection reason** per item / **context budget** (char cap) / **duplicate removal** / **sensitive-content filtering** (emails / card-like numbers / key-like tokens / secret assignments never included) / Developer-Mode **context trace** (selected + excluded with reasons) / does not alter run pipeline / governance-logged / analytics / Smart Context Developer-Mode panel / `/api/context`.
- [x] **v72 — Agent Quality Optimizer:** read-only analysis over run analytics + feedback / per-agent **score trends** (avg vs recent, up/down/flat) / **weak-agent detection** (recent < 60/100) / rule-based **prompt improvement suggestions** / **best agent by task type** / **regression checks** (prev vs recent window, >10% drop) / **human-feedback correlation** (ratings vs judge scores) / normalizes 0-1 & 0-100 scales / no prompt changes, nothing executed / governance-logged / analytics / Agent Quality Developer-Mode panel / `/api/agent-quality`.
- [x] **v73 — Workflow Recommendation Engine:** classifies a goal (coding/research/business/data_analysis/general) / **recommended workflow** (ordered expected steps) / **similar past runs** (Master Agent route history by keyword) / **risk level** + **approval requirements** (risky verbs / sensitive task held for approval) / **time & complexity** estimate / read-only, planning-only / governance-logged / analytics / Workflow Recommender Developer-Mode panel / `/api/workflow-recommend`.
- [x] **v74 — Personal Productivity Brain:** reads goals/life-tasks/deadlines / **priority recommendations** (overdue → priority → due date) / **daily focus** (top 3) / **blocker detection** / **overdue review** / **upcoming deadlines** / **goal-progress summary** (open goals + avg %) / "**what should I work on now?**" pick + reason / read-only, no create/complete / governance-logged / analytics / Productivity Brain Developer-Mode panel / `/api/productivity`.
- [x] **v75 — Document Intelligence 2.0:** **deterministic, local, read-only** document toolkit — **comparison** (term overlap + unique + verdict) / **resume ATS scoring** (keyword coverage, matched/missing, recommendation) / **contract/risk summary** (auto-renewal/liability/termination/non-compete/confidentiality/penalty clauses) / **CSV insight** (rows/columns/headers) / **document Q&A** (keyword sentence retrieval, no LLM) / no external model calls / governance-logged / analytics / Document Intelligence Developer-Mode panel / `/api/doc-intel`.
- [x] **v76 — Code Intelligence 2.0:** deterministic **read-only static analyzer** of submitted code — **bug-risk scan** (eval/exec, bare/broad except, hard-coded secrets, shell/subprocess, TODOs, `==None`, prints) / **suggested refactor plan** / **complexity metrics** (lines/functions/long-functions/max-line) / **API route map** / **dependency list** / **test-coverage summary** / no filesystem access, no edits, no execution / governance-logged / analytics / Code Intelligence Developer-Mode panel / `/api/code-intel`.
- [x] **v77 — Research Agent 2.0:** deterministic **local research toolkit** — **source comparison** (pairwise overlap + agreement) / **claim/evidence table** / **contradiction detection** (shared subject + differing negation) / **citation quality score** (urls/years/attribution/ids) / **research brief generator** (markdown) / **bias/risk flags** (loaded language) / no web browsing, no model calls / read-only / governance-logged / analytics / `/api/research-agent`. *(Developer-Mode panel deferred — added in a later UI pass.)*
- [x] **v78 — Business Intelligence 2.0:** read-only analytics over local business records — **KPI dashboard** (leads/proposals/win-rate) / **lead pipeline** (by stage) / **proposal tracker** (by status) / **mock revenue forecast** (illustrative deal size × stage probability, never real money) / **risk register** (project + derived pipeline risks) / **business report** + **executive summary** (markdown) / read-only, no billing/payment / governance-logged / analytics / `/api/business-intel`. *(Developer-Mode panel deferred to a later UI pass.)*
- [x] **v79 — Meeting Intelligence 2.0:** deterministic read-only extraction over a submitted transcript — **summary** / **decisions** / **action items** + **owners** / **follow-up drafts** (never sent) / **timeline** (time cues) / **propose goal+tasks** (planning-only, nothing created) / no model call / governance-logged / analytics / `/api/meeting-intel`. *(Developer-Mode panel deferred to a later UI pass.)*
- [x] **v80 — Multi-Agent Collaboration 2.0:** deterministic read-only analysis of agent contributions (role+position) — **conversation view** / **consensus summary** (majority-shared terms) / **disagreement notes** (low overlap or opposing negation) / **reviewer/auditor pass** (flags no-evidence contributions) / **final decision** (most central position) + **rationale** / no model call, nothing executed / governance-logged / analytics / `/api/collaboration`. *(Developer-Mode panel deferred to a later UI pass.)*
- [x] **v81 — Permission System 3.0:** declarative **permission profiles** (global/workspace/agent/tool + action pattern + risk) with **deny/require_approval/allow** / **most-restrictive** evaluation / **approval chains by risk** (0/1/2 approvers) / side-effect-free **policy preview** / **blocked-action explanation** / **additive** to core PermissionService; can only tighten; allow grants no new power / governance-logged / analytics / `/api/permissions`. *(Developer-Mode panel deferred to a later UI pass.)*
- [x] Backend tests green and frontend build green after each version.
- [ ] PRs merged in order (v36 → v37 → v38 → v39 → v40 → v41 → v42 → v43 → v44) and verified on `main` before marking Linear Done.

## v44.5 — Portfolio & Demo Pack (consolidation)

- [x] Docs synced to real scale (44 versions · 85 services · ~480 routes · 48 test modules · 494 tests · ~10,200-line UI).
- [x] Portfolio pack created (`docs/PORTFOLIO_PACK.md`).
- [x] Screenshot guide refreshed with prioritized 12-shot pack (`screenshots/README.md`).
- [x] Demo script refreshed to a 5–7 minute, 9-scene flow (`docs/DEMO_VIDEO_SCRIPT.md`).
- [x] Release notes created (`docs/RELEASE_NOTES_v44.md`).
- [x] Demo-data checklist created (`docs/DEMO_DATA_CHECKLIST.md`).
- [x] `VERSIONS.md` includes a v44.5 entry + table row.
- [x] Backend tests pass (494) and frontend build passes.
- [x] No secrets committed.
- [x] No runtime data committed (`backend/app/data/*.json` remains git-ignored).
- [x] No backend/frontend behavior change — documentation only.

> **Not AGI.** Governed orchestration layer only. Roadmap after v40 is future-only.

## Current Roadmap Status

- **Completed and merged:** v21.0 — Multi-Modal Real-World Agent
- **Active work:** v22.0 — Industry Workflow Modes
- **Platform base:** v15.0 — EvolveAgent OS
- **Backend tests:** passing on completed release branches
- **Frontend build:** passing on completed release branches
- **Git status:** may include active v22 source work and local generated files; do not commit runtime data or secrets
- **Secrets/runtime data:** none committed; `.env` files and `backend/app/data/*.json` remain gitignored

### Release Readiness Checklist

- [x] README is final and professional (title, description, architecture, features, safety, tech stack, setup, status)
- [x] Architecture diagram added (`docs/ARCHITECTURE.md` + README + summary)
- [x] Screenshot guide exists (`screenshots/README.md`)
- [x] Demo video script exists (`docs/DEMO_VIDEO_SCRIPT.md`)
- [x] Resume bullets document exists (`docs/RESUME_BULLETS.md`)
- [x] Interview explanation document exists (`docs/INTERVIEW_EXPLANATION.md`)
- [x] Project case study exists (`docs/CASE_STUDY.md`)
- [x] GitHub repo is clean (gitignore covers env/uploads/runtime data/logs/build output)
- [x] Backend tests pass (222)
- [x] Frontend build passes
- [x] `.env.example` files present (`backend/.env.example`, `frontend/.env.example`)

### Known Limitations

- No authentication, cloud database, or deployment setup (intentionally local-first / MVP)
- No production vector database or RAG search — local JSON index only
- No OCR for scanned PDFs; no speaker diarization; no full video understanding
- No real image-generation API enabled by default (mock with fallback path)
- JSON storage is for MVP/demo scale, not distributed workloads
- Agent Jobs are local persisted records, not distributed workers

## Verification Commands

Backend tests:

```bash
cd backend
./venv/bin/pytest
```

Frontend build:

```bash
cd frontend
npm run build
```

## Completed Roadmap Checklist Through v21

- [ ] `GET /api/os/installer` returns readiness + setup steps (read-only; nothing installed)
- [ ] `GET /api/os/plugin-sdk` returns manifest schema + example manifest
- [ ] `POST /api/os/plugin-sdk/validate` accepts a valid manifest and rejects missing/invalid fields
- [ ] `GET /api/os/sla` returns uptime proxy score + SLA rating from local data
- [ ] `GET /api/os/scheduler` returns scheduler health overview
- [ ] `GET /api/os/summary` combines installer readiness, plugin SDK, SLA rating, scheduler health, and safety notes
- [ ] Developer Mode shows the EvolveAgent OS panel; Simple Mode stays clean
- [ ] Positioning is accurate: local-first, governed — not fully autonomous without approval, not self-training a base model, not hosted SaaS, no unrestricted shell access
- [ ] v16 departments and collaboration planning are visible in Developer Mode
- [ ] v17 workforce marketplace templates/import/export/rating flows work
- [ ] v18 business automation dashboard and draft-only workflows work
- [ ] v19 chief-of-staff planning and next-action flows work
- [ ] v20 business simulation comparisons work
- [ ] v21 multi-modal real-world analysis workflow works
- [ ] v22 industry workflow mode work is kept on its feature branch until verified

## Manual Demo Prompts

- `Explain how EvolveAgent AI works.`
- `Search my project knowledge for app automation decisions.`
- `Calculate 184 * 27.`
- `Generate an image prompt for a futuristic AI assistant.`
- `Summarize this uploaded document.`
- `Summarize this recording and list action items.`
- `Compare the best plan for improving this project demo.` with Deep Mode on
- `Build an AI resume analyzer app.`
- `Add dark mode to this app.`
- `Run tests for this project.`
- `Explain the current app architecture.`

## Manual UI Checks

- Simple Mode opens cleanly with the Jarvis-style voice/text start.
- Jarvis-style command center shows voice and text options.
- Light/dark theme toggle works and persists.
- Theme styling remains readable in chat, panels, markdown, code blocks, cards, and composer.
- Onboarding walkthrough appears on first run and can be dismissed.
- Reduced-motion setting is respected by UI animations.
- Developer Mode inspector opens and closes cleanly.
- Developer Mode sidebar works on narrow/mobile-width windows.
- Workspace switcher works.
- Memory panel can add, search, filter, edit, delete, pin, and unpin memory.
- Project Brain / Knowledge Base search works.
- Knowledge export works as Markdown and JSON.
- Cross-session knowledge links appear when linked records exist.
- Assistant Tools work through the frontend.
- Tool Trace appears in Developer Mode when a run selects tools.
- Approval Queue appears in Developer Mode.
- Approval Audit appears in Developer Mode.
- Agent Jobs panel appears in Developer Mode.
- Agent Jobs can create a test job, start next, pause/resume/cancel, and heartbeat.
- System Prompt Registry panel appears in Developer Mode.
- System prompts can be viewed and saved.
- Mission Control goals and task cards still work.
- Custom Agent Builder still works.
- File upload still works.
- Recording upload still works.
- Mock Image Agent still works.
- Feedback buttons still work.
- Analytics and Learning panels still work.
- Simple Mode hides technical metadata.

## Backend Checks

- `/api/run` still works for normal text.
- `/api/run` still works for file tasks.
- `/api/run` still works for recording tasks.
- `/api/run` still works for image generation.
- `/api/run` still returns tool trace metadata when tools are selected.
- `/api/tools` returns registered tools.
- `/api/plugins` returns plugin manifests without crashing on invalid plugins.
- `/api/approvals` returns approval queue data.
- `/api/approvals/audit` returns audit data.
- `/api/agent-jobs` returns persisted jobs.
- `/api/agent-jobs/health` returns job health.
- `/api/system-prompts` returns registry entries.
- `/api/governance` still works.
- `/api/analytics` still works.
- `/api/learning/report` still works.

## Automation Safety Checklist

- File edits require explicit approval.
- Command execution is allowlisted only.
- Allowed commands: `npm run build`, `npm test`, `npm run lint`, `pytest`, `python -m pytest`.
- Destructive file deletion is not supported.
- Unrestricted shell execution is not supported.
- Package installation is not supported through automation.
- `.env` editing is blocked.
- `.git`, `node_modules/`, `venv/`, uploads, and local data/analytics files are blocked.
- Execute-level tools require approval.
- Prompt/workflow/model learning proposes changes only.
- Prompt versions require approval and can be rolled back.
- Custom agents cannot bypass permissions or governance.
- The app does not silently self-modify.
- The base LLM is not retrained or fine-tuned by the app.

## Files to Avoid Committing

- `.env`
- `backend/.env`
- `venv/`
- `node_modules/`
- `dist/`
- `__pycache__/`
- `.pytest_cache/`
- `backend/app/uploads/`
- `backend/app/uploads/extracted/`
- `backend/app/data/*.json`
- local logs
- private uploaded documents
- private screenshots with secrets

## Environment Safety Checklist

- Confirm `.env` files are ignored.
- Do not commit API keys.
- Use `.env.example` or README examples for configuration.
- Keep `IMAGE_MODE=mock` unless real image support is intentionally added later.
- Use `TRANSCRIPTION_MODE=mock` for demos without transcription cost.
- Use `LLM_MODE=mock` for demos without API keys.
- Optional consensus keys are `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, and `MISTRAL_API_KEY`.
- Optional Linear/Codex worker keys stay server-side in `backend/.env`.

## GitHub Cleanup Checklist

- README reflects v21 completed and v22 in progress.
- DEMO.md reflects v21 completed and v22 in progress.
- FINAL_PROJECT_SUMMARY.md reflects v21 completed and v22 in progress.
- FINAL_CHECKLIST.md reflects v21 completed and v22 in progress.
- WORK_SUMMARY.md maps recent EVO issues to commits.
- Backend tests pass.
- Frontend build passes.
- No API keys are committed.
- No uploaded private files are committed.
- No runtime JSON data is committed.
- No generated build output is committed.
- No local logs are committed.
