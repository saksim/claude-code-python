"""
Claude Code Python - Task List Tool
List all tasks.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- pathlib.Path for file operations
- Proper error handling
"""

from __future__ import annotations

from typing import Optional, Any

from claude_code.tasks.repository import create_file_task_repository
from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


# Task status values
TASK_STATUS_OPTIONS: tuple[str, ...] = ("pending", "in_progress", "completed", "all")
DEFAULT_TASK_STATUS: str = "all"


class TaskListTool(Tool):
    """Tool to list all tasks.
    
    Reads task data from a JSON file in the working directory
    and optionally filters by status.
    
    Attributes:
        name: Tool name
        description: Tool description for the API
    """
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "task_list"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "List all tasks"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": list(TASK_STATUS_OPTIONS),
                    "description": "Filter by status",
                    "default": DEFAULT_TASK_STATUS,
                }
            }
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """List all tasks, optionally filtered by status.
        
        Args:
            input_data: Dictionary with optional 'status' filter.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with task list or error message.
        """
        status_filter: str = input_data.get("status", DEFAULT_TASK_STATUS)
        
        try:
            repository = create_file_task_repository(context.working_directory)
            tasks = repository.list_tasks()

            if status_filter != DEFAULT_TASK_STATUS:
                tasks = [t for t in tasks if t.get("status") == status_filter]
            
            if not tasks:
                return ToolResult(content=f"No {status_filter} tasks")
            
            lines: list[str] = [f"Tasks ({status_filter}):", ""]
            for i, task in enumerate(tasks, 1):
                lines.append(f"{i}. {task.get('title', 'Untitled')} ({task.get('id', 'N/A')})")
                lines.append(f"   Status: {task.get('status', 'pending')}")
            
            return ToolResult(content="\n".join(lines))
            
        except Exception as e:
            return ToolResult(content=f"Error: {str(e)}", is_error=True)
