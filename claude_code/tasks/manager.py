"""
Task manager for Claude Code Python.

Manages task execution and tracking.
"""

import asyncio
import uuid
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from claude_code.tasks.types import (
    Task,
    TaskType,
    TaskStatus,
    TaskResult,
    BashTask,
    AgentTask,
    is_background_task,
)


@dataclass
class TaskEvent:
    """Event from task execution."""
    task_id: str
    event_type: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: dict = field(default_factory=dict)


class TaskManager:
    """
    Manages task execution and tracking.
    
    Handles creating, running, and monitoring tasks.
    Supports singleton pattern via get_instance().
    """
    
    _instance: Optional['TaskManager'] = None
    
    def __init__(self):
        self._tasks: dict[str, Task] = {}
        self._background_tasks: set[str] = set()
        self._task_handlers: dict[str, Callable] = {}
        self._event_handlers: list[Callable[[TaskEvent], None]] = []
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
    
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
    ) -> BashTask:
        """Create a bash command task."""
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
        
        self._tasks[task_id] = task
        
        return task
    
    async def create_agent_task(
        self,
        prompt: str,
        model: Optional[str] = None,
        tools: Optional[list] = None,
        background: bool = True,
    ) -> AgentTask:
        """Create an agent task."""
        task_id = str(uuid.uuid4())
        
        task = AgentTask(
            id=task_id,
            prompt=prompt,
            model=model,
            tools=tools,
            is_backgrounded=background,
        )
        
        self._tasks[task_id] = task
        
        return task
    
    async def start_task(
        self,
        task_id: str,
        executor: Optional[Callable] = None,
    ) -> None:
        """Start a task."""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                raise ValueError(f"Task not found: {task_id}")
            
            if task.status != TaskStatus.PENDING:
                raise ValueError(f"Task is not pending: {task_id}")
            
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
        
        self._emit_event(TaskEvent(
            task_id=task_id,
            event_type="started",
        ))
        
        if executor:
            async_task = asyncio.create_task(self._run_task(task_id, executor))
            self._running_tasks[task_id] = async_task
    
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
                task.status = TaskStatus.COMPLETED
                task.result = result
                task.completed_at = datetime.now()
                task.set_completed()
            
            self._emit_event(TaskEvent(
                task_id=task_id,
                event_type="completed",
                data={"result": result},
            ))
            
        except asyncio.TimeoutError:
            async with self._lock:
                task.status = TaskStatus.TIMEOUT
                task.completed_at = datetime.now()
                task.set_completed()
            
            self._emit_event(TaskEvent(
                task_id=task_id,
                event_type="timeout",
            ))
            
        except Exception as e:
            async with self._lock:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.completed_at = datetime.now()
                task.set_completed()
            
            self._emit_event(TaskEvent(
                task_id=task_id,
                event_type="failed",
                data={"error": str(e)},
            ))
            
        finally:
            if task_id in self._running_tasks:
                del self._running_tasks[task_id]
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        async with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                return False
            
            if task_id in self._running_tasks:
                self._running_tasks[task_id].cancel()
                try:
                    await self._running_tasks[task_id]
                except asyncio.CancelledError:
                    pass
            
            task.status = TaskStatus.CANCELLED
            task.completed_at = datetime.now()
            task.set_completed()
        
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
        for handler in self._event_handlers:
            try:
                handler(event)
            except Exception:
                pass
    
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
            del self._tasks[task_id]
        
        return len(completed)


def get_task_manager() -> TaskManager:
    """Get the global task manager."""
    return TaskManager.get_instance()


def set_task_manager(manager: TaskManager) -> None:
    """Set the global task manager."""
    TaskManager._instance = manager
