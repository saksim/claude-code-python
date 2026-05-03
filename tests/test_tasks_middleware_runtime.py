"""Runtime tests for task middleware reliability fixes."""

from __future__ import annotations

import io
import json
import shutil
import uuid
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest
from rich.console import Console

from claude_code.commands.base import CommandContext
from claude_code.commands.tasks import TasksCommand
from claude_code.tasks.manager import TaskManager
from claude_code.tasks.types import TaskResult, TaskStatus
from claude_code.tools.base import ToolContext
from claude_code.tools.control import TaskControlListTool, TaskOutputTool, TaskStopTool
from claude_code.tools.cron import CronDeleteTool, CronListTool, ScheduleCronTool
from claude_code.tools.cron.create import CronCreateTool, _SESSION_ONLY_TASKS
from claude_code.tools.workflow import TaskListTool, TaskUpdateTool
from claude_code.utils.task_store import load_tasks, mutate_tasks


@contextmanager
def _temp_workdir():
    base = Path(".claude") / "perf_tmp" / f"middleware_{uuid.uuid4().hex}"
    base.mkdir(parents=True, exist_ok=True)
    try:
        yield base
    finally:
        shutil.rmtree(base, ignore_errors=True)


def _tool_context(workdir: Path) -> ToolContext:
    return ToolContext(working_directory=str(workdir), environment={})


@pytest.mark.asyncio
async def test_task_control_toolchain_uses_singleton_manager():
    with _temp_workdir() as workdir:
        TaskManager._instance = None
        manager = TaskManager.get_instance()

        agent_task = await manager.create_agent_task(prompt="agent task", background=True)
        bash_task = await manager.create_bash_task(command="echo hello", background=True)
        bash_task.status = TaskStatus.COMPLETED
        bash_task.result = TaskResult(code=0, stdout="hello", stderr="")
        bash_task.set_completed()

        context = _tool_context(workdir)

        list_result = await TaskControlListTool().execute({}, context)
        assert not list_result.is_error
        assert agent_task.id in list_result.content
        assert bash_task.id in list_result.content

        output_result = await TaskOutputTool().execute({"task_id": bash_task.id}, context)
        assert not output_result.is_error
        assert "hello" in output_result.content

        missing_stop = await TaskStopTool().execute({"task_id": "missing-task"}, context)
        assert missing_stop.is_error


@pytest.mark.asyncio
async def test_workflow_tools_migrate_legacy_dict_schema():
    with _temp_workdir() as workdir:
        task_file = workdir / ".claude" / "tasks.json"
        task_file.parent.mkdir(parents=True, exist_ok=True)
        task_file.write_text(
            json.dumps({"legacy001": {"description": "legacy", "status": "pending"}}),
            encoding="utf-8",
        )

        context = _tool_context(workdir)

        list_result = await TaskListTool().execute({}, context)
        assert not list_result.is_error
        assert "legacy001" in list_result.content

        update_result = await TaskUpdateTool().execute(
            {"task_id": "legacy001", "status": "completed"},
            context,
        )
        assert not update_result.is_error

        payload = json.loads(task_file.read_text(encoding="utf-8"))
        assert payload["schema_version"] == 2
        assert isinstance(payload["tasks"], list)
        assert payload["tasks"][0]["id"] == "legacy001"
        assert payload["tasks"][0]["status"] == "completed"


def test_task_store_file_lock_prevents_lost_updates():
    with _temp_workdir() as workdir:
        task_file = workdir / ".claude" / "tasks.json"

        def _append_task(idx: int) -> None:
            task_id = f"t{idx:03d}"

            def _mutator(tasks: list[dict]) -> list[dict]:
                tasks.append(
                    {
                        "id": task_id,
                        "title": f"Task {idx}",
                        "description": str(idx),
                        "status": "pending",
                    }
                )
                return tasks

            mutate_tasks(task_file, _mutator)

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(_append_task, range(40)))

        tasks = load_tasks(task_file)
        assert len(tasks) == 40
        assert len({t["id"] for t in tasks}) == 40


@pytest.mark.asyncio
async def test_cron_create_honors_durable_flag():
    with _temp_workdir() as workdir:
        _SESSION_ONLY_TASKS.clear()
        tool = CronCreateTool()
        context = _tool_context(workdir)
        schedule_file = workdir / ".claude" / "scheduled_tasks.json"

        result_session = await tool.execute(
            {"cron": "*/5 * * * *", "prompt": "session-only", "durable": False},
            context,
        )
        assert not result_session.is_error
        assert not schedule_file.exists()
        assert len(_SESSION_ONLY_TASKS) == 1

        result_durable = await tool.execute(
            {"cron": "*/10 * * * *", "prompt": "durable", "durable": True},
            context,
        )
        assert not result_durable.is_error
        assert schedule_file.exists()
        persisted = json.loads(schedule_file.read_text(encoding="utf-8"))
        assert len(persisted) == 1


@pytest.mark.asyncio
async def test_schedule_tools_share_scheduled_tasks_storage():
    with _temp_workdir() as workdir:
        _SESSION_ONLY_TASKS.clear()
        context = _tool_context(workdir)
        schedule_file = workdir / ".claude" / "scheduled_tasks.json"

        create_result = await ScheduleCronTool().execute(
            {"command": "echo hi", "schedule": "0 * * * *", "name": "hourly"},
            context,
        )
        assert not create_result.is_error
        assert schedule_file.exists()

        list_result = await CronListTool().execute({}, context)
        assert not list_result.is_error
        assert "hourly" in str(list_result.content)
        assert "Durable: True" in str(list_result.content)

        delete_result = await CronDeleteTool().execute({"name": "hourly"}, context)
        assert not delete_result.is_error

        payload = json.loads(schedule_file.read_text(encoding="utf-8"))
        assert "hourly" not in payload


@pytest.mark.asyncio
async def test_tasks_command_uses_unified_task_schema():
    with _temp_workdir() as workdir:
        command = TasksCommand()
        context = CommandContext(
            working_directory=str(workdir),
            console=Console(file=io.StringIO(), force_terminal=False, width=120),
        )

        create_result = await command.execute("create unify schema", context)
        assert create_result.success
        created_id = str(create_result.content).split(": ")[-1]

        list_result = await command.execute("list", context)
        assert list_result.success
        assert created_id in str(list_result.content)

        complete_result = await command.execute(f"complete {created_id}", context)
        assert complete_result.success

        remove_result = await command.execute(f"remove {created_id}", context)
        assert remove_result.success
