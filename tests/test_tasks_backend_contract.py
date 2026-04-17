"""Backend contract tests for queue and runtime repositories."""

from __future__ import annotations

import shutil
import uuid
from contextlib import contextmanager
from pathlib import Path

import pytest

from claude_code.tasks.queue import InMemoryTaskQueue, QueueItem
from claude_code.tasks.repository import create_file_runtime_task_repository
from claude_code.tasks.types import BashTask, TaskResult, TaskStatus


@contextmanager
def _temp_runtime_workdir():
    base = Path(".claude") / "perf_tmp" / f"backend_{uuid.uuid4().hex}"
    base.mkdir(parents=True, exist_ok=True)
    try:
        yield base
    finally:
        shutil.rmtree(base, ignore_errors=True)


@pytest.mark.asyncio
async def test_queue_contract_enqueue_dequeue_fifo():
    queue = InMemoryTaskQueue()

    await queue.enqueue(QueueItem(task_id="task-1"))
    await queue.enqueue(QueueItem(task_id="task-2"))

    first = await queue.dequeue(timeout=0.1)
    second = await queue.dequeue(timeout=0.1)

    assert first is not None and first.task_id == "task-1"
    assert second is not None and second.task_id == "task-2"
    assert queue.qsize() == 0


@pytest.mark.asyncio
async def test_queue_contract_timeout_returns_none():
    queue = InMemoryTaskQueue()
    item = await queue.dequeue(timeout=0.01)
    assert item is None


@pytest.mark.asyncio
async def test_queue_contract_zero_timeout_is_non_blocking():
    queue = InMemoryTaskQueue()
    assert await queue.dequeue(timeout=0) is None

    await queue.enqueue(QueueItem(task_id="task-0"))
    item = await queue.dequeue(timeout=0)
    assert item is not None
    assert item.task_id == "task-0"


def test_runtime_repository_contract_upsert_get_delete():
    with _temp_runtime_workdir() as workdir:
        repo = create_file_runtime_task_repository(workdir)

        task = BashTask(
            id="task-123",
            command="echo contract",
            status=TaskStatus.COMPLETED,
        )
        task.result = TaskResult(code=0, stdout="ok", stderr="")

        repo.upsert_task(task)
        record = repo.get_task_record(task.id)
        assert record is not None
        assert record["id"] == "task-123"
        assert record["status"] == "completed"
        assert record["result"]["stdout"] == "ok"

        repo.delete_task(task.id)
        assert repo.get_task_record(task.id) is None
