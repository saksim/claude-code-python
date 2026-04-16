"""
Claude Code Python - Task Update Tool
Update a task's status.

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
TASK_STATUS_OPTIONS: tuple[str, ...] = ("pending", "in_progress", "completed")


class TaskUpdateTool(Tool):
    """Tool to update a task's status.
    
    Modifies task data in a JSON file to update status
    or other details of an existing task.
    
    Attributes:
        name: Tool name
        description: Tool description for the API
    """
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "task_update"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Update a task's status or details"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "ID of the task to update"
                },
                "status": {
                    "type": "string",
                    "enum": list(TASK_STATUS_OPTIONS),
                    "description": "New status"
                },
                "title": {
                    "type": "string",
                    "description": "New title (optional)"
                },
                "description": {
                    "type": "string",
                    "description": "New description (optional)"
                }
            },
            "required": ["task_id"]
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Update a task's status or details.
        
        Args:
            input_data: Dictionary with 'task_id' and optional updates.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with success message or error.
        """
        task_id: str = input_data.get("task_id", "")
        status: str = input_data.get("status", "")
        title: Optional[str] = input_data.get("title")
        description: Optional[str] = input_data.get("description")
        
        if not task_id:
            return ToolResult(content="Error: task_id is required", is_error=True)
        
        try:
            repository = create_file_task_repository(context.working_directory)
            updates: dict[str, Any] = {}
            if status:
                updates["status"] = status
            if title is not None:
                updates["title"] = title
            if description is not None:
                updates["description"] = description

            task = repository.update_task(task_id, **updates)
            if task is None:
                return ToolResult(content=f"Task {task_id} not found", is_error=True)
            
            update_messages: list[str] = []
            if status:
                update_messages.append(f"status to {status}")
            if title:
                update_messages.append(f"title to '{title}'")
            if description:
                update_messages.append("description updated")
            
            update_str = ", ".join(update_messages) if update_messages else "updated"
            return ToolResult(content=f"Task {task_id} {update_str}")
            
        except Exception as e:
            return ToolResult(content=f"Error: {str(e)}", is_error=True)
