# Codex Assignment — v240 GPU Worker Expansion Plan

**Status:** PLAN ONLY. Do not implement v240 from this document yet.

This PR is a review checkpoint for EvolveAgent v240: local + cloud GPU worker
expansion. The goal is to define the smallest useful slice before any code is
written, so the implementation can be approved, tested, and budget-gated
instead of becoming a broad distributed-compute rewrite.

Read `docs/CODEX_HANDOFF.md` first for general repo conventions and safety
rules. Read the current worker code before implementing any future v240 branch:

- `backend/app/services/worker_registry_service.py`
- `backend/app/services/kaggle_worker_service.py`
- `backend/app/api/worker_registry_routes.py`
- `backend/tests/test_kaggle_worker_service.py`

## Existing foundation to reuse

v220 already shipped the first real Compute Fabric pieces:

1. `WorkerRegistryService`
   - Persists workers in `compute_workers.json`.
   - Supports register, heartbeat, list, deregister, dashboard, analytics.
   - Does not run jobs itself.
   - Uses `StorageService.update_list()` for heartbeat/deregister so concurrent
     worker updates do not lose writes.

2. `KaggleWorkerService`
   - Persists jobs in `kaggle_worker_jobs.json`.
   - Real, opt-in Kaggle GPU adapter using the allowlisted `kaggle` CLI.
   - Disabled by default via `KAGGLE_WORKER_ENABLED=false`.
   - Submits, polls, and downloads Kaggle kernel output.
   - Registers submitted workers with `WorkerRegistryService`.
   - Deregisters terminal Kaggle workers on complete/error.
   - Integrates with `AgentSchedulerService` when present.

3. `worker_registry_routes.py`
   - Exposes `/api/worker-registry/*`.
   - Existing Kaggle job endpoint safely declines when Kaggle is disabled.

v240 must extend these pieces. Do not create a parallel worker system.

## What v240 means

v240 means EvolveAgent can describe, register, inspect, and safely plan work
for GPU workers across local and cloud-backed environments, while preserving
the current approval-first execution model.

Concrete scope:

- Add provider-neutral GPU worker capability metadata to the existing worker
  registry model.
- Add a small coordinator service that summarizes available GPU providers and
  worker readiness.
- Treat Kaggle as the first real provider adapter.
- Add local/manual GPU worker registration support for machines the user
  controls.
- Add cloud provider readiness/dry-run cards without executing paid GPU work.
- Keep real provider execution disabled by default and human-approved.

The first implementation should answer:

- Which GPU workers exist?
- Which provider backs each worker?
- What capabilities do they advertise?
- Is a provider configured?
- Is real execution enabled?
- Would a proposed job be accepted, declined, or require approval?
- What cost/risk warning should the user see before execution?

The first implementation should not try to become Kubernetes, Ray, Celery, or
a full model-serving platform.

## Proposed implementation slice

### 1. Backward-compatible registry metadata

Extend worker metadata through the existing `WorkerRegistryService` entry shape
without breaking current callers:

- `provider`: `local | kaggle | runpod | lambda_labs | modal | replicate | other`
- `gpu_model`
- `gpu_memory_gb`
- `region`
- `runtime`: `python | container | notebook | openai_compatible | unknown`
- `supports_jobs`
- `supports_model_serving`
- `estimated_cost_per_hour`
- `quota_state`
- `requires_approval`
- `last_provider_check`

Existing workers with only `worker_type`, `capabilities`, and `metadata` must
continue to render and pass tests.

### 2. GPU worker coordinator service

Add a small service such as:

- `backend/app/services/gpu_worker_service.py`

Responsibilities:

- Read from `WorkerRegistryService`.
- Read status from `KaggleWorkerService.status()`.
- Build one normalized GPU dashboard.
- Produce dry-run execution plans.
- Decline real cloud execution unless the provider is explicitly enabled.
- Log stateful/planning actions through `GovernanceService`.

This service should coordinate existing adapters; it should not replace
`WorkerRegistryService` or `KaggleWorkerService`.

### 3. Local/manual GPU workers

For this slice, local GPU support should be manual or status-only.

Acceptable:

- User registers a local GPU worker through the existing registry API with
  richer metadata.
- Optional read-only status endpoint shows manual/local workers.
- Future auto-detection can be planned separately.

Avoid in v240:

- Running shell probes such as `nvidia-smi`.
- Installing GPU drivers.
- Starting model servers.
- Managing local containers.

### 4. Cloud provider readiness and dry-run

Add provider status records for future cloud adapters, but do not trigger real
billing by default.

Provider status should expose:

- `provider`
- `enabled`
- `configured`
- `execution_enabled`
- `supports_gpu_jobs`
- `supports_cancellation`
- `risk_level`
- `cost_warning`
- `required_env_vars` as names only, never values

Dry-run should return a plan such as:

- `accepted`: boolean
- `requires_approval`: boolean
- `declined_reason`
- `provider`
- `estimated_cost_note`
- `missing_configuration`
- `next_human_action`

Only Kaggle has an existing real adapter. Additional providers can be
readiness-only in v240.

### 5. API surface

Prefer extending the existing worker route module:

