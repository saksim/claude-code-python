"""
Claude Code Python - Write Tool
Write content to files.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class WriteTool(Tool):
    """Tool to write content to files.
    
    This tool creates new files or overwrites existing files with the provided content.
    It supports both creating new files and appending to existing files.
    """
    
    @property
    def name(self) -> str:
        return "write"
    
    @property
    def description(self) -> str:
        return "Write content to a file, creating or overwriting it"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                },
                "append": {
                    "type": "boolean",
                    "description": "Append to file instead of overwriting",
                    "default": False
                }
            },
            "required": ["file_path", "content"]
        }
    
    def is_destructive(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the write tool.
        
        Args:
            input_data: Dictionary containing file_path, content, and optional append flag
            context: Tool execution context with working directory
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with success message or error details
        """
        file_path = input_data.get("file_path", "")
        content = input_data.get("content", "")
        append = input_data.get("append", False)
        
        if not file_path:
            return ToolResult(content="Error: file_path is required", is_error=True)
        
        if not os.path.isabs(file_path):
            file_path = os.path.join(context.working_directory, file_path)
        
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            mode = 'a' if append else 'w'
            with open(file_path, mode, encoding='utf-8') as f:
                f.write(content)
            
            action = "Appended to" if append else "Written"
            return ToolResult(content=f"{action} {file_path}")
            
        except OSError as e:
            return ToolResult(content=f"Error writing file: {e}", is_error=True)
