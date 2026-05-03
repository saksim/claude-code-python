"""Runtime tests for task backend factory."""

from __future__ import annotations

import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path

import pytest

from claude_code.tasks.factory import (
    TaskBackendConfig,
    create_runtime_repository,
    create_task_manager,
    create_task_queue,
)
from claude_code.tasks.queue import InMemoryTaskQueue
from claude_code.tasks.repository import SQLiteRuntimeTaskRepository


@contextmanager
def _temp_runtime_workdir():
    base = Path(".claude") / "perf_tmp" / f"factory_{uuid.uuid4().hex}"
    base.mkdir(parents=True, exist_ok=True)
    try:
        yield base
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_factory_creates_memory_queue():
    queue = create_task_queue("memory")
    assert isinstance(queue, InMemoryTaskQueue)


def test_factory_redis_backend_not_yet_wired():
    with pytest.raises(RuntimeError, match="not wired yet"):
        create_task_queue("redis")


def test_factory_creates_runtime_repository_and_manager():
    with _temp_runtime_workdir() as workdir:
        repo = create_runtime_repository(workdir, "sqlite")
        assert repo is not None
        assert isinstance(repo, SQLiteRuntimeTaskRepository)

        manager = create_task_manager(
            TaskBackendConfig(
                working_directory=workdir,
                queue_backend="memory",
                runtime_backend="sqlite",
            )
        )
        stats = manager.get_stats()
        assert stats["recovered"] == 0
