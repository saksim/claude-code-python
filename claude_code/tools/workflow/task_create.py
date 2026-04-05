"""
Claude Code Python - Task Create Tool
Create a new task.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Pathlib for file operations
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class TaskCreateTool(Tool):
    """Tool to create a new task.
    
    Creates a task and stores it in .claude/tasks.json in the working directory.
    Each task has a unique ID, title, description, and status.
    """
    
    TASKS_FILE = ".claude/tasks.json"
    MAX_DURATION = 300
    
    @property
    def name(self) -> str:
        return "task_create"
    
    @property
    def description(self) -> str:
        return "Create a new task"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Task title"
                },
                "description": {
                    "type": "string",
                    "description": "Task description"
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "in_progress", "completed"],
                    "description": "Initial status",
                    "default": "pending"
                }
            },
            "required": ["title"]
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the task create tool.
        
        Args:
            input_data: Dictionary containing title, description, status
            context: Tool execution context with working directory
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with success message or error details
        """
        title = input_data.get("title", "")
        description = input_data.get("description", "")
        status = input_data.get("status", "pending")
        
        if not title:
            return ToolResult(content="Error: title is required", is_error=True)
        
        task_dir = Path(context.working_directory) / ".claude"
        task_dir.mkdir(parents=True, exist_ok=True)
        
        task_file = task_dir / "tasks.json"
        
        tasks: list[dict[str, Any]] = []
        if task_file.exists():
            try:
                tasks = json.loads(task_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        
        task_id = str(uuid4())[:8]
        
        task: dict[str, Any] = {
            "id": task_id,
            "title": title,
            "description": description,
            "status": status,
        }
        
        tasks.append(task)
        
        task_file.write_text(json.dumps(tasks, indent=2, ensure_ascii=False), encoding="utf-8")
        
        return ToolResult(content=f"Task #{task_id} created: {title}")
