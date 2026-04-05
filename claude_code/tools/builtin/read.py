"""
Claude Code Python - Read Tool
Read file contents.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Proper file path handling with pathlib.Path
- Offset/limit support for large files
- Proper error handling
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


# Default constants
DEFAULT_OFFSET: int = 1
DEFAULT_FILE_ENCODING: str = "utf-8"


class ReadTool(Tool):
    """Tool to read file contents.
    
    A read-only tool that safely reads file contents with support
    for partial reads via offset and limit parameters.
    
    Attributes:
        name: Tool name
        description: Tool description for the API
    
    Example:
        >>> tool = ReadTool()
        >>> result = await tool.execute({"file_path": "example.txt"}, context)
    """
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "read"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Read the contents of a file"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path to the file to read"
                },
                "offset": {
                    "type": "integer",
                    "description": "Line number to start reading from (1-indexed)",
                    "default": DEFAULT_OFFSET
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of lines to read"
                }
            },
            "required": ["file_path"]
        }
    
    def is_read_only(self) -> bool:
        """Read tool only reads files, never modifies."""
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Read file contents.
        
        Args:
            input_data: Dictionary with 'file_path', optional 'offset' and 'limit'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with file contents or error message.
        """
        file_path: str = input_data.get("file_path", "")
        offset: int = input_data.get("offset", DEFAULT_OFFSET)
        limit: Optional[int] = input_data.get("limit")
        
        if not file_path:
            return ToolResult(
                content="Error: file_path is required",
                is_error=True
            )
        
        # Resolve relative paths against working directory using pathlib
        path = Path(file_path)
        if not path.is_absolute():
            path = Path(context.working_directory) / path
        
        # Check if file exists
        if not path.exists():
            return ToolResult(
                content=f"File not found: {path}",
                is_error=True
            )
        
        # Check if it's a file (not a directory)
        if not path.is_file():
            return ToolResult(
                content=f"Not a file: {path}",
                is_error=True
            )
        
        try:
            with open(path, 'r', encoding=DEFAULT_FILE_ENCODING, errors='replace') as f:
                lines = f.readlines()
            
            # Calculate slice indices (convert from 1-indexed to 0-indexed)
            start_idx = max(0, offset - 1)
            end_idx = len(lines) if limit is None else start_idx + limit
            
            content = "".join(lines[start_idx:end_idx])
            
            return ToolResult(content=content)
            
        except PermissionError:
            return ToolResult(
                content=f"Permission denied: {path}",
                is_error=True
            )
        except UnicodeDecodeError:
            return ToolResult(
                content=f"Unable to decode file (try binary read): {path}",
                is_error=True
            )
        except Exception as e:
            return ToolResult(
                content=f"Error reading file: {str(e)}",
                is_error=True
            )
