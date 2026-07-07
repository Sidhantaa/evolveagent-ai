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
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from app.config import settings
from app.services.scheduled_tasks_service import ScheduledTasksService


class SchedulerTickWorker:
    def __init__(self, scheduled_tasks: ScheduledTasksService):
        self.scheduled_tasks = scheduled_tasks
        self.running = False
        self._task: asyncio.Task | None = None
        self.last_tick_at: str | None = None
        self.last_error: str | None = None
        self.last_fired: list[dict[str, Any]] = []

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
        return fired

    def status(self) -> dict:
        return {
            "enabled": settings.scheduler_tick_enabled,
            "running": self.running,
            "interval_seconds": settings.scheduler_tick_interval_seconds,
            "last_tick_at": self.last_tick_at,
            "last_error": self.last_error,
            "last_fired": self.last_fired,
        }
