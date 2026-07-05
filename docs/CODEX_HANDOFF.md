# EvolveAgent — Continuation Handoff (for Codex / any agent)

**Purpose:** if the current assistant (Claude) hits a usage limit, paste this file
to Codex (or another coding agent) and it can continue the work with full context.
This is the single source of truth for *how we build here*.

---

## 1. Mission & current state

EvolveAgent is a **local-first, planning-first agent workspace**: a FastAPI
backend + React (Vite) frontend. We finished a "futuristic" roadmap
(Phases 0–7, all merged) and are now executing an 11-item **"Depth · Real · Trust"**
program. Nothing here is speculative — follow the existing patterns exactly.

**Repo:** `manit0700/evolveagent-ai` · default branch `main` (protected, required
CI: "Backend tests" + "Frontend build"). `gh` is authenticated.

## 2. The task program (work top-to-bottom, one PR each)

| # | Task | Notes | Blocked on |
|---|------|-------|-----------|
| 9 | ✅ End-to-end smoke suite | `scripts/smoke_test.py` (DONE) | — |
| 1 | Design Agent → live in-app | approval-gated OpenRouter path + web panel; mock-safe until key | 🟡 user's `OPENROUTER_API_KEY` for live calls |
| 2 | Git Intelligence real reads | real commit/branch/diff read views (read-only) | — |
| 3 | Durable Workflows real step actions | step calls a **whitelisted internal** action (create task/notify) behind approval gate; NO external mutation | — |
| 4 | Agent Studio hardening | fork/duplicate, version rollback, richer eval, few-shot preview | — |
| 5 | Voice Console depth | live-transcript panel + push-to-talk polish | — |
| 6 | Command palette polish | recent/frequent, fuzzy scoring, per-result actions | — |
| 10 | Backfill deferred v77–v90 UI panels | some backend features lack front doors | — |
| 8 | Split monoliths | `routes.py` → routers; `App.jsx` panels → components (incremental) | — |
| 11 | Net-new | approval-gated MCP connector exec · home/today dashboard · multi-workspace polish | — |
| 7 | Mac app compile | prep done; **user** runs `npm run tauri build` (needs Rust+Xcode) | 🟡 user's machine |

## 3. Architecture map

- **Backend:** ONE monolith `backend/app/api/routes.py` (~5.7k lines, 671 routes)
  wires thin route → service. **131+ services** in `backend/app/services/`.
  Pydantic models in `backend/app/models/{request,response}_models.py`.
  Persistence = **flat JSON files** in `backend/app/data/` via `StorageService`
  (`read_list` / `append` / `write_list`). Every mutating action is logged via
  `GovernanceService.log_event(GovernanceEvent(...))`. Per-service metrics are
  merged into `GET /api/analytics`.
- **Frontend:** ONE monolith `frontend/src/App.jsx` (~14k lines) + `api.js`
  (helpers: `getJson/postJson/patchJson/putJson/delJson`, `API_BASE =
  import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'`). Design system in
  `frontend/src/styles/tokens.css` (`--ds-*`) + `components/ui/{Card,Button,Badge}`
  and `components/layout/CommandPalette`. Dev-mode panels are `<section
  data-group="agent|workspace|ops|tools|intel|build">`.

## 4. Recipe to add a backend feature (follow exactly)

1. `backend/app/services/<feature>_service.py` — class takes `(storage,
   governance_service, ...deps)`; methods return plain dicts; add
   `analytics_summary()` returning `{"<feature>_x": n, ...}`.
2. Register any new JSON filenames in `StorageService.__init__`'s tuple
   (`storage_service.py`).
3. Request models in `request_models.py` (validate + cap lengths).
4. In `routes.py`: import the service, instantiate it next to the others
   (~line 465), add `@router.<verb>("/<feature>/...")` handlers (translate
   `ValueError` → `HTTPException(400/404)`), and add
   `**<svc>.analytics_summary(),` to the `/api/analytics` dict (~line 1770).
5. Tests: `backend/tests/test_<feature>_service.py` using
   `fastapi.testclient.TestClient(app)`. Include a
   `test_existing_endpoints_still_work` guard.
