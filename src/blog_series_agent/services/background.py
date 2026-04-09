"""Background task execution for long-running pipeline operations."""

from __future__ import annotations

import logging
import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class BackgroundTaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackgroundTask:
    task_id: str
    status: BackgroundTaskStatus = BackgroundTaskStatus.PENDING
    result: object = None
    error: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None


class BackgroundExecutor:
    """Runs pipeline operations in background threads with status tracking."""

    def __init__(self, max_workers: int = 2) -> None:
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="bg-pipeline")
        self._tasks: dict[str, BackgroundTask] = {}
        self._futures: dict[str, Future] = {}
        self._lock = threading.Lock()

    def submit(self, task_id: str, fn, *args, **kwargs) -> BackgroundTask:
        """Submit a callable to run in the background."""
        task = BackgroundTask(task_id=task_id, status=BackgroundTaskStatus.RUNNING)
        with self._lock:
            self._tasks[task_id] = task

        future = self._executor.submit(fn, *args, **kwargs)
        self._futures[task_id] = future
        future.add_done_callback(lambda f: self._on_complete(task_id, f))
        return task

    def get_task(self, task_id: str) -> BackgroundTask | None:
        with self._lock:
            return self._tasks.get(task_id)

    def list_tasks(self) -> list[BackgroundTask]:
        with self._lock:
            return list(self._tasks.values())

    def _on_complete(self, task_id: str, future: Future) -> None:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return
            task.completed_at = datetime.now(timezone.utc)
            try:
                task.result = future.result()
                task.status = BackgroundTaskStatus.COMPLETED
            except Exception as exc:
                task.error = str(exc)
                task.status = BackgroundTaskStatus.FAILED
                logger.exception("Background task %s failed", task_id)

    def shutdown(self, wait: bool = True) -> None:
        self._executor.shutdown(wait=wait)
