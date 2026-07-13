# Codex Assignment — Real Cost Tracking (Parallel Track)

**Context:** EvolveAgent's v1-v200 backend roadmap is complete
(`docs/roadmap/EvolveAgent-v200-Strategy.md`). Claude is running a same-day
audit-driven session finding and closing small "real vs mock" wiring gaps —
services with genuinely real logic whose production consumer never calls
them. Read `docs/CODEX_HANDOFF.md` first for the general architecture,
patterns, safety contract, and PR cadence; it's slightly stale on task
numbering but accurate on conventions (service/route/test structure, PR
cadence, governance logging, `StorageService` usage).

This assignment is a **separate, well-isolated gap** in the same style,
scoped to avoid any file Claude is actively iterating on today.

## 🚫 Do NOT touch (Claude may be mid-edit — would cause merge conflicts)
- `backend/app/services/scheduler_tick_worker.py`
- `backend/app/services/kaggle_worker_service.py`
- `backend/app/services/worker_registry_service.py`
- `backend/app/services/agent_department_service.py`
- `backend/app/services/custom_agent_service.py`
- `backend/app/services/provider_control_service.py`
- `backend/app/agents/master_agent.py`
- `backend/app/api/routes.py` — **the singleton-construction block only**. If
  you need to add a new singleton, append it at the very end of that block
  (after the last line), never insert mid-block, and pull latest `main`
  immediately before your PR to minimize conflict risk.

## ✅ You own
`backend/app/services/llm_router.py`, `backend/app/services/usage_ledger_service.py`,
their route modules, and new tests. Pull latest `main` before starting — Claude
is merging several small PRs today, so `llm_router.py` in particular may have
moved since this doc was written.

---

## The gap

`UsageLedgerService.record_usage()` is real: it computes an estimated cost per
call (`units * _DEFAULT_RATES[capability]`, or an explicit override), persists
it, and `summary()`/`department_budget_status()` already gate real actions on
it (a department over budget gets a new run blocked — see
`AgentDepartmentService.plan_run()`, merged today). But **nothing calls
`record_usage()` automatically**. Every real LLM call goes through
`LLMRouter.generate()` → `generate_with_route()` (or the forced-provider path
`generate_for_provider()`), which already returns real `latency_ms` and
`success`/`fallback_used` per call — but never records an estimated cost
against any workspace's budget. A workspace can be completely out of its
budget and every subsequent real LLM call still succeeds identically, because
nothing is watching spend at the point where spend actually happens.

## Task: wire real per-call cost recording into `LLMRouter`

1. **`LLMRouter`**: add an optional `usage_ledger=None` constructor param
   (mirrors the existing optional `provider_control=None` pattern in the same
   class). Store it as `self.usage_ledger`.
2. In `generate_with_route()` (the single choke point every real/mock call
   already flows through — confirm this by reading the method fully before
   changing it), after a call completes (success or failure, real or
   mock-fallback), best-effort call
   `self.usage_ledger.record_usage({...})` if `self.usage_ledger is not
   None`, wrapped in `try/except Exception: pass` so a ledger failure can
   *never* affect the actual LLM call's result. Map:
   - `capability`: `"text"` (the only capability this call site produces —
     do not invent new capability types)
   - `units`: `1` per call (do not try to estimate real token counts unless
     you find the provider response already exposes them cleanly — if it's
     not trivial, stick with `1` and let `estimated_cost` come from the
     existing default per-unit rate; do not guess a token-based formula)
   - `workspace_id`: **this is the hard part.** `LLMRouter.generate()` today
     has no `workspace_id` parameter anywhere in its signature. You need to
     thread an optional `workspace_id: str | None = None` through
     `generate()` → `route_for_agent()` (only where needed to reach
     `generate_with_route`) → `generate_with_route()`, **defaulting to
     `None` everywhere it's not passed** so every existing call site
     (there are many — `master_agent.py`, `custom_agent_service.py`, etc.)
     keeps working unchanged. When `workspace_id` is `None`,
     `record_usage()` already defaults to `"default"` — that's fine and
     expected for call sites you don't update.
   - `mode`: `"mock"` if the route's provider ended up being `"mock"` after
     fallback, else `"real"`.
3. **Do not thread `workspace_id` through every caller in this PR.** Just
   wire the plumbing (`LLMRouter.generate()`/`generate_with_route()` accept
   and forward it) and add it to the **two or three real call sites that are
   easy and unambiguous** (e.g. if `MasterOrchestratorAgent.run()` already
   has `workspace_id` in scope at its own `agent.run_with_metadata()` call
   sites — check `base_agent.py`'s `run_with_metadata` signature and decide
   whether it's worth threading there too, or whether that's a separate,
   larger follow-up task not in scope here). If threading it everywhere
   turns out to be invasive, stop at the `LLMRouter` plumbing + `analytics_summary()`
   wiring and leave a note in the PR description — partial-but-safe is
   better than a large risky diff.
4. **Wire the collaborator** in `routes.py`: `usage_ledger_service` is
   already constructed (search for `usage_ledger_service = UsageLedgerService(`);
   `llm_router` is the module-level singleton in `llm_router.py` (not
   constructed in `routes.py` — check how `provider_control` gets wired onto
   it post-init in `routes.py` today and mirror that exact pattern).
5. **Tests**: new tests in `backend/tests/test_llm_router.py` (do not touch
   the existing tests in that file, only add new ones) verifying: a real
   call with `usage_ledger` wired records a usage entry with the right
   `mode`; a broken `usage_ledger` never breaks the LLM call itself; no
   `workspace_id` passed still records against `"default"`; existing
   call-sites-with-no-`usage_ledger`-wired behavior is completely unchanged
   (regression, not just new coverage).
6. Bump `UsageLedgerService.analytics_summary()`'s existing `/api/analytics`
   merge (already wired) — no changes needed there, just confirm real counts
   now move as real calls happen (add one test for this).

## Rules
- Follow the safety contract: no billing/charging (this service already says
  "estimates only" everywhere — keep that framing, do not add a "charge the
  user" path), governance already logs `usage_recorded` via the existing
  `record_usage()` — do not duplicate that logging.
- Every new/changed function needs the existing docstring style: WHY it
  exists, not WHAT it does line-by-line.
- **PR cadence:** branch off latest `origin/main` (never bare `git checkout
  main` if you're in a worktree — use `git checkout -B <branch>
  origin/main`); `cd backend && python -m pytest tests/test_llm_router.py
  tests/test_usage_ledger_service.py tests/test_api.py -q`; run
  `scripts/smoke_test.py` against a scratch-port backend
  (`python -m uvicorn app.main:app --port <free-port>`); commit only
  intended files (**never `git add -A`**; no `Co-Authored-By` trailer unless
  this repo's `.claude/settings.json` sets `attribution.commit`); push;
  `gh pr create`; wait for CI green; merge with
  `gh pr merge <#> --admin --merge --delete-branch` (a
  `fatal: 'main' is already used by worktree` error from that command is
  expected/harmless in this repo's worktree setup — verify the merge
  actually landed with `gh pr view <#> --json state,mergedAt` and manually
  `git push origin --delete <branch>` if the remote branch didn't
  auto-delete).
- If `llm_router.py` has diverged significantly from what's described here
  by the time you start (Claude is actively shipping PRs today), re-read the
  current file fully before planning your diff — this doc describes the
  gap and the shape of the fix, not necessarily today's exact line numbers.

**Deliver as one PR. Report the PR number when done.**
