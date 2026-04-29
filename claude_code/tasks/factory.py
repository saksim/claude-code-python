"""Factory helpers for task middleware backend selection."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from claude_code.services.event_journal import EventJournal
from claude_code.tasks.queue import InMemoryTaskQueue, TaskQueue
from claude_code.tasks.repository import (
    RuntimeTaskRepository,
    create_file_runtime_task_repository,
    create_sqlite_runtime_task_repository,
)

QueueBackend = Literal["memory", "redis"]
RuntimeBackend = Literal["sqlite", "file", "none"]


@dataclass(frozen=True, slots=True)
class TaskBackendConfig:
    """Backend configuration for task middleware."""

    working_directory: str | Path
    queue_backend: QueueBackend = "memory"
    runtime_backend: RuntimeBackend = "sqlite"


def create_task_queue(backend: QueueBackend = "memory") -> TaskQueue:
    """Create task queue by backend name."""
    if backend == "memory":
        return InMemoryTaskQueue()
    if backend == "redis":
        raise RuntimeError(
            "Redis queue backend is not wired yet. "
            "Next phase will provide RedisTaskQueue implementation."
        )
    raise ValueError(f"Unknown queue backend: {backend}")


def create_runtime_repository(
    working_directory: str | Path,
    backend: RuntimeBackend = "sqlite",
) -> Optional[RuntimeTaskRepository]:
    """Create runtime repository by backend name."""
    if backend == "none":
        return None
    if backend == "sqlite":
        return create_sqlite_runtime_task_repository(working_directory)
    if backend == "file":
        return create_file_runtime_task_repository(working_directory)
    raise ValueError(f"Unknown runtime backend: {backend}")


def create_task_manager(config: TaskBackendConfig):
    """Create TaskManager with selected queue and runtime backends."""
    from claude_code.tasks.manager import TaskManager

    queue = create_task_queue(config.queue_backend)
    runtime_repository = create_runtime_repository(
        config.working_directory,
        config.runtime_backend,
    )
    return TaskManager(task_queue=queue, runtime_repository=runtime_repository)


def create_task_manager_with_event_journal(
    config: TaskBackendConfig,
    event_journal: EventJournal,
):
    """Create TaskManager with selected backends and event journal."""
    from claude_code.tasks.manager import TaskManager

    queue = create_task_queue(config.queue_backend)
    runtime_repository = create_runtime_repository(
        config.working_directory,
        config.runtime_backend,
    )
    return TaskManager(
        task_queue=queue,
        runtime_repository=runtime_repository,
        event_journal=event_journal,
    )


__all__ = [
    "QueueBackend",
    "RuntimeBackend",
    "TaskBackendConfig",
    "create_task_queue",
    "create_runtime_repository",
    "create_task_manager",
    "create_task_manager_with_event_journal",
]
