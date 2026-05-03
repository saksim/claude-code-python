"""Runtime tests for TaskManager queue and state machine behavior."""

from __future__ import annotations

import asyncio
import shutil
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

import pytest

from claude_code.tasks.manager import TaskManager, TaskStateTransitionError
from claude_code.tasks.queue import InMemoryTaskQueue
from claude_code.tasks.repository import (
    create_file_runtime_task_repository,
    create_sqlite_runtime_task_repository,
)
from claude_code.tasks.types import TaskResult, TaskStatus, BashTask, create_task_from_dict


@contextmanager
def _temp_runtime_workdir():
    base = Path(".claude") / "perf_tmp" / f"runtime_{uuid.uuid4().hex}"
    base.mkdir(parents=True, exist_ok=True)
    try:
        yield base
    finally:
        shutil.rmtree(base, ignore_errors=True)


@pytest.mark.asyncio
async def test_start_task_requires_executor():
    manager = TaskManager(task_queue=InMemoryTaskQueue())
    task = await manager.create_bash_task(command="echo hi")

    with pytest.raises(ValueError, match="executor is required"):
        await manager.start_task(task.id)

    assert task.status == TaskStatus.PENDING


@pytest.mark.asyncio
async def test_start_task_rejects_invalid_state_transition():
    manager = TaskManager(task_queue=InMemoryTaskQueue())
    task = await manager.create_agent_task(prompt="long running")

    async def _slow_executor(_task):
        await asyncio.sleep(0.1)
        return TaskResult(code=0, stdout="ok")

    await manager.start_task(task.id, executor=_slow_executor)
    await asyncio.sleep(0.01)

    with pytest.raises(TaskStateTransitionError):
        await manager.start_task(task.id, executor=_slow_executor)

    await manager.wait_for_task(task.id, timeout=1.0)
    assert task.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_cancel_completed_task_returns_false():
    manager = TaskManager(task_queue=InMemoryTaskQueue())
    task = await manager.create_bash_task(command="echo done")

    async def _ok_executor(_task):
        return TaskResult(code=0, stdout="done")

    await manager.start_task(task.id, executor=_ok_executor)
    await manager.wait_for_task(task.id, timeout=1.0)
    assert task.status == TaskStatus.COMPLETED

    cancelled = await manager.cancel_task(task.id)
    assert cancelled is False
    assert task.status == TaskStatus.COMPLETED


@pytest.mark.asyncio
async def test_task_manager_stats_track_lifecycle():
    manager = TaskManager(task_queue=InMemoryTaskQueue())
    success_task = await manager.create_bash_task(command="echo success")
    fail_task = await manager.create_agent_task(prompt="fail task")

    async def _ok_executor(_task):
        return TaskResult(code=0, stdout="ok")

    async def _fail_executor(_task):
        raise RuntimeError("boom")

    await manager.start_task(success_task.id, executor=_ok_executor)
    await manager.start_task(fail_task.id, executor=_fail_executor)

    await manager.wait_for_task(success_task.id, timeout=1.0)
    await manager.wait_for_task(fail_task.id, timeout=1.0)

    stats = manager.get_stats()
    assert stats["created"] == 2
    assert stats["queued"] == 2
    assert stats["started"] == 2
    assert stats["completed"] == 1
    assert stats["failed"] == 1
    assert stats["queue_size"] == 0


@pytest.mark.asyncio
async def test_task_manager_retry_policy_requeues_and_succeeds():
    manager = TaskManager(task_queue=InMemoryTaskQueue())
    task = await manager.create_bash_task(command="echo retry")
    attempts = {"count": 0}

    async def _flaky_executor(_task):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("transient failure")
        return TaskResult(code=0, stdout="ok after retry")

    await manager.start_task(task.id, executor=_flaky_executor, max_retries=1)
    await manager.wait_for_task(task.id, timeout=1.0)

    assert task.status == TaskStatus.COMPLETED
    assert attempts["count"] == 2

    stats = manager.get_stats()
    assert stats["retried"] == 1
    assert stats["retry_rate"] > 0


@pytest.mark.asyncio
async def test_task_manager_observability_rates_include_failure_and_timeout():
    manager = TaskManager(task_queue=InMemoryTaskQueue())
    fail_task = await manager.create_agent_task(prompt="fail task")
    timeout_task = await manager.create_bash_task(command="timeout task")

    async def _fail_executor(_task):
        raise RuntimeError("boom")

    async def _timeout_executor(_task):
        raise asyncio.TimeoutError()

    await manager.start_task(fail_task.id, executor=_fail_executor)
    await manager.start_task(timeout_task.id, executor=_timeout_executor)
    await manager.wait_for_task(fail_task.id, timeout=1.0)
    await manager.wait_for_task(timeout_task.id, timeout=1.0)

    stats = manager.get_stats()
    assert stats["failed"] == 1
    assert stats["timed_out"] == 1
    assert stats["failure_rate"] == pytest.approx(0.5)
    assert stats["timeout_rate"] == pytest.approx(0.5)
    assert stats["queue_backlog"] >= 0
    assert stats["queue_lag_avg_ms"] >= 0
    assert stats["task_exec_avg_ms"] >= 0


