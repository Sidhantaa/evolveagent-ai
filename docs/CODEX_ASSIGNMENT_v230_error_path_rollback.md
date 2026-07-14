# Codex Assignment — Error-Path / Partial-Failure Rollback Correctness

**Context:** EvolveAgent's v1-v200 backend roadmap is complete
(`docs/roadmap/EvolveAgent-v200-Strategy.md`). Claude ran a same-day
audit-driven session today (2026-07-13/14) that closed 17 real gaps across
two lenses:

1. **Wiring gaps** (rounds 1-24): services with genuinely real logic whose
   production consumer never called them, or hand-maintained
   registries/rollups that went stale after a same-day capability landed.
2. **Concurrency lost-update races** (rounds 25-33, PRs #252-#259): a
   `StorageService.update_list(filename, mutator)` primitive was added to
   close a real, standalone-repro-confirmed class of bug — a plain
   `read_list()` + `write_list()` pair (as two separate lock acquisitions)
   silently drops a concurrent writer's change. Fixed in: the storage layer
   itself, `KaggleWorkerService`, `WorkerRegistryService`,
   `AgentSchedulerService`, `AdaptiveLearningService`,
   `ScheduledTasksService`, `GoalService`, `LinearLinkService`,
   `CodexJobService`. That lens concluded when a mechanical sweep confirmed
   the app has exactly two background loops
   (`linear_poll_worker.py`, `scheduler_tick_worker.py`) and every file
   either writes is now fixed.

Read `docs/CODEX_HANDOFF.md` first for the general architecture, patterns,
safety contract, and PR cadence — it's slightly stale on task numbering but
accurate on conventions (service/route/test structure, PR cadence,
governance logging, `StorageService` usage, the `update_list()` primitive
added today).

This assignment opens a **third lens**: error-path / partial-failure
correctness in a real multi-step execution pipeline. Unlike the first two
lenses, this is explicitly an **audit-then-fix** task, not a pre-diagnosed
bug — find one real, concretely reachable gap with the same rigor standard
today's session used (a standalone repro proving the bug is real against the
unmodified code, not a theoretical concern), then fix it.

## 🚫 Do NOT touch (Claude touched these today — high conflict risk)
- `backend/app/storage/backend.py`, `backend/app/storage/json_backend.py`,
  `backend/app/storage/cached_backend.py`, `backend/app/storage/postgres_backend.py`
- `backend/app/services/storage_service.py`
- `backend/app/services/kaggle_worker_service.py`
- `backend/app/services/worker_registry_service.py`
- `backend/app/services/agent_scheduler_service.py`
- `backend/app/services/adaptive_learning_service.py`
- `backend/app/services/scheduled_tasks_service.py`
- `backend/app/services/goal_service.py`
- `backend/app/services/linear_link_service.py`
- `backend/app/services/codex_job_service.py`
- `backend/app/api/routes.py` — **the singleton-construction block only**
  (append new singletons at the very end, never insert mid-block; pull
  latest `main` immediately before your PR)

## ✅ Suggested area to audit (not prescriptive — verify before committing)
`backend/app/services/durable_workflow_service.py` and its real,
approval-gated multi-step execution (`start_run`, `advance_run`,
`approve_step`, `run_quality_checks`, `run_eval_suite`). This is EvolveAgent's
main "several real steps in sequence, some of which can genuinely fail
mid-run" pipeline (real `SafeCommandRunner` subprocess execution for quality
gates, real self-healing check/repair creation, real eval-suite runs). Look
for: a step that partially mutates state (e.g. writes a partial result,
increments a counter, marks something in-progress) and then hits a real
failure (subprocess error, missing collaborator, an exception from a
downstream service) without either completing the mutation or rolling it
back — leaving the run/job record in an inconsistent state a human or the
scheduler can't cleanly recover from.

If, after genuinely reading the code, `DurableWorkflowService` turns out to
already handle this correctly (many of today's earlier rounds found genuine
dead ends and correctly said so — that's a valid, useful outcome, not a
failure), look instead at `MasterOrchestratorAgent.run()`'s specialist loop
(`app/agents/master_agent.py`) — 4+ real agents run in sequence per request;
does a mid-loop agent failure leave `shared_context`/governance logging/cost
recording in a half-updated state that a later step relies on?

## Rules
- **Audit first, with evidence.** Before writing any fix, produce a concrete
  reachability proof: exact file/line, exact trigger (a real subprocess
  failure, a real exception path, a real partial state), and ideally a
  scratch script or failing test demonstrating the bad state against the
  **current, unmodified** code. Do not report or fix something you can't
  demonstrate is reachable — several candidates today turned out to be
  theoretical-only and were correctly rejected rather than "fixed" anyway.
- Keep the fix scoped to the one gap you found and proved — don't refactor
  the whole pipeline. Partial-but-safe beats a large risky diff.
- Follow the existing safety contract: never bypass approval gates, never
  auto-retry a risky step, keep every stateful action governance-logged.
- **PR cadence:** branch off latest `origin/main` (`git checkout -B <branch>
  origin/main`, never a bare `git checkout main` in a worktree); run the
  specific test file(s) for whatever you touch plus
  `cd backend && python -m pytest tests/test_durable_workflow_service.py -q`
  (or `tests/test_master_agent.py`-equivalent, check what exists) as
  regression; run `scripts/smoke_test.py` against a scratch-port backend;
  commit only intended files (**never `git add -A`**; no `Co-Authored-By`
  trailer unless this repo's `.claude/settings.json` sets
  `attribution.commit`); push; `gh pr create`; wait for CI green; merge with
  `gh pr merge <#> --admin --merge --delete-branch` (a
  `fatal: 'main' is already used by worktree` error from that command is
  expected/harmless — verify the merge landed with
  `gh pr view <#> --json state,mergedAt`, and `git push origin --delete
  <branch>` if the remote branch didn't auto-delete).
- If the codebase has diverged significantly from what's described here by
  the time you start, re-read the current files fully before planning your
  diff — this doc describes the shape of the task, not necessarily today's
  exact line numbers.

**Deliver as one PR (or report back "genuinely nothing reachable found" if
that's the honest outcome after a real audit — that's a valid result). Report
the PR number, or your dead-end finding, when done.**
