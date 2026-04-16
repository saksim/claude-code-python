"""Task repository abstraction for workflow task persistence."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from claude_code.utils.task_store import TaskFileLock, load_tasks, save_tasks


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


def create_file_task_repository(working_directory: str | Path) -> TaskRepository:
    """Create default file-backed repository for a working directory."""
    workdir = Path(working_directory)
    task_file = workdir / ".claude" / "tasks.json"
    task_file.parent.mkdir(parents=True, exist_ok=True)
    return TaskRepository(TaskRepositoryConfig(task_file=task_file))


__all__ = [
    "TaskRepositoryConfig",
    "TaskRepository",
    "create_file_task_repository",
]
