# Codex Assignment — EvolveAgent v150 Frontend (Autonomous Software Team UI)

**Context:** EvolveAgent AI's backend just shipped a complete, real,
approval-gated "Autonomous Software Team" pipeline (v150, PRs #198–#200):
an agent can propose a real code change (one file or up to 10 related files),
which — only after a human approves it — becomes a real local git commit on a
brand-new branch; a **second**, separately-approved step can then push that
branch and open a real GitHub pull request. Every write is opt-in (off by
default), allow-list-scoped to specific repos, and never touches
EvolveAgent's own source tree unless an operator explicitly configures it to.

**There is currently ZERO frontend for any of this.** Your job is to build it.
Claude owns the backend (`backend/app/services/code_writer_service.py`,
`durable_workflow_service.py`, `github_connector_service.py`) — **do not
modify those**. You own the frontend.

Read `docs/CODEX_HANDOFF.md` first for general architecture/safety/PR-cadence
conventions used across this repo.

## 🚫 Do NOT touch
- Anything under `backend/app/services/**` or `backend/app/api/**`
- `backend/tests/**`
- If you find a genuine backend bug while building the UI (e.g. a response
  shape mismatch), **document it and work around it in the frontend** rather
  than patching the backend yourself — flag it in the PR description instead.

## ✅ You own
`frontend/**` (and can extend `frontend/src/data/api.ts` freely — that file
is the shared frontend/backend contract layer, not backend code).

---

## What already exists (read before building)

- `frontend/src/pages/MissionControl.tsx` — the closest existing analog.
  Already calls `startDurableRun()` / `fetchWorkflowRuns()` from
  `frontend/src/data/api.ts` and renders a Kanban of runs by status
  (`planned` / `running` / `waiting_approval` / `completed`). Study this
  pattern; your new panel should feel like a natural sibling, not a
  from-scratch design.
- `frontend/src/pages/ApprovalsPage.tsx` — the general approvals UI (currently
  wired to the older MCP-execution approval flow, not durable-workflow steps).
  Reuse its `GlassCard` / `StatusBadge` / `RiskBadge` components
  (`frontend/src/components/shared/`) and `lucide-react` icon style for visual
  consistency.
- `frontend/src/data/api.ts` — has `startDurableRun(name, steps)` and
  `fetchWorkflowRuns()` already. **Missing** (you need to add these):
  a per-run detail fetch (`GET /api/durable-workflows/runs/{run_id}`), a
  step-approve call (`POST /api/durable-workflows/runs/{run_id}/approve` with
  body `{approved: boolean, note?: string, approver?: string}`), and a
  `GET /api/code-writer/status` fetch.

## Real backend endpoints to wire up (all live, all real, no mocking needed)

- `GET /api/durable-workflows/runs` — list runs (already used).
- `GET /api/durable-workflows/runs/{run_id}` — full run detail, including
  `steps[]`. Each step has `action_type`, `action_params`, `status`
  (`pending`/`waiting_approval`/`done`/`skipped`), and — once executed —
  `output` (a human-readable string like
  `"[executed] write_code_change: branch=eva/auto-abc123 files=2 sha=deadbeef"`
  or `"[declined] write_code_change: Code writes are disabled. ..."`).
- `POST /api/durable-workflows/runs/{run_id}/approve` — body
  `{"approved": true|false, "note": "optional", "approver": "optional name"}`.
  Approving/rejecting the *current* gated step. If the step named 2+
  approvers (`action_params` won't show this — it's on the step's own
  `approvers`/`approval_progress` fields), multiple calls may be needed; show
  `approval_progress` if present.
- `GET /api/durable-workflows/effects?run_id={run_id}` — the actual effect
  records, including the real `result` dict from the backend service (for
  `write_code_change`: `{wrote, repo, branch, commit_sha, file_path(s),
  commit_message, note}`; for `open_pull_request`:
  `{pushed, pull_request: {url, number, ...} | null, note}`).
- `GET /api/code-writer/status` — `{available, writes_enabled,
  writes_opt_in_env, push_enabled, push_opt_in_env, allowed_repos_env,
  allowed_repos: string[], allowed_git_subcommands, note}`. Use this to show
  "why is this declining?" — e.g. if `writes_enabled` is false, show the exact
  env var name to set, not a generic error.
- `GET /api/github/status` — `{writes_enabled, supported_writes, ...}` —
  same idea for the PR-creation half.

Two step `action_type` values you'll specifically render specially:
`write_code_change` and `open_pull_request`. Every other action_type
(`create_task`, `notify`, `create_github_issue`, etc.) already renders fine
generically — don't break that.

## What to build

1. **A "Code Changes" panel** (new page or a well-integrated section of
   `MissionControl.tsx` — your call on which reads better) that:
   - Lists durable-workflow runs whose steps include `write_code_change` or
     `open_pull_request`, most-recent first.
   - For a run currently `waiting_approval` on one of these steps: show the
     **proposed diff** in a readable way — file path(s) + content from
     `action_params` (for multi-file steps, `action_params.files` is a
     **JSON-encoded string** — `JSON.parse` it; each item is
     `{file_path, content}`), the commit message, and the target repo. A
     simple syntax-highlighted or monospace content preview is enough — no
     need for a full diff algorithm since this is a *new* file/commit, not a
     diff against existing content.
   - Approve / Reject buttons that call the new approve endpoint. After
     approving, poll or refetch the run to show the real result (branch name,
     commit sha, or — for `open_pull_request` — the real PR URL as a
     clickable link once opened).
   - When a step declines (writes disabled, repo not allow-listed, etc.),
     show the **exact reason** from the step's `output` / effect `result.note`
     — don't swallow it into a generic "failed" state. This is a safety
     feature, not a bug — surface it clearly (e.g. an amber "Declined safely"
     state, not a red "Error" state).

2. **A small config/status strip** (could live in `SettingsPage.tsx` or
   `DevModeConsole.tsx` — your call) showing `/api/code-writer/status` +
   `/api/github/status`: whether writes/push are enabled, which repos are
   allow-listed, secret-safe (never render any token value — there isn't one
   in these responses, but double-check before rendering anything from a
   `/api/github/*` response).

3. Update `frontend/src/data/api.ts` with typed helpers for the endpoints
   above (mirror the existing style — see `fetchWorkflowRuns`,
   `approveConnectorExecution` for the shape/error-handling convention: never
   throw on a network error, return `null` and let the caller show a toast).

## Rules

- Follow the safety-surfacing principle above: a "declined safely" state is
  **not** an error state in the UI. This mirrors the backend's own design
  philosophy (never a silent no-op, never a crash, always a clear reason).
- Never render a secret/token value from any API response (there shouldn't be
  one, but verify).
- **PR cadence:** branch off latest `origin/main`; `cd frontend && npm ci &&
  npm run build` (and `npm run test` if a test script exists — check
  `package.json`) must pass before you open a PR; commit only intended files
  (**never `git add -A`**, no `Co-Authored-By` trailer); push; `gh pr create`;
  poll `gh pr checks`; merge with `gh pr merge <#> --admin --merge
  --delete-branch` **only if CI is green** — leave it open and fix forward if
  red, never force-merge.
- Test against a **live local backend** if possible
  (`cd backend && uvicorn app.main:app --reload`) — you can safely exercise
  the full flow end-to-end because `CODE_WRITES_ENABLED` /
  `GITHUB_WRITES_ENABLED` are off by default in that environment, so nothing
  destructive can actually happen; every approve click will show the real
  "declined safely" path unless you deliberately export those env vars
  against a disposable throwaway git repo.

**Report back the PR number when done.**
