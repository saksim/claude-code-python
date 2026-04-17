"""Task file storage utilities.

Provides cross-process locking, schema compatibility, and atomic writes
for `.claude/tasks.json`.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Callable, IO


TASKS_SCHEMA_VERSION = 2
_LOCK_SUFFIX = ".lock"
_DEFAULT_LOCK_TIMEOUT_SECONDS = 5.0
_DEFAULT_LOCK_POLL_SECONDS = 0.05


class TaskFileLockTimeoutError(TimeoutError):
    """Raised when task file lock acquisition times out."""


class TaskFileLock:
    """Cross-platform file lock for task file operations."""

    def __init__(
        self,
        target_file: Path | str,
        timeout_seconds: float = _DEFAULT_LOCK_TIMEOUT_SECONDS,
        poll_seconds: float = _DEFAULT_LOCK_POLL_SECONDS,
    ) -> None:
        self._target_file = Path(target_file)
        self._lock_file = self._target_file.with_name(self._target_file.name + _LOCK_SUFFIX)
        self._timeout_seconds = timeout_seconds
        self._poll_seconds = poll_seconds
        self._handle: IO[bytes] | None = None

    def acquire(self) -> None:
        """Acquire the lock or raise TaskFileLockTimeoutError."""
        start = time.monotonic()
        self._lock_file.parent.mkdir(parents=True, exist_ok=True)
        self._handle = open(self._lock_file, "a+b")
        self._handle.seek(0)

        while True:
            try:
                self._acquire_non_blocking()
                return
            except OSError:
                if (time.monotonic() - start) >= self._timeout_seconds:
                    self.release()
                    raise TaskFileLockTimeoutError(
                        f"Timed out waiting for lock: {self._lock_file}"
                    )
                time.sleep(self._poll_seconds)

    def release(self) -> None:
        """Release the lock."""
        try:
            self._release_lock()
        finally:
            if self._handle is not None:
                self._handle.close()
                self._handle = None

    def _acquire_non_blocking(self) -> None:
        """Acquire the lock without blocking."""
        if self._handle is None:
            raise RuntimeError("Lock handle not initialized")
        if os.name == "nt":
            import msvcrt

            self._handle.seek(0)
            msvcrt.locking(self._handle.fileno(), msvcrt.LK_NBLCK, 1)
            return

        import fcntl

        fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _release_lock(self) -> None:
        """Release lock held on the lock file."""
        if self._handle is None:
            return
        if os.name == "nt":
            import msvcrt

            self._handle.seek(0)
            msvcrt.locking(self._handle.fileno(), msvcrt.LK_UNLCK, 1)
            return

        import fcntl

        fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)

    def __enter__(self) -> "TaskFileLock":
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()


def _atomic_write_json(path: Path, data: Any) -> None:
    """Write JSON atomically using temp file + replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    payload = json.dumps(data, indent=2, ensure_ascii=False)
    temp_path.write_text(payload, encoding="utf-8")
    try:
        temp_path.replace(path)
    except PermissionError:
        # Restricted filesystems may disallow rename/unlink operations.
        path.write_text(payload, encoding="utf-8")


def _normalize_task(raw: Any, fallback_id: str | None = None) -> dict[str, Any] | None:
    """Normalize a task record into the canonical list schema."""
    if not isinstance(raw, dict):
        return None

    task = dict(raw)
    task_id = str(task.get("id") or fallback_id or uuid.uuid4().hex[:8])
    description = task.get("description", "")
    if not isinstance(description, str):
        description = str(description)

    title = task.get("title")
    if not isinstance(title, str) or not title.strip():
        title = description or f"Task {task_id}"

    status = task.get("status", "pending")
    if not isinstance(status, str) or not status.strip():
        status = "pending"

    task["id"] = task_id
    task["title"] = title
    task["description"] = description
    task["status"] = status
    return task


def load_tasks(task_file: Path | str) -> list[dict[str, Any]]:
    """Load tasks from disk, supporting legacy schemas."""
    path = Path(task_file)
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    if isinstance(payload, dict) and isinstance(payload.get("tasks"), list):
        raw_tasks = payload["tasks"]
    elif isinstance(payload, list):
        raw_tasks = payload
    elif isinstance(payload, dict):
        # Legacy schema: {"<id>": {...}}
        raw_tasks = []
        for raw_id, raw_task in payload.items():
            normalized = _normalize_task(raw_task, fallback_id=str(raw_id))
            if normalized is not None:
                raw_tasks.append(normalized)
    else:
        return []

    tasks: list[dict[str, Any]] = []
    for raw_task in raw_tasks:
        normalized = _normalize_task(raw_task)
        if normalized is not None:
            tasks.append(normalized)
    return tasks


def save_tasks(task_file: Path | str, tasks: list[dict[str, Any]]) -> None:
    """Persist tasks using canonical schema and atomic writes."""
    path = Path(task_file)
    normalized_tasks: list[dict[str, Any]] = []
    for raw_task in tasks:
        normalized = _normalize_task(raw_task)
        if normalized is not None:
            normalized_tasks.append(normalized)

    payload = {
        "schema_version": TASKS_SCHEMA_VERSION,
        "tasks": normalized_tasks,
    }
    _atomic_write_json(path, payload)


def mutate_tasks(
    task_file: Path | str,
    mutator: Callable[[list[dict[str, Any]]], list[dict[str, Any]] | None],
) -> list[dict[str, Any]]:
    """Mutate tasks under a file lock and persist atomically."""
    path = Path(task_file)
    with TaskFileLock(path):
        tasks = load_tasks(path)
        updated = mutator(tasks)
        if updated is not None:
            tasks = updated
        save_tasks(path, tasks)
        return tasks


__all__ = [
    "TASKS_SCHEMA_VERSION",
    "TaskFileLock",
    "TaskFileLockTimeoutError",
    "load_tasks",
    "save_tasks",
    "mutate_tasks",
]
