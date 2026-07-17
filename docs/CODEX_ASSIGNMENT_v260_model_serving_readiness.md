# Codex Assignment — v260 Distributed Model Serving: Readiness Slice

**Status:** PLAN ONLY. Do not implement v260 from this document yet.

This mirrors the v240 process (`docs/CODEX_ASSIGNMENT_v240_gpu_worker_expansion.md`,
shipped as PRs #263/#264): define the smallest useful, safe slice before any
code is written, so implementation can be approved, tested, and gated instead
of becoming a broad model-hosting rewrite.

Read `docs/CODEX_HANDOFF.md` first. Read the current GPU/worker code before
proposing any implementation:

- `backend/app/services/gpu_worker_service.py` (v240 coordinator — read/status,
  provider readiness, dry-run; never starts real cloud jobs itself)
- `backend/app/services/worker_registry_service.py`
- `backend/app/services/kaggle_worker_service.py`
- `backend/app/services/runpod_worker_service.py`
- `backend/app/api/worker_registry_routes.py`

## Why this is a different risk category from v220-v240

Everything shipped for the Compute Fabric so far (worker registry, Kaggle
adapter, RunPod adapter, GPU dashboard/dry-run) reads and writes JSON records
and, when explicitly approved, submits a job to an *external* provider's API.
None of it starts a process on the machine EvolveAgent itself runs on.

"Model serving" as described in the roadmap (`docs/roadmap/EvolveAgent-v200-Strategy.md`,
v260) means something categorically different: actually starting a local
inference server process, binding a port, and holding it open across
requests. That is real, ongoing resource consumption (CPU/RAM/GPU/disk for
model weights) and a new local network surface — not a one-shot approval-gated
write. Treat this as a materially higher blast-radius feature than anything
shipped in v220-v240.

Because of that, **this slice is readiness/status/dry-run ONLY.** No model
server process may be started by this implementation, under any flag,
enabled or not. That decision (actually running local inference) is
explicitly out of scope until a separate, later assignment.

## What this slice should answer

Same shape as the v240 dry-run pattern, applied to model serving instead of
GPU jobs:

- What model-serving backends does EvolveAgent know how to describe (e.g.
  `ollama`, `openai_compatible_endpoint`, `vllm`, `local_transformers`)?
- Is a given backend detected as already running (read-only check against a
  well-known local port/health endpoint — e.g. Ollama's default
  `http://127.0.0.1:11434/api/tags` — GET only, short timeout, never spawns
  anything if unreachable)?
- What models does a detected backend report it currently has loaded/available
  (read-only query against that backend's own list endpoint, if reachable)?
- If EvolveAgent wanted to route a request to local model serving instead of a
  cloud model API, what would the readiness/dry-run response look like
  (`accepted`/`declined_reason`/`missing_configuration`), mirroring
  `gpu_worker_service.py`'s `dry_run()` shape?

## Explicitly in scope

1. `backend/app/services/model_serving_service.py` (new) — read-only:
   - `detect(backend: str) -> dict`: a short-timeout GET against that backend's
     own health/list endpoint (only if the backend's base URL is explicitly
     configured via an env var — never guess/scan arbitrary ports). Returns
     `{"backend": ..., "reachable": bool, "models": [...], "checked_at": ...}`.
     Never raises on connection failure — degrades to `reachable: false`.
   - `dashboard() -> dict`: one normalized summary across all configured
     backends, same shape discipline as `GpuWorkerService.dashboard()`.
   - `dry_run(...) -> dict`: would a hypothetical local-serving request be
     accepted, declined, or need configuration — never actually sends an
     inference request.
   - Log planning/detection actions through `GovernanceService`, same as
     `GpuWorkerService`.
2. Route additions on the existing worker/GPU route module or a small new one:
   - `GET /api/model-serving/dashboard`
   - `POST /api/model-serving/dry-run`
   No mutation endpoints in this slice — nothing to approve yet because
   nothing writes or starts anything.
3. Tests: `backend/tests/test_model_serving_service.py`, plus a smoke check.
4. `analytics_summary()` on the new service, wired into `/api/analytics` like
   every other service.

## Explicitly out of scope for this slice (defer to a later, separate assignment)

- Actually starting, stopping, or supervising any local model server process.
- Downloading model weights.
- Installing or shelling out to `ollama`, `vllm`, or any CLI (no
  `subprocess`/`os.system` calls in this service at all — HTTP GET only,
  against operator-configured URLs).
- Proxying or forwarding real inference requests through EvolveAgent.
- Any new `*_ENABLED`/`*_EXECUTION_ENABLED` flag that would gate a real write
  — there is no real write in this slice, so no such flag should exist yet.
- Frontend work of any kind (frontend is owned separately; backend-only PR).
- Touching `AgentSchedulerService`, `DurableWorkflowService`'s action
  whitelist, or the model router — this slice does not wire local serving
  into request routing yet, it only reports readiness.

## Safety rules (same bar as v220-v240, tightened for this slice)

- No outbound call except a GET to an operator-configured local/loopback URL,
  short timeout (2-3s), never a POST that could mutate the target backend's
  state.
- If no backend URL is configured, `detect()` must return
  `reachable: false, configured: false` — never attempt a request.
- No secrets: if any backend needs an API key later, follow the existing
  pattern (env var only, booleans in responses, never the value) — but no
  backend in this slice should need one (Ollama et al. are typically
  keyless on loopback).
- Failed detection must never crash `/api/analytics` or the dashboard route.

## Test and verification plan

```bash
cd backend
python -m pytest tests/test_model_serving_service.py -q
python -m pytest -q   # full suite before merge
python scripts/smoke_test.py
```

Live verification: only check `detect()` against whatever is actually
reachable on the dev machine (may be nothing — `reachable: false` is a valid,
expected, fully-tested outcome, not a failure).

## Acceptance criteria

- No process is ever started by this code, under any configuration.
- `dashboard()`/`dry_run()` degrade safely with zero backends configured.
- New service follows the existing constructor-injection + `analytics_summary()`
  pattern exactly.
- Existing GPU/worker-registry tests and routes are untouched.

## Suggested PR sequence after this plan is approved

1. This plan doc (docs-only PR, for review).
2. Backend-only PR: `ModelServingService` + routes + tests (read-only,
   as scoped above).
3. Stop. Whether/how to actually wire real local inference (starting a
   server, routing requests to it) is a separate decision requiring its own
   scoping doc and explicit human sign-off — not an automatic next step from
   this slice.
