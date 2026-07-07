# Codex Assignment — EvolveAgent v100 (Parallel Track)

**Context:** EvolveAgent AI is in v100 ("Real Foundation"). **Claude owns the
storage/DB core** (Postgres backend, migration, Memory v2, Agent Registry, Redis).
**You (Codex) work the parallel track: real connectors + frontend.** Read
`docs/CODEX_HANDOFF.md` first for architecture, patterns, safety, and PR cadence.

## 🚫 Do NOT touch (Claude owns — would cause merge conflicts)
- `backend/app/storage/**`
- `backend/app/services/storage_service.py`
- `backend/alembic/**`
- the `storage_backend` / `database_url` / `redis_url` fields in `backend/app/config.py`
- any new `memory_service.py` / `agent_registry_service.py`
- Do NOT add DB / Postgres / Redis code anywhere.

## ✅ You OWN
`frontend/**`, **new** connector service files in `backend/app/services/`, their
route modules, their tests, and `docs/`.

---

## Task C1 (start now — fully independent): real GitHub connector
Read-only, governed GitHub connector so EVA can see a user's real repos/issues/PRs.

- **New** `backend/app/services/github_connector_service.py` (do NOT modify
  `git_discovery_service` or `repo_finder_service`).
- Uses the GitHub REST API via stdlib `urllib` — **copy the safety pattern from
  `repo_finder_service.py`**. Token from `GITHUB_TOKEN` env only; **never stored,
  logged, or returned** (status exposes a boolean). **Graceful degradation** to a
  note when offline / no token (never 500).
- Methods: `status()`, `list_repos()`, `list_issues(repo)`, `list_pull_requests(repo)`,
  `summary()`. **Read-only — no writes** (creating issues/PRs is a later,
  approval-gated task).
- Governance-logged (`GovernanceService.log_event`); analytics merged into `/api/analytics`.
- **New** `backend/app/api/github_connector_routes.py`
  (`/api/github/{status,repos,issues,pulls,summary}`), registered in `main.py`
  the same way as the other split routers.
- **New** `backend/tests/test_github_connector_service.py` — mock the HTTP layer
  (patch a `_http_get` method, like `test_repo_finder_service.py`): test mapping,
  secret-safety (boolean only), graceful degradation. Add 1–2 checks to
  `scripts/smoke_test.py`.

## Task C2 (after Claude's task 5 lands on main): Storage-status card
Claude will expose **`GET /api/system/storage-status`** returning:
```json
{ "backend": "json", "collections": 210, "total_documents": 12345, "postgres_ready": false, "redis_ready": false }
```
Build a **"Storage" card in the Dev Console** (`frontend/src/pages/DevModeConsole.tsx`)
+ `fetchStorageStatus()` in `frontend/src/data/api.ts` + a Vitest test. Show backend
kind (JSON/Postgres pill), collection/doc counts, PG/Redis readiness dots. **Do not
start until the endpoint is on `main`.**

---

## Rules
- Follow the **safety contract**: read-only, secret-safe (booleans only, never raw
  keys), governance-logged, no autonomous external mutation.
- **PR cadence:** branch per task off latest `main`;
  `cd backend && python -m pytest tests/test_github_connector_service.py -q`;
  `cd frontend && npm ci && npm run test && npm run build`; commit only intended
  files (**never `git add -A`**; no `Co-Authored-By` trailer); push; `gh pr create`;
  merge with `gh pr merge <#> --admin --merge --delete-branch` **only after CI is
  green** (leave the PR open if red).
- **Response format** per task: use the 12-step format the product owner defined
  (what / why / files to check / backend / frontend / storage / governance / API /
  tests / steps / risks / future).

**Deliver C1 first, report the PR number, then wait for the storage-status endpoint
before starting C2.**
