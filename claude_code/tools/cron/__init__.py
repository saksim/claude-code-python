"""
Claude Code Python - Schedule/Cron Tools
Scheduled task management.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- pathlib.Path for file operations
"""

from __future__ import annotations

from typing import Any, Optional
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback
from claude_code.tools.cron.create import (
    CronCreateTool,
    _SESSION_ONLY_TASKS,
    _load_persisted_tasks,
    _save_persisted_tasks,
)


_SCHEDULE_FILE_NAME = "scheduled_tasks.json"


class ScheduleCronTool(Tool):
    """Schedule a task to run at intervals using cron expressions.
    
    This tool allows users to schedule tasks to run at specified
    intervals using cron syntax. Schedules are persisted to disk
    and managed by the Claude Code background runner.
    
    Attributes:
        name: schedule_cron
        description: Schedule a task to run on a cron schedule
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "schedule_cron"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Schedule a task to run on a cron schedule"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command or task to run"
                },
                "schedule": {
                    "type": "string",
                    "description": "Cron expression (e.g., '0 * * * *' for hourly)"
                },
                "name": {
                    "type": "string",
                    "description": "Name for this schedule"
                },
                "enabled": {
                    "type": "boolean",
                    "description": "Enable/disable schedule",
                    "default": True
                }
            },
            "required": ["command", "schedule"]
        }
    
    def is_read_only(self) -> bool:
        """Tool modifies system state by creating schedules.
        
        Returns:
            False since this tool creates scheduled tasks.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the schedule creation.
        
        Args:
            input_data: Dictionary with 'command', 'schedule', optional 'name', 'enabled'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with schedule creation status.
        """
        command = input_data.get("command", "")
        schedule = input_data.get("schedule", "")
        name = input_data.get("name", str(uuid4())[:8])
        enabled = bool(input_data.get("enabled", True))
        
        if not command or not schedule:
            return ToolResult(
                content="Error: command and schedule are required",
                is_error=True
            )
        
        schedule_file = Path(context.working_directory) / ".claude" / _SCHEDULE_FILE_NAME
        schedules = _load_persisted_tasks(schedule_file)
        schedules[name] = {
            "cron": schedule,
            "prompt": command,
            "recurring": True,
            "durable": True,
            "status": "active" if enabled else "disabled",
            "created_at": datetime.now().isoformat(),
            "last_run": None,
            "source": "schedule_cron",
            "name": name,
        }
        _save_persisted_tasks(schedule_file, schedules)
        
        return ToolResult(content=f"""# Schedule Created

**Name:** {name}
**Command:** {command}
**Schedule:** {schedule}
**Enabled:** {enabled}
**Stored In:** .claude/{_SCHEDULE_FILE_NAME}

Use /schedule list to see all schedules.""")


class CronListTool(Tool):
    """List all scheduled tasks.
    
    This tool displays all configured cron schedules including
    their commands, schedules, and enabled status.
    
    Attributes:
        name: cron_list
        description: List all scheduled tasks
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "cron_list"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "List all scheduled tasks"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema (no parameters required).
        """
        return {"type": "object", "properties": {}}
    
    def is_read_only(self) -> bool:
        """Tool only reads schedule information.
        
        Returns:
            True since listing is a read operation.
        """
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the schedule listing.
        
        Args:
            input_data: Empty dictionary (no parameters).
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with list of schedules.
        """
        schedule_file = Path(context.working_directory) / ".claude" / _SCHEDULE_FILE_NAME
        persisted = _load_persisted_tasks(schedule_file)
        if not persisted and not _SESSION_ONLY_TASKS:
            return ToolResult(content="No schedules configured")
        
        lines = ["# Scheduled Tasks\n"]

        for name, config in persisted.items():
            cron = str(config.get("cron", config.get("schedule", "")))
            prompt = str(config.get("prompt", config.get("command", "")))
            enabled = str(config.get("status", "active")).lower() == "active"
            lines.append(f"\n## {name}")
            lines.append(f"Prompt/Command: {prompt}")
            lines.append(f"Cron: {cron}")
            lines.append(f"Enabled: {enabled}")
            lines.append("Durable: True")
            lines.append(f"Created: {config.get('created_at', 'unknown')}")

        for name, config in _SESSION_ONLY_TASKS.items():
            cron = str(config.get("cron", ""))
            prompt = str(config.get("prompt", ""))
            enabled = str(config.get("status", "active")).lower() == "active"
            lines.append(f"\n## {name}")
            lines.append(f"Prompt/Command: {prompt}")
            lines.append(f"Cron: {cron}")
            lines.append(f"Enabled: {enabled}")
            lines.append("Durable: False (session-only)")
            lines.append(f"Created: {config.get('created_at', 'unknown')}")
        
        return ToolResult(content="\n".join(lines))


class CronDeleteTool(Tool):
    """Delete a scheduled task.
    
    This tool removes a scheduled task from the schedule configuration.
    
    Attributes:
        name: cron_delete
        description: Delete a scheduled task
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "cron_delete"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Delete a scheduled task"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of schedule to delete"
                }
            },
            "required": ["name"]
        }
    
    def is_read_only(self) -> bool:
        """Tool modifies system state by deleting schedules.
        
        Returns:
            False since this tool removes scheduled tasks.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the schedule deletion.
        
        Args:
            input_data: Dictionary with 'name'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with deletion status.
        """
        name = input_data.get("name", "")
        
        if not name:
            return ToolResult(content="Error: name is required", is_error=True)
        
        schedule_file = Path(context.working_directory) / ".claude" / _SCHEDULE_FILE_NAME
        schedules = _load_persisted_tasks(schedule_file)

        deleted = False
        if name in schedules:
            del schedules[name]
            _save_persisted_tasks(schedule_file, schedules)
            deleted = True
        if name in _SESSION_ONLY_TASKS:
            del _SESSION_ONLY_TASKS[name]
            deleted = True

        if not deleted:
            return ToolResult(content=f"Schedule not found: {name}", is_error=True)

        return ToolResult(content=f"Deleted schedule: {name}")


__all__ = ["ScheduleCronTool", "CronListTool", "CronDeleteTool", "CronCreateTool"]
