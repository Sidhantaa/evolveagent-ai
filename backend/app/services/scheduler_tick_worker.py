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
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.services.scheduled_tasks_service import ScheduledTasksService


class SchedulerTickWorker:
    def __init__(self, scheduled_tasks: ScheduledTasksService, agent_scheduler=None):
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
        self.running = False
        self._task: asyncio.Task | None = None
        self.last_tick_at: str | None = None
        self.last_error: str | None = None
        self.last_fired: list[dict[str, Any]] = []
        self.last_stale_jobs_failed: list[dict[str, Any]] = []

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
        self.last_stale_jobs_failed = self._fail_stale_jobs()
        return fired

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
        }
