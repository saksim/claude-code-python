"""
Task types and states for Claude Code Python.

Defines the task state machine and types.
"""

import asyncio
from enum import Enum
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


class TaskType(Enum):
    """Types of tasks."""
    LOCAL_BASH = "local_bash"
    LOCAL_AGENT = "local_agent"
    REMOTE_AGENT = "remote_agent"
    LOCAL_WORKFLOW = "local_workflow"
    MONITOR_MCP = "monitor_mcp"
    DREAM = "dream"


class TaskStatus(Enum):
    """Task status states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class TaskResult:
    """Result from a task execution."""
    code: int = 0
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None


@dataclass
class Task:
    """
    Base task definition.
    
    Represents a unit of work that can be executed in the background.
    """
    id: str
    type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[TaskResult] = None
    error: Optional[str] = None
    is_backgrounded: bool = True
    parent_id: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    _done_event: Optional[asyncio.Event] = None
    
    def _get_done_event(self) -> asyncio.Event:
        """Get or create the done event."""
        if self._done_event is None:
            self._done_event = asyncio.Event()
            if self.is_completed:
                self._done_event.set()
        return self._done_event
    
    async def wait(self) -> None:
        """Wait for the task to complete."""
        if self.is_completed:
            return
        await self._get_done_event().wait()
    
    def get_output(self) -> str:
        """Get the task output as a string."""
        if self.result:
            output = self.result.stdout
            if self.result.stderr:
                output += "\n\nSTDERR:\n" + self.result.stderr
            return output
        
        if self.error:
            return f"Error: {self.error}"
        
        if self.status == TaskStatus.RUNNING:
            return "(Task is still running)"
        
        return "(No output)"
    
    def set_completed(self) -> None:
        """Mark the task as completed and signal waiters."""
        if self._done_event is not None:
            self._done_event.set()
    
    @property
    def duration(self) -> Optional[float]:
        """Get task duration in seconds."""
        if self.started_at is None:
            return None
        
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()
    
    @property
    def is_running(self) -> bool:
        """Check if task is currently running."""
        return self.status == TaskStatus.RUNNING
    
    @property
    def is_completed(self) -> bool:
        """Check if task has completed."""
        return self.status in (
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
            TaskStatus.TIMEOUT,
        )
    
    @property
    def is_failed(self) -> bool:
        """Check if task has failed."""
        return self.status == TaskStatus.FAILED
    
    @property
    def is_success(self) -> bool:
        """Check if task completed successfully."""
        return self.status == TaskStatus.COMPLETED and self.result and self.result.code == 0


@dataclass
class BashTask(Task):
    """A shell command task."""
    
    def __init__(
        self,
        id: str,
        command: str,
        cwd: Optional[str] = None,
        env: Optional[dict] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        super().__init__(
            id=id,
            type=TaskType.LOCAL_BASH,
            description=command,
            **kwargs,
        )
        self.command = command
        self.cwd = cwd
        self.env = env or {}
        self.timeout = timeout


@dataclass
class AgentTask(Task):
    """An agent task (runs Claude)."""
    
    def __init__(
        self,
        id: str,
        prompt: str,
        model: Optional[str] = None,
        tools: Optional[list] = None,
        **kwargs,
    ):
        super().__init__(
            id=id,
            type=TaskType.LOCAL_AGENT,
            description=prompt[:100] + "..." if len(prompt) > 100 else prompt,
            **kwargs,
        )
        self.prompt = prompt
        self.model = model
        self.tools = tools or []
        self.result_content: Optional[str] = None


@dataclass
class WorkflowTask(Task):
    """A workflow task."""
    
    def __init__(
        self,
        id: str,
        steps: list[dict],
        **kwargs,
    ):
        super().__init__(
            id=id,
            type=TaskType.LOCAL_WORKFLOW,
            description=f"Workflow with {len(steps)} steps",
            **kwargs,
        )
        self.steps = steps
        self.current_step: int = 0


def is_background_task(task: Task) -> bool:
    """
    Check if a task should be shown in background tasks indicator.
    
    A task is considered a background task if:
    1. It is running or pending
    2. It has been explicitly backgrounded
    """
    if task.status not in (TaskStatus.RUNNING, TaskStatus.PENDING):
        return False
    
    if hasattr(task, 'is_backgrounded') and task.is_backgrounded is False:
        return False
    
    return True


def create_task_from_dict(data: dict) -> Task:
    """Create a task from a dictionary."""
    task_type = TaskType(data.get("type", "local_bash"))
    
    if task_type == TaskType.LOCAL_BASH:
        return BashTask(
            id=data["id"],
            command=data.get("command", ""),
            cwd=data.get("cwd"),
            env=data.get("env"),
            timeout=data.get("timeout"),
            status=TaskStatus(data.get("status", "pending")),
            description=data.get("description", ""),
        )
    elif task_type == TaskType.LOCAL_AGENT:
        return AgentTask(
            id=data["id"],
            prompt=data.get("prompt", ""),
            model=data.get("model"),
            tools=data.get("tools"),
            status=TaskStatus(data.get("status", "pending")),
            description=data.get("description", ""),
        )
    else:
        return Task(
            id=data["id"],
            type=task_type,
            status=TaskStatus(data.get("status", "pending")),
            description=data.get("description", ""),
        )
