"""
Claude Code Python - Send User File Tool

Allows sending a file to the user for download.

Following TOP Python Dev standards:
- Frozen dataclasses for immutable configs
- Clear type hints
- Comprehensive docstrings

This is a stub implementation that provides the interface.
Real implementation would integrate with file transfer mechanisms.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from claude_code.tools.base import Tool, ToolResult
from claude_code.tools.base import ToolDefinition, ToolContext


class SendUserFileTool(Tool):
    """Send a file to the user for download.
    
    This tool allows the AI to send files back to the user for download.
    It's useful when the user wants to export generated content.
    
    Attributes:
        name: Tool name
        description: Tool description
        input_schema: JSON schema for tool input
    """
    
    def __init__(self) -> None:
        self._name = "send_user_file"
        self._description = "Send a file to the user for download"
        self._input_schema = {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to send",
                },
                "description": {
                    "type": "string",
                    "description": "Description of the file",
                },
            },
            "required": ["file_path"],
        }
    
    @property
    def name(self) -> str:
        """Tool name."""
        return self._name
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return self._description
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return self._input_schema
    
    def get_definition(self) -> ToolDefinition:
        """Get tool definition."""
        return ToolDefinition(
            name=self.name,
            description=self.description,
            input_schema=self.input_schema,
        )
    
    async def execute(
        self,
        params: dict[str, Any],
        context: ToolContext,
    ) -> ToolResult:
        """Execute the tool.
        
        Args:
            params: Tool parameters
            context: Tool execution context
            
        Returns:
            ToolResult with the file information
        """
        file_path = params.get("file_path", "")
        description = params.get("description", "")
        
        if not file_path:
            return ToolResult(
                tool_name=self._name,
                content="Error: file_path is required",
                is_error=True,
            )
        
        path = Path(file_path)
        
        if not path.exists():
            return ToolResult(
                tool_name=self._name,
                content=f"Error: File not found: {file_path}",
                is_error=True,
            )
        
        content = f"File ready for download: {path.name}"
        if description:
            content += f"\n\nDescription: {description}"
        
        content += f"\n\nSize: {path.stat().st_size} bytes"
        
        return ToolResult(
            tool_name=self._name,
            content=content,
            is_error=False,
        )


__all__ = ["SendUserFileTool"]