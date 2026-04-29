"""
Task manager for Claude Code Python.

Manages task execution and tracking.
"""

import asyncio
import uuid
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime

from claude_code.services.event_journal import EventJournal
from claude_code.tasks.types import (
    Task,
    TaskType,
    TaskStatus,
    TaskResult,
    BashTask,
    AgentTask,
    create_task_from_dict,
    is_background_task,
)
from claude_code.tasks.queue import InMemoryTaskQueue, QueueItem, TaskQueue
from claude_code.tasks.repository import RuntimeTaskRepository


@dataclass
class TaskEvent:
    """Event from task execution."""
    task_id: str
    event_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict = field(default_factory=dict)


class TaskStateTransitionError(ValueError):
    """Raised when task status transition violates the task state machine."""


@dataclass(frozen=True, slots=True)
class TaskRetryPolicy:
    """Retry policy for task execution."""

    max_retries: int = 0
    retry_delay: float = 0.0


class TaskManager:
    """
    Manages task execution and tracking.
    
    Handles creating, running, and monitoring tasks.
    Supports singleton pattern via get_instance().
    """
    
    _instance: Optional['TaskManager'] = None
    
    _ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
        TaskStatus.PENDING: frozenset({TaskStatus.RUNNING, TaskStatus.CANCELLED}),
        TaskStatus.RUNNING: frozenset(
            {
                TaskStatus.PENDING,
                TaskStatus.COMPLETED,
                TaskStatus.FAILED,
                TaskStatus.CANCELLED,
                TaskStatus.TIMEOUT,
            }
        ),
        TaskStatus.COMPLETED: frozenset(),
        TaskStatus.FAILED: frozenset(),
        TaskStatus.CANCELLED: frozenset(),
        TaskStatus.TIMEOUT: frozenset(),
    }

    def __init__(
        self,
        task_queue: Optional[TaskQueue] = None,
        runtime_repository: Optional[RuntimeTaskRepository] = None,
        max_concurrency: Optional[int] = None,
        event_journal: Optional[EventJournal] = None,
    ):
        if max_concurrency is not None and max_concurrency <= 0:
            raise ValueError("max_concurrency must be > 0 when provided")

        self._tasks: dict[str, Task] = {}
        self._background_tasks: set[str] = set()
        self._task_handlers: dict[str, Callable] = {}
        self._event_handlers: list[Callable[[TaskEvent], None]] = []
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._pending_executors: dict[str, Callable] = {}
        self._idempotency_index: dict[str, str] = {}
        self._retry_policies: dict[str, TaskRetryPolicy] = {}
        self._attempt_counts: dict[str, int] = {}
        self._task_queue: TaskQueue = task_queue or InMemoryTaskQueue()
        self._runtime_repository = runtime_repository
        self._event_journal = event_journal
        self._max_concurrency = max_concurrency
        self._queue_lag_samples: list[float] = []
        self._execution_samples: list[float] = []
        self._sample_window = 512
        self._lock = asyncio.Lock()
        self._stats: dict[str, int] = {
            "created": 0,
            "queued": 0,
            "started": 0,
            "completed": 0,
            "failed": 0,
            "cancelled": 0,
            "timed_out": 0,
            "retried": 0,
            "recovered": 0,
        }
        self._recover_from_runtime_repository()
    
    @classmethod
    def get_instance(cls) -> 'TaskManager':
        """Get the global task manager instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    async def create_bash_task(
        self,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
        background: bool = True,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> BashTask:
        """Create a bash command task."""
        if idempotency_key:
            existing = self._get_task_for_idempotency(idempotency_key)
            if existing is not None:
                if not isinstance(existing, BashTask):
                    raise ValueError(
                        f"idempotency key already used by task type {existing.type.value}: {idempotency_key}"
                    )
                return existing

        task_id = str(uuid.uuid4())
        
        task = BashTask(
            id=task_id,
            command=command,
            cwd=cwd,
            env=env,
            timeout=timeout,
            is_backgrounded=background,
        )

        if description:
            task.description = description
        if idempotency_key:
            task.metadata["idempotency_key"] = idempotency_key
            self._idempotency_index[idempotency_key] = task.id
        
        self._tasks[task_id] = task
        self._persist_task(task)
        self._stats["created"] += 1
        
        return task
    
    async def create_agent_task(
        self,
        prompt: str,
        model: Optional[str] = None,
        tools: Optional[list] = None,
        background: bool = True,
        idempotency_key: Optional[str] = None,
    ) -> AgentTask:
        """Create an agent task."""
        if idempotency_key:
            existing = self._get_task_for_idempotency(idempotency_key)
            if existing is not None:
                if not isinstance(existing, AgentTask):
                    raise ValueError(
                        f"idempotency key already used by task type {existing.type.value}: {idempotency_key}"
                    )
                return existing

        task_id = str(uuid.uuid4())
        
        task = AgentTask(
            id=task_id,
            prompt=prompt,
            model=model,
            tools=tools,
            is_backgrounded=background,
        )
        if idempotency_key:
            task.metadata["idempotency_key"] = idempotency_key
            self._idempotency_index[idempotency_key] = task.id
        
        self._tasks[task_id] = task
        self._persist_task(task)
        self._stats["created"] += 1
        
        return task
    
    async def start_task(
        self,
        task_id: str,
        executor: Optional[Callable] = None,
        max_retries: int = 0,
        retry_delay: float = 0.0,
    ) -> None:
        """Start a task."""
        if executor is None:
            raise ValueError(f"executor is required to start task: {task_id}")
        if max_retries < 0:
            raise ValueError("max_retries must be >= 0")
        if retry_delay < 0:
            raise ValueError("retry_delay must be >= 0")

        async with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise ValueError(f"Task not found: {task_id}")
            if task.status != TaskStatus.PENDING:
                raise TaskStateTransitionError(
                    f"Task must be pending before start: {task.id} ({task.status.value})"
                )

        self._pending_executors[task_id] = executor
        self._retry_policies[task_id] = TaskRetryPolicy(
            max_retries=max_retries,
            retry_delay=retry_delay,
        )
        await self._task_queue.enqueue(QueueItem(task_id=task_id))
        self._stats["queued"] += 1
        await self._dispatch_available()

    async def _dispatch_available(self) -> None:
        """Dispatch queued tasks while worker capacity is available."""
        while self._can_dispatch_more():
            queued_item = await self._task_queue.dequeue(timeout=0)
            if queued_item is None:
                return

            self._record_queue_lag(queued_item)
            dispatched_task_id = queued_item.task_id
            executor = self._pending_executors.pop(dispatched_task_id, None)
            if executor is None:
                continue

            async with self._lock:
                task = self._tasks.get(dispatched_task_id)
                if task is None or task.status != TaskStatus.PENDING:
                    continue

                self._transition_status(task, TaskStatus.RUNNING)
                task.started_at = datetime.now()
                task.completed_at = None
                self._persist_task(task)
                self._stats["started"] += 1
                attempt = self._attempt_counts.get(dispatched_task_id, 0) + 1
                self._attempt_counts[dispatched_task_id] = attempt

            self._emit_event(
                TaskEvent(
                    task_id=dispatched_task_id,
                    event_type="started",
                    data={"attempt": attempt},
                )
            )

            async_task = asyncio.create_task(self._run_task(dispatched_task_id, executor))
            self._running_tasks[dispatched_task_id] = async_task

    async def _run_task(
        self,
        task_id: str,
        executor: Callable,
    ) -> None:
        """Run a task with an executor."""
        task = self._tasks.get(task_id)
        if not task:
            return
        
        try:
            result = await executor(task)
            
            async with self._lock:
                self._transition_status(task, TaskStatus.COMPLETED)
                task.result = result
                task.error = None
                task.completed_at = datetime.now()
                task.set_completed()
                self._persist_task(task)
                self._stats["completed"] += 1

            self._record_execution_duration(task)
            self._cleanup_retry_state(task_id)
            
            self._emit_event(TaskEvent(
                task_id=task_id,
                event_type="completed",
                data={"result": result},
            ))
            
        except asyncio.TimeoutError:
            timeout_error = "Task execution timed out"
            retried = await self._requeue_on_failure(
                task=task,
                executor=executor,
                reason=timeout_error,
                failure_kind="timeout",
            )
            if retried:
                return

            async with self._lock:
                self._transition_status(task, TaskStatus.TIMEOUT)
                task.error = timeout_error
                task.completed_at = datetime.now()
                task.set_completed()
                self._persist_task(task)
                self._stats["timed_out"] += 1

            self._record_execution_duration(task)
            self._cleanup_retry_state(task_id)
            
            self._emit_event(TaskEvent(
                task_id=task_id,
                event_type="timeout",
            ))
            
        except Exception as e:
            retried = await self._requeue_on_failure(
                task=task,
                executor=executor,
                reason=str(e),
                failure_kind="error",
            )
            if retried:
                return

            async with self._lock:
                self._transition_status(task, TaskStatus.FAILED)
                task.error = str(e)
                task.completed_at = datetime.now()
                task.set_completed()
                self._persist_task(task)
                self._stats["failed"] += 1

            self._record_execution_duration(task)
            self._cleanup_retry_state(task_id)
            
            self._emit_event(TaskEvent(
                task_id=task_id,
                event_type="failed",
                data={"error": str(e)},
            ))
            
        finally:
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
            self._schedule_dispatch()
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        running_async_task: Optional[asyncio.Task] = None

        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            if not self._can_transition(task.status, TaskStatus.CANCELLED):
                return False

            running_async_task = self._running_tasks.get(task_id)
            if running_async_task is not None:
                running_async_task.cancel()
            self._pending_executors.pop(task_id, None)

        if running_async_task is not None:
            try:
                await running_async_task
            except asyncio.CancelledError:
                pass

        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False

            if not self._can_transition(task.status, TaskStatus.CANCELLED):
                return False

            self._transition_status(task, TaskStatus.CANCELLED)
            task.completed_at = datetime.now()
            task.set_completed()
            self._persist_task(task)
            self._stats["cancelled"] += 1
            self._cleanup_retry_state(task_id)
        
        self._emit_event(TaskEvent(
            task_id=task_id,
            event_type="cancelled",
        ))
        
        return True
    
    async def stop_task(self, task_id: str) -> bool:
        """Stop a task forcefully."""
        return await self.cancel_task(task_id)
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> list[Task]:
        """Get all tasks."""
        return list(self._tasks.values())
    
    def get_background_tasks(self) -> list[Task]:
        """Get all background tasks."""
        return [
            task for task in self._tasks.values()
            if is_background_task(task)
        ]
    
    def get_running_tasks(self) -> list[Task]:
        """Get all currently running tasks."""
        return [
            task for task in self._tasks.values()
            if task.status == TaskStatus.RUNNING
        ]
    
    def get_completed_tasks(self) -> list[Task]:
        """Get all completed tasks."""
        return [
            task for task in self._tasks.values()
            if task.is_completed
        ]
    
    def register_handler(self, handler: Callable[[TaskEvent], None]) -> None:
        """Register an event handler."""
        self._event_handlers.append(handler)
    
    def _emit_event(self, event: TaskEvent) -> None:
        """Emit a task event."""
        self._record_journal_event(event)
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception:
                pass

    def _record_journal_event(self, event: TaskEvent) -> None:
        """Persist normalized task lifecycle event into runtime event journal."""
        if self._event_journal is None:
            return

        task = self._tasks.get(event.task_id)
        task_type: str | None = None
        task_status: str | None = None
        task_metadata: dict[str, Any] = {}
        if task is not None:
            task_type = task.type.value if hasattr(task.type, "value") else str(task.type)
            task_status = task.status.value if hasattr(task.status, "value") else str(task.status)
            task_metadata = dict(task.metadata)

        session_id = task_metadata.get("session_id")
        conversation_id = task_metadata.get("conversation_id")
        self._event_journal.append_event(
            event_type=f"task.{event.event_type}",
            payload={
                "task_id": event.task_id,
                "task_type": task_type,
                "task_status": task_status,
                "event_data": dict(event.data),
            },
            session_id=session_id if isinstance(session_id, str) else None,
            conversation_id=conversation_id if isinstance(conversation_id, str) else None,
            source="task_manager",
            metadata={
                "task_event_type": event.event_type,
            },
            timestamp=event.timestamp.timestamp(),
        )
    
    async def wait_for_task(
        self,
        task_id: str,
        timeout: Optional[float] = None,
    ) -> Task:
        """Wait for a task to complete."""
        task = self._tasks.get(task_id)
        if not task:
            raise ValueError(f"Task not found: {task_id}")
        
        if task.is_completed:
            return task
        
        if task_id in self._running_tasks:
            async_task = self._running_tasks[task_id]
            try:
                await asyncio.wait_for(async_task, timeout=timeout)
            except asyncio.TimeoutError:
                pass
        
        return self._tasks.get(task_id, task)
    
    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        task_type: Optional[TaskType] = None,
    ) -> list[Task]:
        """List tasks with optional filtering."""
        tasks = self._tasks.values()
        
        if status:
            tasks = [t for t in tasks if t.status == status]
        
        if task_type:
            tasks = [t for t in tasks if t.type == task_type]
        
        return list(tasks)
    
    def clear_completed(self) -> int:
        """Clear all completed tasks."""
        completed = [
            task_id for task_id, task in self._tasks.items()
            if task.is_completed
        ]
        
        for task_id in completed:
            self._delete_persisted_task(task_id)
            self._cleanup_retry_state(task_id)
            del self._tasks[task_id]
        self._cleanup_idempotency_index()
        
        return len(completed)

    def get_stats(self) -> dict[str, int | float]:
        """Get task manager statistics."""
        terminal_total = (
            self._stats["completed"]
            + self._stats["failed"]
            + self._stats["cancelled"]
            + self._stats["timed_out"]
        )
        started_total = self._stats["started"]
        queue_size = self._task_queue.qsize()
        pending = len(self._pending_executors)

        return {
            **self._stats,
            "total_tasks": len(self._tasks),
            "running_tasks": len(self._running_tasks),
            "queue_size": queue_size,
            "pending_executors": pending,
            "queue_backlog": queue_size + pending,
            "idempotency_keys": len(self._idempotency_index),
            "queue_lag_avg_ms": self._sample_average_ms(self._queue_lag_samples),
            "queue_lag_p95_ms": self._sample_percentile_ms(self._queue_lag_samples, 0.95),
            "task_exec_avg_ms": self._sample_average_ms(self._execution_samples),
            "task_exec_p95_ms": self._sample_percentile_ms(self._execution_samples, 0.95),
            "failure_rate": self._safe_rate(self._stats["failed"], terminal_total),
            "timeout_rate": self._safe_rate(self._stats["timed_out"], terminal_total),
            "retry_rate": self._safe_rate(self._stats["retried"], started_total),
        }

    def _can_transition(self, current: TaskStatus, target: TaskStatus) -> bool:
        """Check if transition is valid in state machine."""
        return target in self._ALLOWED_TRANSITIONS.get(current, frozenset())

    def _transition_status(self, task: Task, new_status: TaskStatus) -> None:
        """Transition task to new status with validation."""
        if task.status == new_status:
            return
        if not self._can_transition(task.status, new_status):
            raise TaskStateTransitionError(
                f"Invalid task status transition: {task.status.value} -> {new_status.value} "
                f"(task_id={task.id})"
            )
        task.status = new_status

    def _persist_task(self, task: Task) -> None:
        """Persist runtime task snapshot when repository is configured."""
        if self._runtime_repository is None:
            return
        try:
            self._runtime_repository.upsert_task(task)
        except Exception:
            # Runtime persistence should not break task execution path.
            pass

    def _delete_persisted_task(self, task_id: str) -> None:
        """Delete persisted runtime task snapshot."""
        if self._runtime_repository is None:
            return
        try:
            self._runtime_repository.delete_task(task_id)
        except Exception:
            pass

    def _get_task_for_idempotency(self, idempotency_key: str) -> Optional[Task]:
        """Return previously created task by idempotency key."""
        existing_task_id = self._idempotency_index.get(idempotency_key)
        if not existing_task_id:
            return None
        return self._tasks.get(existing_task_id)

    def _cleanup_idempotency_index(self) -> None:
        """Remove stale idempotency key mappings."""
        valid_task_ids = set(self._tasks.keys())
        stale_keys = [
            key for key, task_id in self._idempotency_index.items()
            if task_id not in valid_task_ids
        ]
        for key in stale_keys:
            del self._idempotency_index[key]

    def _cleanup_retry_state(self, task_id: str) -> None:
        """Remove retry bookkeeping for a task."""
        self._retry_policies.pop(task_id, None)
        self._attempt_counts.pop(task_id, None)

    async def _requeue_on_failure(
        self,
        task: Task,
        executor: Callable,
        reason: str,
        failure_kind: str,
    ) -> bool:
        """Requeue task when retry policy allows; returns True when requeued."""
        task_id = task.id
        policy = self._retry_policies.get(task_id)
        if policy is None:
            return False

        attempts = self._attempt_counts.get(task_id, 0)
        max_attempts = policy.max_retries + 1
        if attempts >= max_attempts:
            return False

        async with self._lock:
            if task.status != TaskStatus.RUNNING:
                return False
            self._transition_status(task, TaskStatus.PENDING)
            task.error = reason
            task.started_at = None
            task.completed_at = None
            self._persist_task(task)
            self._stats["retried"] += 1
            self._pending_executors[task_id] = executor

        self._emit_event(
            TaskEvent(
                task_id=task_id,
                event_type="retrying",
                data={
                    "reason": reason,
                    "kind": failure_kind,
                    "attempt": attempts,
                    "max_attempts": max_attempts,
                },
            )
        )
        if policy.retry_delay > 0:
            await asyncio.sleep(policy.retry_delay)

        await self._task_queue.enqueue(QueueItem(task_id=task_id))
        self._stats["queued"] += 1
        return True

    def _can_dispatch_more(self) -> bool:
        if self._max_concurrency is None:
            return True
        return len(self._running_tasks) < self._max_concurrency

    def _schedule_dispatch(self) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        loop.create_task(self._dispatch_available())

    def _record_queue_lag(self, item: QueueItem) -> None:
        lag_seconds = max((datetime.now() - item.enqueued_at).total_seconds(), 0.0)
        self._add_sample(self._queue_lag_samples, lag_seconds)

    def _record_execution_duration(self, task: Task) -> None:
        if task.duration is None:
            return
        self._add_sample(self._execution_samples, max(task.duration, 0.0))

    def _add_sample(self, samples: list[float], value: float) -> None:
        samples.append(value)
        if len(samples) > self._sample_window:
            del samples[0]

    @staticmethod
    def _safe_rate(numerator: int, denominator: int) -> float:
        if denominator <= 0:
            return 0.0
        return numerator / denominator

    @staticmethod
    def _sample_average_ms(samples: list[float]) -> float:
        if not samples:
            return 0.0
        return (sum(samples) / len(samples)) * 1000.0

    @staticmethod
    def _sample_percentile_ms(samples: list[float], percentile: float) -> float:
        if not samples:
            return 0.0
        sorted_samples = sorted(samples)
        index = int((len(sorted_samples) - 1) * percentile)
        return sorted_samples[index] * 1000.0

    def _recover_from_runtime_repository(self) -> None:
        """Recover runtime task snapshots from repository on manager startup."""
        if self._runtime_repository is None:
            return

        try:
            records = self._runtime_repository.list_task_records()
        except Exception:
            return

        for record in records:
            task = self._record_to_task(record)
            if task is None:
                continue

            # Tasks left pending/running before restart are marked failed.
            if task.status in (TaskStatus.PENDING, TaskStatus.RUNNING):
                task.status = TaskStatus.FAILED
                if not task.error:
                    task.error = "Task recovered after process restart before completion"
                task.completed_at = datetime.now()
                task.set_completed()

            self._tasks[task.id] = task
            self._stats["recovered"] += 1

            idempotency_key = task.metadata.get("idempotency_key")
            if isinstance(idempotency_key, str) and idempotency_key:
                self._idempotency_index[idempotency_key] = task.id

            self._persist_task(task)

    def _record_to_task(self, record: dict[str, Any]) -> Optional[Task]:
        """Convert persisted runtime record to Task instance."""
        if not isinstance(record, dict):
            return None
        if "id" not in record or "type" not in record:
            return None

        try:
            task = create_task_from_dict(record)
        except Exception:
            return None

        created_at = self._parse_datetime(record.get("created_at"))
        started_at = self._parse_datetime(record.get("started_at"))
        completed_at = self._parse_datetime(record.get("completed_at"))
        if created_at is not None:
            task.created_at = created_at
        task.started_at = started_at
        task.completed_at = completed_at

        result_payload = record.get("result")
        if isinstance(result_payload, dict):
            task.result = TaskResult(
                code=int(result_payload.get("code", 0)),
                stdout=str(result_payload.get("stdout", "")),
                stderr=str(result_payload.get("stderr", "")),
                error=result_payload.get("error"),
            )

        if task.is_completed:
            task.set_completed()

        return task

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        """Parse ISO datetime string to datetime object."""
        if not isinstance(value, str) or not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None


def get_task_manager() -> TaskManager:
    """Get the global task manager."""
    return TaskManager.get_instance()


def set_task_manager(manager: TaskManager) -> None:
    """Set the global task manager."""
    TaskManager._instance = manager


def create_persistent_task_manager(working_directory: str) -> TaskManager:
    """Create TaskManager with file-backed runtime repository enabled."""
    from claude_code.tasks.repository import create_file_runtime_task_repository

    runtime_repo = create_file_runtime_task_repository(working_directory)
    return TaskManager(
        task_queue=InMemoryTaskQueue(),
        runtime_repository=runtime_repo,
    )