@pytest.mark.asyncio
async def test_task_manager_idempotency_reuses_existing_task():
    manager = TaskManager(task_queue=InMemoryTaskQueue())

    first = await manager.create_bash_task(
        command="echo first",
        idempotency_key="bash-task-key",
    )
    second = await manager.create_bash_task(
        command="echo second",
        idempotency_key="bash-task-key",
    )

    assert first.id == second.id

    stats = manager.get_stats()
    assert stats["created"] == 1
    assert stats["idempotency_keys"] == 1


@pytest.mark.asyncio
async def test_runtime_repository_persists_task_lifecycle():
    with _temp_runtime_workdir() as workdir:
        runtime_repo = create_file_runtime_task_repository(workdir)
        manager = TaskManager(
            task_queue=InMemoryTaskQueue(),
            runtime_repository=runtime_repo,
        )

        task = await manager.create_bash_task(command="echo persist")
        pending_record = runtime_repo.get_task_record(task.id)
        assert pending_record is not None
        assert pending_record["status"] == "pending"

        async def _ok_executor(_task):
            return TaskResult(code=0, stdout="persisted")

        await manager.start_task(task.id, executor=_ok_executor)
        await manager.wait_for_task(task.id, timeout=1.0)

        completed_record = runtime_repo.get_task_record(task.id)
        assert completed_record is not None
        assert completed_record["status"] == "completed"
        assert completed_record["result"]["stdout"] == "persisted"

        cleared = manager.clear_completed()
        assert cleared == 1
        assert runtime_repo.get_task_record(task.id) is None


@pytest.mark.asyncio
async def test_sqlite_runtime_repository_persists_task_lifecycle():
    with _temp_runtime_workdir() as workdir:
        runtime_repo = create_sqlite_runtime_task_repository(workdir)
        manager = TaskManager(
            task_queue=InMemoryTaskQueue(),
            runtime_repository=runtime_repo,
        )

        task = await manager.create_bash_task(command="echo persist sqlite")
        pending_record = runtime_repo.get_task_record(task.id)
        assert pending_record is not None
        assert pending_record["status"] == "pending"

        async def _ok_executor(_task):
            return TaskResult(code=0, stdout="persisted-sqlite")

        await manager.start_task(task.id, executor=_ok_executor)
        await manager.wait_for_task(task.id, timeout=1.0)

        completed_record = runtime_repo.get_task_record(task.id)
        assert completed_record is not None
        assert completed_record["status"] == "completed"
        assert completed_record["result"]["stdout"] == "persisted-sqlite"

        cleared = manager.clear_completed()
        assert cleared == 1
        assert runtime_repo.get_task_record(task.id) is None


def test_create_task_from_dict_handles_bash_description():
    payload = {
        "id": "task-1",
        "type": "local_bash",
        "command": "echo hello",
        "status": "pending",
        "description": "custom bash description",
    }

    task = create_task_from_dict(payload)
    assert isinstance(task, BashTask)
    assert task.description == "custom bash description"


@pytest.mark.asyncio
async def test_manager_recovers_inflight_task_as_failed():
    with _temp_runtime_workdir() as workdir:
        runtime_repo = create_file_runtime_task_repository(workdir)
        seed_manager = TaskManager(
            task_queue=InMemoryTaskQueue(),
            runtime_repository=runtime_repo,
        )

        task = await seed_manager.create_bash_task(
            command="echo recover me",
            idempotency_key="recover-key",
        )
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        runtime_repo.upsert_task(task)

        recovered_manager = TaskManager(
            task_queue=InMemoryTaskQueue(),
            runtime_repository=runtime_repo,
        )

        recovered = recovered_manager.get_task(task.id)
        assert recovered is not None
        assert recovered.status == TaskStatus.FAILED
        assert "recovered after process restart" in (recovered.error or "")
        assert recovered_manager.get_stats()["recovered"] >= 1
        assert recovered_manager.get_stats()["idempotency_keys"] == 1

        record = runtime_repo.get_task_record(task.id)
        assert record is not None
        assert record["status"] == "failed"


@pytest.mark.asyncio
async def test_manager_recovers_inflight_task_as_failed_with_sqlite_repo():
    with _temp_runtime_workdir() as workdir:
        runtime_repo = create_sqlite_runtime_task_repository(workdir)
        seed_manager = TaskManager(
            task_queue=InMemoryTaskQueue(),
            runtime_repository=runtime_repo,
        )

        task = await seed_manager.create_bash_task(
            command="echo recover sqlite",
            idempotency_key="recover-sqlite-key",
        )
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        runtime_repo.upsert_task(task)

        recovered_manager = TaskManager(
            task_queue=InMemoryTaskQueue(),
            runtime_repository=runtime_repo,
        )

        recovered = recovered_manager.get_task(task.id)
        assert recovered is not None
        assert recovered.status == TaskStatus.FAILED
        assert "recovered after process restart" in (recovered.error or "")
        assert recovered_manager.get_stats()["recovered"] >= 1
        assert recovered_manager.get_stats()["idempotency_keys"] == 1

        record = runtime_repo.get_task_record(task.id)
        assert record is not None
        assert record["status"] == "failed"
