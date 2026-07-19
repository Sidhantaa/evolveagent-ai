# Codex Assignment — v280 Parallel Multi-Agent Execution: Scoped Slice

**Status:** PLAN ONLY. Do not implement v280 from this document yet.

Mirrors the v230/v240/v260 process: read the current execution code, define
the smallest real, safe slice, get it reviewed before any implementation.

Read `docs/CODEX_HANDOFF.md` first. Read the current execution code before
proposing any implementation:

- `backend/app/agents/master_agent.py` (`run()`, `run_consensus_candidates()`)
- `backend/app/services/agent_scheduler_service.py`
- `backend/app/services/llm_router.py` (`generate_with_route()`, `consensus_routes()`)
- `backend/tests/test_master_agent.py`, `backend/tests/test_agent_scheduler_service.py`

## Why this needs careful scoping (read this before proposing anything)

The obvious reading of "parallel multi-agent execution" is: make
`MasterOrchestratorAgent.run()`'s specialist loop (`for agent in
self.specialists: ...`) run concurrently instead of one at a time. **Do not
do this.** It is not safe, and this doc explicitly rules it out.

`run()` builds `shared_context` incrementally: each specialist's real output
is appended to `shared_context` (`shared_context += f"\n\n{agent.name}
output:\n{agent_output.output}"`) **before the next specialist runs**, so
specialist N actually reads specialist N-1's real output as part of its own
prompt. This is a genuine, load-bearing sequential data dependency, not an
incidental implementation detail — parallelizing this loop would mean every
specialist sees a different (smaller) context than it does today, which
changes the actual content and quality of every multi-specialist response on
the app's main, highest-traffic request path. That is a real behavior change
to the default chat experience, not a performance optimization, and it is not
something to make by scoping a "parallel execution" PR narrowly — it needs
its own explicit product decision if it's ever wanted, and is **out of scope
for this v280 slice**.

## What v280 means for this slice

Two places in the codebase already do independent, parallelizable work but
currently do it sequentially, with **zero cross-call data dependency** —
these are the genuinely safe v280 targets.

### Target 1: Deep Mode consensus candidates (real latency win, zero behavior change)

`run_consensus_candidates()` (`master_agent.py:1882`) builds ONE
`system_prompt`/`user_prompt` pair, then loops over `llm_router.consensus_routes()`
calling `llm_router.generate_for_provider(...)` once per route, sequentially.
Each call is a real, independent outbound LLM request to a different
provider — no candidate reads another candidate's output, unlike the main
specialist loop. This is exactly the class of thing that should run
concurrently: same total work, same final result set (just reordered/timed
differently), only reachable when `request.deep_mode` is already true (opt-in,
not the default path).

Proposed change: run the loop body concurrently (e.g. `asyncio.gather` if
`generate_for_provider` has/gets an async path, or a bounded thread pool if
it stays sync — match whatever `llm_router.py`'s existing call style is,
don't introduce a new async/sync split without checking how `run()` itself is
invoked). Preserve exact existing behavior: same `AgentOutput` list, same
order in the returned list (sort by original route order after gathering,
not completion order, so `summarize_consensus()` and any test asserting order
stays unaffected), same per-candidate error isolation (one candidate's
provider failure must not lose the others — already true sequentially via
`LLMResult.success`/`fallback_used`, keep it true concurrently).

### Target 2: AgentSchedulerService concurrent dispatch (real gap, needs an explicit opt-in decision)

`AgentSchedulerService` already supports genuine concurrent job execution --
`concurrency_limit: int = 2` (constructor default), enforced atomically in
`start_next()` via `storage.update_list()` (checks `len(running) >=
concurrency_limit` before dequeuing). But nothing automated ever calls
`start_next()`: `grep` confirms the only caller is a manual POST route
(`app/api/agent_jobs_routes.py`). `SchedulerTickWorker.tick_once()` fires due
scheduled tasks, sweeps stale jobs, and polls Kaggle jobs every tick, but
never dequeues a queued `AgentSchedulerService` job. So today, a job sitting
in `queued` status stays there forever unless a human manually hits the
dequeue endpoint once per job — the concurrency capability exists but is
unreachable through any automated path.

**This is a real, provable gap, but the fix is a genuine behavior/policy
choice, not a pure bug fix** — automatically starting previously-manual jobs
changes what "creating a job" means (today: nothing happens until a human
dequeues it; after: it starts on its own, up to `concurrency_limit` at a
time). Propose this as an explicit, default-OFF opt-in:

- A new settings flag, e.g. `AGENT_SCHEDULER_AUTO_DISPATCH_ENABLED` (default
  `false`), mirroring every other `*_ENABLED` flag in this app.
- When enabled, `SchedulerTickWorker.tick_once()` calls
  `agent_scheduler.start_next()` in a loop until it returns `None` (queue
  empty or `concurrency_limit` reached) — same isolation pattern as the
  existing stale-job sweep (try/except per call, one failure never stops the
  tick).
- When disabled (default), behavior is byte-for-byte unchanged: `queued` jobs
  wait for a human, exactly as today.
- Document clearly in the flag's own comment (in `config.py`, mirroring the
  Kaggle/RunPod flag comments) that turning this on changes `create_job()`'s
  effective semantics from "queued until a human starts it" to "starts
  automatically, up to N concurrent."

## Explicitly out of scope for this slice

- Parallelizing `MasterOrchestratorAgent.run()`'s main specialist loop (see
  the "why this needs careful scoping" section above — this is not a "maybe
  later in v280", it needs its own separate decision if ever revisited, and
  should be treated with the same weight as a request/response contract
  change, not a performance PR).
- Any new distributed-execution technology (Ray, Celery, Kubernetes Jobs,
  Temporal, Dask) — out of scope per the roadmap doc's own v220-v300 section.
- Autoscaling, cluster networking, or multi-machine work distribution.
- Increasing `concurrency_limit`'s default value — stays `2` unless the user
  explicitly asks for a different default.
- Wiring GPU/model-serving job execution (`run_kaggle_job`, `run_runpod_job`)
  into this concurrent dispatch path — those already have their own
  approval-gated execution path through `DurableWorkflowService` and should
  not be touched by this slice.

## Safety rules

- Target 1 (consensus candidates): no new flag needed — it's already gated
  behind `request.deep_mode`, and the change is latency-only, not a new
  capability. Must not change response content/ordering/error-handling
  semantics versus the sequential version — cover this with a test that
  asserts identical output for a given set of mocked provider responses,
  sequential vs concurrent.
- Target 2 (scheduler dispatch): must default to `false`. Enabling it changes
  real behavior (jobs start automatically) but does not bypass any approval
  gate — `AgentSchedulerService` jobs were never themselves an approval
  mechanism, DurableWorkflowService's step-level approval is untouched by
  this. Still: document this clearly so it isn't mistaken for a governance
  bypass.
- Neither target touches `master_agent.py`'s main `run()` specialist loop.

## Test and verification plan

```bash
cd backend
python -m pytest tests/test_master_agent.py tests/test_llm_router.py -q
python -m pytest tests/test_agent_scheduler_service.py tests/test_scheduler_tick_worker.py -q
python -m pytest -q   # full suite before merge
python scripts/smoke_test.py
```

Live verification: Target 1's real speedup is only observable with real (not
mock) LLM keys configured for 2+ providers — mock mode is fine for
correctness tests but won't show a timing difference. Target 2's real
automated dispatch should only be turned on (`AGENT_SCHEDULER_AUTO_DISPATCH_ENABLED=true`)
by the user themselves, after reviewing what "automatic" means for their
own job producers.

## Acceptance criteria

- `MasterOrchestratorAgent.run()`'s default (non-deep-mode) request path is
  byte-for-byte unchanged.
- Deep Mode's consensus output content/ordering/error-handling is unchanged
  from the sequential version, only faster with 2+ real providers configured.
- `AgentSchedulerService`'s existing manual dequeue route and
  `concurrency_limit` enforcement are unchanged.
- With `AGENT_SCHEDULER_AUTO_DISPATCH_ENABLED` unset/false (the default),
  `SchedulerTickWorker` behavior is unchanged from today.
- No secrets, no new approval-gate bypass, no change to
  `DurableWorkflowService`'s existing approval model.

## Suggested PR sequence after this plan is approved

1. This plan doc (docs-only PR, for review).
2. Backend-only PR: Target 1 (consensus candidates concurrency) + tests. Pure
   latency win, no new flag, safest to ship first.
3. Backend-only PR: Target 2 (scheduler auto-dispatch behind
   `AGENT_SCHEDULER_AUTO_DISPATCH_ENABLED`, default off) + tests.
4. Stop. Whether to ever parallelize the main specialist loop is a separate,
   later decision requiring its own scoping doc and explicit human sign-off —
   not an automatic next step from this slice.
