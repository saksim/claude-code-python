"""
Claude Code Python - Task Get Tool
Get details of a task.

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


class TaskGetTool(Tool):
    """Tool to get details of a specific task.
    
    Reads task data from JSON file and returns details
    for a specific task by ID.
    
    Attributes:
        name: Tool name
        description: Tool description for the API
    """
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "task_get"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Get details of a specific task by ID"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "ID of the task to retrieve"
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
        """Get details of a specific task.
        
        Args:
            input_data: Dictionary with 'task_id'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with task details or error message.
        """
        task_id: str = input_data.get("task_id", "")
        
        if not task_id:
            return ToolResult(content="Error: task_id is required", is_error=True)
        
        try:
            repository = create_file_task_repository(context.working_directory)
            task = repository.get_task(task_id)
            if task is None:
                return ToolResult(content=f"Task {task_id} not found", is_error=True)

            lines = [
                f"Task: {task.get('title', 'Untitled')}",
                f"Status: {task.get('status', 'pending')}",
                f"ID: {task.get('id', 'N/A')}",
            ]
            if desc := task.get("description"):
                lines.append(f"Description: {desc}")
            return ToolResult(content="\n".join(lines))
            
        except Exception as e:
            return ToolResult(content=f"Error: {str(e)}", is_error=True)
