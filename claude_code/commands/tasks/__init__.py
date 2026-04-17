"""
Claude Code Python - Tasks Command

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- pathlib.Path for file operations
"""

from __future__ import annotations

import uuid
from pathlib import Path

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType
from claude_code.tasks.repository import create_file_task_repository


class TasksCommand(Command):
    """Manage tasks within Claude Code.
    
    Provides subcommands to create, list, complete, and remove tasks
    stored in .claude/tasks.json.
    """
    
    def __init__(self) -> None:
        """Initialize the tasks command."""
        super().__init__(
            name="tasks",
            description="Manage tasks",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the tasks command.
        
        Args:
            args: Command arguments (subcommand and its args).
            context: The command execution context.
            
        Returns:
            CommandResult with subcommand output.
        """
        args = args.strip()
        
        if not args:
            return await self._list_tasks(context)
        
        parts = args.split()
        subcmd = parts[0]
        
        if subcmd == "list":
            return await self._list_tasks(context)
        
        if subcmd == "create":
            if len(parts) < 2:
                return CommandResult(success=False, error="Usage: /tasks create <description>")
            return await self._create_task(" ".join(parts[1:]), context)
        
        if subcmd == "complete":
            if len(parts) < 2:
                return CommandResult(success=False, error="Usage: /tasks complete <id>")
            return await self._complete_task(parts[1], context)
        
        if subcmd == "remove":
            if len(parts) < 2:
                return CommandResult(success=False, error="Usage: /tasks remove <id>")
            return await self._remove_task(parts[1], context)
        
        return CommandResult(success=False, error=f"Unknown: {subcmd}")
    
    async def _list_tasks(self, context: CommandContext) -> CommandResult:
        """List all tasks.
        
        Args:
            context: The command execution context.
            
        Returns:
            CommandResult with task list.
        """
        tasks_file = Path(context.working_directory) / ".claude" / "tasks.json"
        
        if not tasks_file.exists():
            return CommandResult(content="No tasks found")
        
        repository = create_file_task_repository(context.working_directory)
        tasks = repository.list_tasks()
        
        if not tasks:
            return CommandResult(content="No tasks found")
        
        lines: list[str] = ["# Tasks\n"]
        
        for task in tasks:
            task_id = str(task.get("id", "N/A"))
            status = task.get("status", "pending")
            title = task.get("title", "Untitled")
            desc = task.get("description", "")
            lines.append(f"\n## {task_id}: {title}")
            lines.append(f"Status: {status}")
            lines.append(f"Description: {desc}")
        
        return CommandResult(content="\n".join(lines))
    
    async def _create_task(self, description: str, context: CommandContext) -> CommandResult:
        """Create a new task.
        
        Args:
            description: Description of the new task.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success.
        """
        tasks_file = Path(context.working_directory) / ".claude" / "tasks.json"
        tasks_file.parent.mkdir(exist_ok=True)
        
        task_id = str(uuid.uuid4())[:8]
        repository = create_file_task_repository(context.working_directory)
        repository.create_task(
            title=description[:60],
            description=description,
            status="pending",
            task_id=task_id,
            created_at=None,
        )
        
        return CommandResult(content=f"Created task: {task_id}")
    
    async def _complete_task(self, task_id: str, context: CommandContext) -> CommandResult:
        """Mark a task as completed.
        
        Args:
            task_id: ID of the task to complete.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success or failure.
        """
        tasks_file = Path(context.working_directory) / ".claude" / "tasks.json"
        
        if not tasks_file.exists():
            return CommandResult(success=False, error="No tasks found")
        
        repository = create_file_task_repository(context.working_directory)
        task = repository.update_task(task_id, status="completed")
        if task is None:
            return CommandResult(success=False, error=f"Task not found: {task_id}")
        
        return CommandResult(content=f"Completed task: {task_id}")
    
    async def _remove_task(self, task_id: str, context: CommandContext) -> CommandResult:
        """Remove a task.
        
        Args:
            task_id: ID of the task to remove.
            context: The command execution context.
            
        Returns:
            CommandResult indicating success or failure.
        """
        tasks_file = Path(context.working_directory) / ".claude" / "tasks.json"
        
        if not tasks_file.exists():
            return CommandResult(success=False, error="No tasks found")
        
        repository = create_file_task_repository(context.working_directory)
        if not repository.delete_task(task_id):
            return CommandResult(success=False, error=f"Task not found: {task_id}")
        
        return CommandResult(content=f"Removed task: {task_id}")


def create_tasks_command() -> TasksCommand:
    return TasksCommand()


__all__ = ["TasksCommand", "create_tasks_command"]
