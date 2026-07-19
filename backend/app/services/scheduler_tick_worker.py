"""v120 — the first real background scheduler tick in the app.

Mirrors ``LinearPollWorker``'s exact shape: an ``asyncio`` loop, started/stopped
from the FastAPI lifespan, gated entirely by a settings flag that defaults to
**off**. When disabled (the default), ``start()`` is a no-op and nothing runs on
a timer — ``ScheduledTasksService`` behaves exactly as it always has (purely
on-demand). When explicitly enabled via ``SCHEDULER_TICK_ENABLED=true``, the loop
periodically calls ``due_tasks()`` and fires ``trigger()`` for each — the tasks
themselves remain whatever they always were: a planning-first mock note, or (v120)
a real durable-workflow run that is still fully governed by that engine's own
approval gates. The tick can start work; it can never approve it.

One bad task can never stop the loop — every trigger is isolated in a try/except
so a single failure is recorded and skipped, not fatal.

Each tick also sweeps AgentSchedulerService for genuinely stale running jobs
(real heartbeat-timeout detection that previously had no automated consumer)
and fails them for real -- isolated from due-task firing, optional collaborator.

Before that sweep, each tick also polls any in-flight KaggleWorkerService jobs
(previously only polled from the manual API route) so their agent_scheduler
heartbeat gets refreshed -- otherwise the stale-job sweep above would
eventually auto-fail a Kaggle kernel that is still genuinely running, since
nothing else was ever refreshing its heartbeat.

Each tick also calls AdaptiveLearningService.learn() -- the same shape of gap:
MasterOrchestratorAgent consults recommend() on every single run (an earlier
fix this session), but the one method that actually ingests fresh signal from
repo searches/high-grade evaluations/workflow effects was manual-button-only,
silently starving that now-automated consumer of anything learned since the
last time a human happened to click it.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.services.scheduled_tasks_service import ScheduledTasksService


_KAGGLE_NONTERMINAL_STATUSES = {"submitted", "running", "queued"}


class SchedulerTickWorker:
    def __init__(self, scheduled_tasks: ScheduledTasksService, agent_scheduler=None, kaggle_worker=None, adaptive_learning=None):
        self.scheduled_tasks = scheduled_tasks
        # Optional AgentSchedulerService collaborator. health() already does
        # real stale-heartbeat detection (a running job whose heartbeat hasn't
        # updated within its timeout) but previously had zero automated
        # consumer -- a run that died mid-step (uncaught exception, process
        # restart) before reaching complete/fail/pause left its job "running"
        # forever with nothing ever noticing. Each tick now fails any
        # genuinely stale job for real, using the engine's own already-real
        # fail() transition -- never touches jobs that are still healthy.
        self.agent_scheduler = agent_scheduler
        # Optional KaggleWorkerService collaborator. poll_job() was only ever
        # invoked from the manual API route, so a Kaggle kernel nobody polled
        # would eventually get its agent_scheduler job auto-failed as "stale
        # heartbeat" by the sweep above even while genuinely still running.
        # Each tick now refreshes every in-flight Kaggle job's real status
        # (and heartbeat) BEFORE the stale sweep runs.
        self.kaggle_worker = kaggle_worker
        # Optional AdaptiveLearningService collaborator. recommend() (real
        # retrieval memory) is consulted on every MasterOrchestratorAgent run,
        # but learn() -- the only thing that ingests fresh signal from repo
        # searches/high-grade evaluations/workflow effects -- was manual-only
        # (POST /adaptive-learning/learn). Each tick now keeps it current for
        # free; idempotent (learn() dedupes via its own fingerprinting).
        self.adaptive_learning = adaptive_learning
        self.running = False
        self._task: asyncio.Task | None = None
        self.last_tick_at: str | None = None
        self.last_error: str | None = None
        self.last_fired: list[dict[str, Any]] = []
        self.last_stale_jobs_failed: list[dict[str, Any]] = []
        self.last_kaggle_jobs_polled: list[dict[str, Any]] = []
        self.last_learn_result: dict[str, Any] | None = None
        self.last_auto_dispatched: list[dict[str, Any]] = []

    async def start(self) -> None:
        if self.running or not settings.scheduler_tick_enabled:
            return
        self.running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self.running = False
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _loop(self) -> None:
        while self.running:
            await asyncio.to_thread(self.tick_once)
            await asyncio.sleep(max(settings.scheduler_tick_interval_seconds, 15))

    def tick_once(self) -> list[dict[str, Any]]:
        """Fire every currently-due task once. This is the real unit of work —
        it is NOT gated on ``scheduler_tick_enabled`` itself, because a direct
        call here is always an explicit, human-initiated action (e.g. the
        ``/tick-now`` endpoint, or a test), same as clicking 'trigger' on each
        due task individually. Only the *autonomous* background loop (``_loop``,
        started only from ``start()``) is gated on the flag."""
        self.last_tick_at = datetime.now(UTC).isoformat()
        self.last_error = None
        fired: list[dict[str, Any]] = []
        try:
            due = self.scheduled_tasks.due_tasks()
        except Exception as exc:  # noqa: BLE001 — never let a read failure kill the loop
            self.last_error = f"due_tasks() failed: {type(exc).__name__}: {exc}"
            self.last_fired = fired
            return fired
        for item in due:
            task_id = item.get("task_id")
            try:
                run = self.scheduled_tasks.trigger(task_id)
                fired.append({"task_id": task_id, "name": item.get("name"), "status": run.get("status")})
            except Exception as exc:  # noqa: BLE001 — isolate one bad task from the rest
                fired.append({"task_id": task_id, "name": item.get("name"), "status": "error", "error": str(exc)})
        self.last_fired = fired
        self.last_kaggle_jobs_polled = self._poll_kaggle_jobs()
        self.last_stale_jobs_failed = self._fail_stale_jobs()
        self.last_learn_result = self._learn_from_history()
        self.last_auto_dispatched = self._auto_dispatch_jobs()
        return fired

    def _auto_dispatch_jobs(self) -> list[dict[str, Any]]:
        """v280 target 2: AgentSchedulerService.start_next() already atomically
        enforces concurrency_limit, but nothing automated ever called it --
        only a manual API route did, so a queued job waited forever for a
        human to dequeue it one at a time. Gated on its OWN flag
        (AGENT_SCHEDULER_AUTO_DISPATCH_ENABLED, default off) rather than
        inheriting the other sweeps' "always runs on an explicit tick_once()
        call" behavior, because auto-starting previously-manual jobs is a
        genuine behavior change, not cleanup of already-dead state like the
        stale-job sweep. Isolated from everything else -- a broken dispatch
        can never affect due-task firing or either sweep above, and one bad
        start_next() call can never lose jobs already dispatched this tick."""
        if self.agent_scheduler is None or not settings.agent_scheduler_auto_dispatch_enabled:
            return []
        started: list[dict[str, Any]] = []
        for _ in range(50):  # hard safety cap -- never an unbounded loop, even if a future bug broke concurrency_limit
            try:
                job = self.agent_scheduler.start_next()
            except Exception:  # noqa: BLE001
                break
            if job is None:
                break
            started.append({"job_id": job.get("job_id"), "title": job.get("title")})
        return started

    def _learn_from_history(self) -> dict[str, Any] | None:
        """Isolated from everything else -- a broken learn() call can never
        affect due-task firing or either sweep above."""
        if self.adaptive_learning is None:
            return None
        try:
            return self.adaptive_learning.learn()
        except Exception:  # noqa: BLE001
            return None

    def _poll_kaggle_jobs(self) -> list[dict[str, Any]]:
        """Isolated from everything else -- a broken Kaggle poll can never
        affect due-task firing or the stale-job sweep, and runs BEFORE that
        sweep so a freshly-refreshed heartbeat prevents a false stale-fail in
        the same tick."""
        if self.kaggle_worker is None:
            return []
        polled: list[dict[str, Any]] = []
        try:
            jobs = self.kaggle_worker.list_jobs(limit=50)
        except Exception:  # noqa: BLE001
            return polled
        for job in jobs:
            if job.get("status") not in _KAGGLE_NONTERMINAL_STATUSES:
                continue
            job_id = job.get("job_id")
            try:
                updated = self.kaggle_worker.poll_job(job_id)
                polled.append({"job_id": job_id, "status": updated.get("status")})
                # The job's stored status was still non-terminal before this
                # poll (the filter above), so a "complete" result here is
                # this job's first-ever completion -- on every later tick
                # it's already terminal and skipped by that same filter, so
                # this fires exactly once per job.
                if updated.get("status") == "complete":
                    self._mirror_kaggle_completion(updated)
            except Exception:  # noqa: BLE001 — one bad job can never stop the sweep
                continue
        return polled

    def _mirror_kaggle_completion(self, job: dict[str, Any]) -> None:
        """A completed real GPU job's output previously had no downstream
        consumer beyond the manual /output route -- mirror it into Adaptive
        Learning's retrieval memory (same idiom WorkspaceService/GoalService
        already use for their own real-content mirrors) so a future run can
        actually recall it. Best-effort; never raises into the caller."""
        if self.adaptive_learning is None or self.kaggle_worker is None:
            return
        try:
            output = self.kaggle_worker.get_job_output(job["job_id"])
            if not output.get("downloaded"):
                return
            files = ", ".join(output.get("files") or []) or "no output files"
            self.adaptive_learning.ingest(
                f"Kaggle job '{job.get('title')}' ({job.get('kernel_ref')}) completed -- output: {files}",
                kind="reference",
                source="kaggle_worker",
            )
        except Exception:  # noqa: BLE001
            pass

    def _fail_stale_jobs(self) -> list[dict[str, Any]]:
        """Isolated from due-task firing above -- a failure here must never
        affect it, and vice versa."""
        if self.agent_scheduler is None:
            return []
        failed: list[dict[str, Any]] = []
        try:
            stale = self.agent_scheduler.health().get("stale_running_jobs", [])
        except Exception:  # noqa: BLE001
            return failed
        for job in stale:
            job_id = job.get("job_id")
            try:
                self.agent_scheduler.fail(job_id, error="Stale heartbeat — no progress reported within timeout.")
                failed.append({"job_id": job_id, "title": job.get("title")})
            except Exception:  # noqa: BLE001 — one bad job can never stop the sweep
                continue
        return failed

    def status(self) -> dict:
        return {
            "enabled": settings.scheduler_tick_enabled,
            "running": self.running,
            "interval_seconds": settings.scheduler_tick_interval_seconds,
            "last_tick_at": self.last_tick_at,
            "last_error": self.last_error,
            "last_fired": self.last_fired,
            "last_stale_jobs_failed": self.last_stale_jobs_failed,
            "last_kaggle_jobs_polled": self.last_kaggle_jobs_polled,
            "last_learn_result": self.last_learn_result,
            "auto_dispatch_enabled": settings.agent_scheduler_auto_dispatch_enabled,
            "last_auto_dispatched": self.last_auto_dispatched,
        }
