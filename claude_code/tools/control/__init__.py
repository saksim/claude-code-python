"""
Claude Code Python - Task Control Tools
Tools for controlling background tasks.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- pathlib.Path for file operations
"""

from __future__ import annotations

from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class TaskStopTool(Tool):
    """Tool to stop a running background task.
    
    This tool allows users to terminate a currently executing
    background task by providing its task ID.
    
    Attributes:
        name: task_stop
        description: Stop a running background task
    
    Example:
        >>> result = await tool.execute(
        ...     {"task_id": "task-123"},
        ...     context,
        ... )
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "task_stop"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Stop a running background task"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "ID of the task to stop"
                }
            },
            "required": ["task_id"]
        }
    
    def is_read_only(self) -> bool:
        """Tool modifies system state by stopping tasks.
        
        Returns:
            False since this tool can terminate running tasks.
        """
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the task stop action.
        
        Args:
            input_data: Dictionary with 'task_id'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult indicating success or error.
        """
        task_id = input_data.get("task_id", "")
        
        if not task_id:
            return ToolResult(content="Error: task_id is required", is_error=True)
        
        try:
            from ...tasks.manager import TaskManager
            manager = TaskManager()
            await manager.stop_task(task_id)
            return ToolResult(content=f"Stopped task: {task_id}")
        except Exception as e:
            return ToolResult(content=f"Error: {str(e)}", is_error=True)


class TaskOutputTool(Tool):
    """Tool to get output from a background task.
    
    This tool retrieves the stdout/stderr output from a running
    or completed background task. Optionally clears the output
    after retrieval.
    
    Attributes:
        name: task_output
        description: Get output from a background task
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "task_output"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Get output from a background task"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "ID of the task"
                },
                "clear": {
                    "type": "boolean",
                    "description": "Clear output after reading",
                    "default": False
                }
            },
            "required": ["task_id"]
        }
    
    def is_read_only(self) -> bool:
        """Tool only reads output, may optionally clear.
        
        Returns:
            True since reading task output is a read operation.
        """
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the task output retrieval.
        
        Args:
            input_data: Dictionary with 'task_id' and optional 'clear'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with task output content.
        """
        task_id = input_data.get("task_id", "")
        clear = input_data.get("clear", False)
        
        if not task_id:
            return ToolResult(content="Error: task_id is required", is_error=True)
        
        try:
            from ...tasks.manager import TaskManager
            manager = TaskManager()
            task = manager.get_task(task_id)
            
            if task is None:
                return ToolResult(content=f"Task not found: {task_id}", is_error=True)
            
            output = task.output or "(no output)"
            
            if clear:
                task.output = ""
            
            return ToolResult(content=output)
        except Exception as e:
            return ToolResult(content=f"Error: {str(e)}", is_error=True)


class TaskControlListTool(Tool):
    """Tool to list background tasks (control perspective).
    
    This tool provides visibility into all background tasks,
    with optional filtering by task status (running, completed, failed).
    
    Differentiated from workflow TaskListTool which lists workflow tasks.
    
    Attributes:
        name: task_control_list
        description: List background tasks with status filtering
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "task_control_list"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "List all background tasks"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status (running, completed, failed, or all)",
                    "enum": ["running", "completed", "failed", "all"],
                    "default": "all"
                }
            },
            "required": []
        }
    
    def is_read_only(self) -> bool:
        """Tool only lists tasks, never modifies.
        
        Returns:
            True since task listing is a read operation.
        """
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the task list retrieval.
        
        Args:
            input_data: Dictionary with optional 'status' filter.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with formatted list of tasks.
        """
        status_filter = input_data.get("status", "all")
        
        try:
            from ...tasks.manager import TaskManager
            manager = TaskManager()
            
            tasks = manager.list_tasks()
            
            if status_filter != "all":
                tasks = [t for t in tasks if t.status.value == status_filter]
            
            if not tasks:
                return ToolResult(content="No tasks found")
            
            lines: list[str] = ["# Tasks\n"]
            for task in tasks:
                lines.append(f"\n## {task.id}")
                lines.append(f"Status: {task.status.value}")
                lines.append(f"Command: {task.command[:50]}...")
            
            return ToolResult(content="\n".join(lines))
        except Exception as e:
            return ToolResult(content=f"Error: {str(e)}", is_error=True)


__all__ = ["TaskStopTool", "TaskOutputTool", "TaskControlListTool"]