6. Frontend: add `api.js` helpers, then a Dev-mode `<section>` panel in
   `App.jsx` built from `Card/Button/Badge`; add a `⌘K` command entry in the
   `commandPaletteCommands` useMemo.

## 5. SAFETY CONTRACT — non-negotiable (from the product owner)

Local-first · planning-first · **mock-safe by default** · approval-gated for risky
actions · governance-logged · permission-aware · secret-safe · user-controlled.

**Hard boundaries — never cross:**
- No unrestricted shell access; no destructive autonomous file ops.
- No autonomous real sending / payment / deployment / deletion / external
  mutation without explicit approval. Risky actions
  (send/email/pay/delete/deploy/post/publish/transfer/…) must start in
  `requires_approval` and never auto-run.
- No raw secret values in UI/logs/API/exports — secrets only as booleans/labels/
  references (e.g., "key configured: true").
- No always-on recording without explicit opt-in. No base-model self-training —
  "personalization" = config + retrieval + few-shot + preference/eval feedback.
- Do not claim the app is AGI.

## 6. Dev workflow & cadence

```bash
# work happens in this git worktree; run everything from its root
BR=feat/<slug>; git checkout main && git fetch origin && git reset --hard origin/main
git checkout -b "$BR"
# ... make changes ...
# backend tests (use the main repo venv):
source /Users/manitdankhara/evolveagent-ai/backend/venv/bin/activate
cd backend && python -m pytest tests/test_<feature>_service.py -q && cd ..
# frontend build:
cd frontend && npm run build && cd ..
# commit only intended files (NEVER `git add -A` — see gotchas), push, PR:
git add <specific files>; git commit -m "..."; git push -u origin "$BR"
gh pr create --title "..." --body "..."
# after CI passes (poll `gh pr checks <#>`), merge with a MERGE COMMIT (not squash):
gh pr merge <#> --admin --merge --delete-branch
git checkout main && git fetch origin && git reset --hard origin/main
```

**Commit trailer:** do NOT add a `Co-Authored-By` line (project rule).

## 7. Gotchas (learned the hard way)

- **Never `git add -A`.** Never commit: `backend/app/data/*.json` (runtime),
  `.env`, `node_modules`, `venv`, `dist`, `.claude-flow/`, `.venv`,
  `desktop/src-tauri/{target,gen,icons}`. Stage explicit files only.
- **Use `--merge`, not `--squash`,** on stacked branches (squash rewrites commits
  and breaks downstream PRs).
- **Name collisions are real** — we've hit 3 (`workflowBusy`, `agentTemplates`,
  route `/git/*`). Before adding a name/route, `grep` for it. Pick a distinct
  namespace (we used `/git-intel`, `/marketplace-hub`, `durableBusy`).
- **zsh** doesn't word-split unquoted vars — use arrays in loops.
- The worktree's `.git` is a **file** (a `gitdir:` pointer), not a dir.
- Frontend has no `vite.config.*`: dev port **5173**, build outDir **dist**.

## 8. Verify everything

```bash
# start a fresh backend, then smoke it (catches stale-code 404s):
cd backend && source /Users/manitdankhara/evolveagent-ai/backend/venv/bin/activate
uvicorn app.main:app --port 8020 &
python ../scripts/smoke_test.py http://127.0.0.1:8020   # want 27/27 (grows as features land)
```
Add a new happy-path check to `scripts/smoke_test.py` `CHECKS` for every panel you ship.

## 9. What needs the user (only two things)

- 🟡 **`OPENROUTER_API_KEY`** in env → unlocks live Design Agent analysis (#1).
  Until then the code must degrade to a deterministic/mock response.
- 🟡 **Rust + Xcode CLT** on the Mac → unlocks the real Tauri build (#7):
  `cd desktop && npm install && npm run tauri icon <logo.png> && npm run tauri build`.

---
*Keep PRs small, additive, tested, and safety-compliant. When in doubt, mirror the
most recent merged feature (Marketplace Hub, PR #132) as a template.*
