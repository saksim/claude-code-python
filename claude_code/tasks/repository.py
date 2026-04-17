"""Task repository abstractions for workflow and runtime task persistence."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from claude_code.tasks.types import AgentTask, BashTask, Task
from claude_code.utils.task_store import TaskFileLock, load_tasks, save_tasks

RUNTIME_TASKS_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class TaskRepositoryConfig:
    """Configuration for task repository."""

    task_file: Path


class TaskRepository:
    """File-backed task repository with schema compatibility."""

    def __init__(self, config: TaskRepositoryConfig) -> None:
        self._task_file = config.task_file

    @property
    def task_file(self) -> Path:
        return self._task_file

    def list_tasks(self) -> list[dict[str, Any]]:
        return load_tasks(self._task_file)

    def get_task(self, task_id: str) -> dict[str, Any] | None:
        for task in self.list_tasks():
            if task.get("id") == task_id:
                return task
        return None

    def create_task(
        self,
        title: str,
        description: str = "",
        status: str = "pending",
        task_id: str | None = None,
        **extra_fields: Any,
    ) -> dict[str, Any]:
        new_task_id = task_id or str(uuid4())[:8]
        task: dict[str, Any] = {
            "id": new_task_id,
            "title": title,
            "description": description,
            "status": status,
            **extra_fields,
        }

        with TaskFileLock(self._task_file):
            tasks = load_tasks(self._task_file)
            tasks.append(task)
            save_tasks(self._task_file, tasks)

        return task

    def update_task(self, task_id: str, **updates: Any) -> dict[str, Any] | None:
        with TaskFileLock(self._task_file):
            tasks = load_tasks(self._task_file)
            for task in tasks:
                if task.get("id") == task_id:
                    task.update(updates)
                    save_tasks(self._task_file, tasks)
                    return task
        return None

    def delete_task(self, task_id: str) -> bool:
        with TaskFileLock(self._task_file):
            tasks = load_tasks(self._task_file)
            filtered = [task for task in tasks if task.get("id") != task_id]
            if len(filtered) == len(tasks):
                return False
            save_tasks(self._task_file, filtered)
            return True


@dataclass(frozen=True, slots=True)
class RuntimeTaskRepositoryConfig:
    """Configuration for runtime task repository."""

    runtime_file: Path


class RuntimeTaskRepository(ABC):
    """Abstraction for runtime task state persistence."""

    @abstractmethod
    def upsert_task(self, task: Task) -> None:
        """Insert or update runtime task record."""

    @abstractmethod
    def delete_task(self, task_id: str) -> None:
        """Delete runtime task record."""

    @abstractmethod
    def get_task_record(self, task_id: str) -> dict[str, Any] | None:
        """Get runtime task record by id."""

    @abstractmethod
    def list_task_records(self) -> list[dict[str, Any]]:
        """List all runtime task records."""


class FileRuntimeTaskRepository(RuntimeTaskRepository):
    """File-backed runtime task repository."""

    def __init__(self, config: RuntimeTaskRepositoryConfig) -> None:
        self._runtime_file = config.runtime_file
        self._runtime_file.parent.mkdir(parents=True, exist_ok=True)

    def upsert_task(self, task: Task) -> None:
        with TaskFileLock(self._runtime_file):
            payload = self._load_payload()
            payload["tasks"][task.id] = self._task_to_record(task)
            self._write_payload(payload)

    def delete_task(self, task_id: str) -> None:
        with TaskFileLock(self._runtime_file):
            payload = self._load_payload()
            payload["tasks"].pop(task_id, None)
            self._write_payload(payload)

    def get_task_record(self, task_id: str) -> dict[str, Any] | None:
        payload = self._load_payload()
        record = payload["tasks"].get(task_id)
        if not isinstance(record, dict):
            return None
        return record

    def list_task_records(self) -> list[dict[str, Any]]:
        payload = self._load_payload()
        records = [r for r in payload["tasks"].values() if isinstance(r, dict)]
        records.sort(key=lambda r: str(r.get("created_at", "")))
        return records

    def _load_payload(self) -> dict[str, Any]:
        if not self._runtime_file.exists():
            return {"schema_version": RUNTIME_TASKS_SCHEMA_VERSION, "tasks": {}}

        try:
            loaded = json.loads(self._runtime_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"schema_version": RUNTIME_TASKS_SCHEMA_VERSION, "tasks": {}}

        tasks = loaded.get("tasks") if isinstance(loaded, dict) else None
        if not isinstance(tasks, dict):
            tasks = {}

        return {
            "schema_version": loaded.get("schema_version", RUNTIME_TASKS_SCHEMA_VERSION)
            if isinstance(loaded, dict)
            else RUNTIME_TASKS_SCHEMA_VERSION,
            "tasks": tasks,
        }

    def _write_payload(self, payload: dict[str, Any]) -> None:
        self._runtime_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _task_to_record(self, task: Task) -> dict[str, Any]:
        result_payload = None
        if task.result is not None:
            result_payload = {
                "code": task.result.code,
                "stdout": task.result.stdout,
                "stderr": task.result.stderr,
                "error": task.result.error,
            }

        record: dict[str, Any] = {
            "id": task.id,
            "type": task.type.value,
            "status": task.status.value,
            "description": task.description,
            "created_at": _dt_to_iso(task.created_at),
            "started_at": _dt_to_iso(task.started_at),
            "completed_at": _dt_to_iso(task.completed_at),
            "error": task.error,
            "is_backgrounded": task.is_backgrounded,
            "parent_id": task.parent_id,
            "tags": list(task.tags),
            "metadata": dict(task.metadata),
            "result": result_payload,
        }

        if isinstance(task, BashTask):
            record["command"] = task.command
            record["cwd"] = task.cwd
            record["timeout"] = task.timeout
        elif isinstance(task, AgentTask):
            record["prompt"] = task.prompt
            record["model"] = task.model

        return record


def _dt_to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def create_file_task_repository(working_directory: str | Path) -> TaskRepository:
    """Create default file-backed repository for a working directory."""
    workdir = Path(working_directory)
    task_file = workdir / ".claude" / "tasks.json"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    return TaskRepository(TaskRepositoryConfig(task_file=task_file))


def create_file_runtime_task_repository(
    working_directory: str | Path,
) -> FileRuntimeTaskRepository:
    """Create default file-backed runtime task repository."""
    workdir = Path(working_directory)
    runtime_file = workdir / ".claude" / "runtime_tasks.json"
    runtime_file.parent.mkdir(parents=True, exist_ok=True)
    return FileRuntimeTaskRepository(
        RuntimeTaskRepositoryConfig(runtime_file=runtime_file)
    )


__all__ = [
    "TaskRepositoryConfig",
    "TaskRepository",
    "RuntimeTaskRepositoryConfig",
    "RuntimeTaskRepository",
    "FileRuntimeTaskRepository",
    "RUNTIME_TASKS_SCHEMA_VERSION",
    "create_file_task_repository",
    "create_file_runtime_task_repository",
]
