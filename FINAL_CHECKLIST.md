# EvolveAgent AI — Final Checklist (current completed: v47.0 Secret Reference Registry · v45.1 MCP Hub UI)

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
