"""
Claude Code Python - Todo Write Tool
Manage todo lists.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Pathlib for file operations
"""

from __future__ import annotations

import json
from typing import Any, Optional
from pathlib import Path

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class TodoWriteTool(Tool):
    """Tool to write/update the todo list.
    
    Stores todo items in .claude/todos.json in the working directory.
    Each todo has content, status (pending/in_progress/completed), and optional active form.
    """
    
    TODO_FILE = ".claude/todos.json"
    MAX_DISPLAY = 50
    
    @property
    def name(self) -> str:
        return "todo_write"
    
    @property
    def description(self) -> str:
        return "Write or update the todo list. Replaces the entire todo list."
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "todos": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "status": {
                                "type": "string",
                                "enum": ["pending", "in_progress", "completed"]
                            },
                            "ACTIVE-FORM": {"type": "string"}
                        },
                        "required": ["content"]
                    },
                    "description": "List of todo items"
                }
            },
            "required": ["todos"]
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the todo write tool.
        
        Args:
            input_data: Dictionary containing todos array
            context: Tool execution context with working directory
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with success message or error details
        """
        todos = input_data.get("todos", [])
        
        todo_dir = Path(context.working_directory) / ".claude"
        todo_dir.mkdir(parents=True, exist_ok=True)
        
        todo_file = todo_dir / "todos.json"
        data: dict[str, Any] = {"todos": todos}
        
        try:
            todo_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            
            if not todos:
                return ToolResult(content="Todo list cleared")
            
            lines: list[str] = ["Current todos:"]
            status_icons = {"completed": "[x]", "in_progress": "[>]", "pending": "[ ]"}
            
            for i, todo in enumerate(todos[:self.MAX_DISPLAY], 1):
                status = todo.get("status", "pending")
                content = todo.get("content", "")
                active = todo.get("ACTIVE-FORM", "")
                
                icon = status_icons.get(status, "[ ]")
                lines.append(f"{icon} {i}. {content}")
                if active:
                    lines.append(f"    {active}")
            
            if len(todos) > self.MAX_DISPLAY:
                lines.append(f"\n... and {len(todos) - self.MAX_DISPLAY} more todos")
            
            return ToolResult(content="\n".join(lines))
            
        except OSError as e:
            return ToolResult(content=f"Error writing todos: {e}", is_error=True)