- `GET /api/worker-registry/gpu/dashboard`
- `GET /api/worker-registry/gpu/providers`
- `POST /api/worker-registry/gpu/dry-run`
- `POST /api/worker-registry/gpu/local-workers`

Do not remove or rename existing v220 endpoints.

### 6. Frontend surface

If frontend is included in the implementation PR, keep it Developer Mode only.

Suggested UI:

- GPU readiness card in the existing compute/worker area.
- Provider cards: local, Kaggle, future cloud providers.
- Worker table with GPU model, provider, status, quota/cost warning.
- Dry-run form that shows whether a GPU job would be accepted, declined, or
  approval-gated.
- Clear warning when a provider could create real external cost.

Simple Mode should remain clean.

## Files likely touched in a future implementation PR

Backend:

- `backend/app/services/worker_registry_service.py`
- `backend/app/services/kaggle_worker_service.py`
- `backend/app/services/gpu_worker_service.py` (new)
- `backend/app/api/worker_registry_routes.py`
- `backend/app/models/request_models.py`
- `backend/app/config.py`
- `backend/app/services/storage_service.py` if a new runtime collection is
  needed
- `.gitignore` if a new runtime collection is added

Tests:

- `backend/tests/test_gpu_worker_service.py` (new)
- `backend/tests/test_kaggle_worker_service.py`
- `scripts/smoke_test.py` if new smoke checks are added

Frontend, only if included:

- `frontend/src/data/api.ts`
- Existing Developer Mode / compute fabric page or panel components
- The relevant frontend test file for API mapper/UI behavior

## Explicitly out of scope for v240

Defer these to v250/v260+:

- Kubernetes, Ray, Dask, Celery, Temporal, or distributed queue migration.
- Automatic cloud GPU provisioning.
- Paid provider execution without a separate approval flow.
- Model serving or OpenAI-compatible local endpoint hosting.
- Multi-GPU scheduling or packing algorithms.
- Parallel multi-agent execution.
- Autoscaling.
- Cluster networking.
- Credential vault work.
- Browser/device automation.
- Provider-specific cancellation guarantees beyond what an adapter already
  supports.
- Training/fine-tuning jobs.
- Any rewrite of `AgentSchedulerService`, durable workflows, or storage
  backends.

## External cost and risk considerations

This feature touches systems that can create real cloud GPU cost. That changes
the safety bar.

Rules for any future implementation:

- All real cloud execution is disabled by default.
- Every provider needs an explicit `*_ENABLED=true` flag.
- Every paid provider needs a separate `*_EXECUTION_ENABLED=true` or equivalent
  flag before job submission is even eligible.
- API keys/tokens are read only from environment variables and are never
  returned, stored, logged, or shown in UI.
- Status responses may expose booleans such as `configured: true`, never secret
  values.
- Real job submission must route through the existing approval/durable workflow
  pattern. Dry-run and readiness checks can be read-only.
- Cost estimates are warnings, not guarantees.
- If cancellation cannot be guaranteed, the UI/API must say so before approval.
- Failed provider calls must degrade safely and never crash the whole app.

Human approval required before wiring any provider that can:

- Start a paid GPU instance.
- Submit a paid job.
- Read private cloud account metadata.
- Upload project files to a third-party GPU provider.
- Keep a worker alive after a request completes.

## Test and verification plan

Targeted backend tests:

```bash
cd backend
python -m pytest tests/test_gpu_worker_service.py tests/test_kaggle_worker_service.py -q
```

Regression tests for related orchestration, if routes touch scheduler or durable
workflow code:

```bash
cd backend
python -m pytest tests/test_scheduler_tick_worker.py tests/test_durable_workflow_service.py -q
```

Full backend before merge:

```bash
cd backend
python -m pytest -q
```

Frontend, if UI is touched:

```bash
cd frontend
npm test
npm run build
```

Smoke test:

```bash
cd backend
python scripts/smoke_test.py
```

Live verification:

- Manual/local worker registration should be verified without secrets.
- Kaggle live submission should only be tested if a human explicitly confirms
  `KAGGLE_WORKER_ENABLED=true`, Kaggle credentials are configured outside the
  app, and the job is approved.
- Any paid cloud provider live test should be skipped until a separate human
  approval confirms billing risk.

## Acceptance criteria for v240 implementation

- Existing `/api/worker-registry/*` and Kaggle tests still pass.
- Existing Kaggle behavior is unchanged except for added dashboard visibility.
- GPU dashboard can show local/manual workers and provider readiness.
- Dry-run explains whether a GPU job is accepted, declined, or approval-gated.
- No real paid GPU work runs by default.
- No secrets appear in logs, API responses, governance events, or UI.
- Governance events record meaningful stateful planning/registration actions.
- Simple Mode remains clean.

## Suggested PR sequence after this plan is approved

1. Backend-only PR: schema-compatible GPU metadata + coordinator service +
   tests.
2. API PR: worker-registry GPU endpoints + smoke checks.
3. Frontend PR: Developer Mode GPU readiness/dry-run panel.
4. Optional live-adapter PR: additional provider adapter, gated by explicit
   env flags and human approval.

Stop after each PR and verify CI before moving to the next.
