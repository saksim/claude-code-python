"""
Claude Code Python - Tasks Module

Provides task management for background command execution.

Tasks allow running shell commands, agents, and workflows in the background
while continuing to interact with the user.
"""

from claude_code.tasks.types import (
    TaskType,
    TaskStatus,
    TaskResult,
    Task,
    BashTask,
    AgentTask,
    WorkflowTask,
    is_background_task,
    create_task_from_dict,
)

from claude_code.tasks.manager import (
    TaskManager,
    TaskEvent,
    get_task_manager,
    set_task_manager,
)

from claude_code.tasks.shell import (
    ShellTaskExecutor,
    run_background_bash,
    run_bash,
)
from claude_code.tasks.repository import (
    TaskRepositoryConfig,
    TaskRepository,
    create_file_task_repository,
)

__all__ = [
    # Types
    "TaskType",
    "TaskStatus",
    "TaskResult",
    "Task",
    "BashTask",
    "AgentTask",
    "WorkflowTask",
    "is_background_task",
    "create_task_from_dict",
    
    # Manager
    "TaskManager",
    "TaskEvent",
    "get_task_manager",
    "set_task_manager",
    
    # Shell
    "ShellTaskExecutor",
    "run_background_bash",
    "run_bash",
    
    # Repository
    "TaskRepositoryConfig",
    "TaskRepository",
    "create_file_task_repository",
]


# Example usage:
#
# # Create a background bash task
# task = await run_background_bash("npm run build")
#
# # Check task status
# task = get_task_manager().get_task(task.id)
# print(f"Status: {task.status}")
#
# # Wait for completion
# await get_task_manager().wait_for_task(task.id)
#
# # Get result
# task = get_task_manager().get_task(task.id)
# print(f"Output: {task.result.stdout}")
