"""
Claude Code Python - Schedule/Cron Tools
Scheduled task management.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- pathlib.Path for file operations
"""

from __future__ import annotations

import os
import json
import subprocess
from typing import Any, Optional
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


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
        enabled = input_data.get("enabled", True)
        
        if not command or not schedule:
            return ToolResult(
                content="Error: command and schedule are required",
                is_error=True
            )
        
        schedule_file = Path(context.working_directory) / ".claude" / "schedules.json"
        schedule_file.parent.mkdir(exist_ok=True)
        
        schedules = {}
        if schedule_file.exists():
            with open(schedule_file) as f:
                schedules = json.load(f)
        
        schedules[name] = {
            "command": command,
            "schedule": schedule,
            "enabled": enabled,
            "created_at": datetime.now().isoformat(),
        }
        
        with open(schedule_file, "w") as f:
            json.dump(schedules, f, indent=2)
        
        return ToolResult(content=f"""# Schedule Created

**Name:** {name}
**Command:** {command}
**Schedule:** {schedule}
**Enabled:** {enabled}

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
        schedule_file = Path(context.working_directory) / ".claude" / "schedules.json"
        
        if not schedule_file.exists():
            return ToolResult(content="No schedules configured")
        
        with open(schedule_file) as f:
            schedules = json.load(f)
        
        if not schedules:
            return ToolResult(content="No schedules configured")
        
        lines = ["# Scheduled Tasks\n"]
        
        for name, config in schedules.items():
            lines.append(f"\n## {name}")
            lines.append(f"Command: {config['command']}")
            lines.append(f"Schedule: {config['schedule']}")
            lines.append(f"Enabled: {config['enabled']}")
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
        
        schedule_file = Path(context.working_directory) / ".claude" / "schedules.json"
        
        if not schedule_file.exists():
            return ToolResult(content=f"Schedule not found: {name}", is_error=True)
        
        with open(schedule_file) as f:
            schedules = json.load(f)
        
        if name not in schedules:
            return ToolResult(content=f"Schedule not found: {name}", is_error=True)
        
        del schedules[name]
        
        with open(schedule_file, "w") as f:
            json.dump(schedules, f, indent=2)
        
        return ToolResult(content=f"Deleted schedule: {name}")


__all__ = ["ScheduleCronTool", "CronListTool", "CronDeleteTool"]
