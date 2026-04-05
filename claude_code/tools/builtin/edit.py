"""
Claude Code Python - Edit Tool
Make targeted edits to files.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class EditTool(Tool):
    """Tool to make targeted edits to files.
    
    This tool performs precise string replacement in files. It replaces the first
    occurrence of the specified old_string with the new_string.
    """
    
    @property
    def name(self) -> str:
        return "edit"
    
    @property
    def description(self) -> str:
        return "Make a targeted edit to a file by replacing the specified string"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to edit"
                },
                "old_string": {
                    "type": "string",
                    "description": "The exact string to replace (must match exactly including whitespace)"
                },
                "new_string": {
                    "type": "string",
                    "description": "The replacement string"
                }
            },
            "required": ["file_path", "old_string", "new_string"]
        }
    
    def is_destructive(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the edit tool.
        
        Args:
            input_data: Dictionary containing file_path, old_string, and new_string
            context: Tool execution context with working directory
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with success message or error details
            
        Raises:
            ValueError: If file_path or old_string is empty
            FileNotFoundError: If the specified file does not exist
        """
        file_path = input_data.get("file_path", "")
        old_string = input_data.get("old_string", "")
        new_string = input_data.get("new_string", "")
        
        if not file_path:
            return ToolResult(content="Error: file_path is required", is_error=True)
        
        if not old_string:
            return ToolResult(content="Error: old_string is required", is_error=True)
        
        if not os.path.isabs(file_path):
            file_path = os.path.join(context.working_directory, file_path)
        
        path = Path(file_path)
        if not path.exists():
            return ToolResult(content=f"File not found: {file_path}", is_error=True)
        
        try:
            content = path.read_text(encoding='utf-8')
            
            if old_string not in content:
                return ToolResult(
                    content="old_string not found in file. Make sure to match the exact text including whitespace.",
                    is_error=True
                )
            
            new_content = content.replace(old_string, new_string, 1)
            
            path.write_text(new_content, encoding='utf-8')
            
            return ToolResult(content=f"Successfully edited {file_path}")
            
        except OSError as e:
            return ToolResult(content=f"Error editing file: {e}", is_error=True)
