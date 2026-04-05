"""
Claude Code Python - Glob Tool
Find files by glob pattern.
"""

from __future__ import annotations

import glob as glob_module
import os
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class GlobTool(Tool):
    """Tool to find files by glob pattern.
    
    This tool searches for files matching a glob pattern within a directory.
    Supports recursive patterns (e.g., '**/*.py') for deep file discovery.
    """
    
    MAX_RESULTS = 100
    
    @property
    def name(self) -> str:
        return "glob"
    
    @property
    def description(self) -> str:
        return "Find files by glob pattern"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match (e.g., '**/*.py')",
                    "default": "**/*"
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in",
                }
            }
        }
    
    def is_read_only(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the glob tool.
        
        Args:
            input_data: Dictionary containing pattern and optional path
            context: Tool execution context with working directory
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with list of matching files or error message
        """
        pattern = input_data.get("pattern", "**/*")
        path = input_data.get("path") or context.working_directory
        
        if not os.path.isabs(path):
            path = os.path.join(context.working_directory, path)
        
        try:
            matches = glob_module.glob(
                pattern,
                root_dir=path,
                recursive=True
            )
            
            matches = [m for m in matches if os.path.isfile(os.path.join(path, m))]
            
            if not matches:
                return ToolResult(content="No files found")
            
            lines = ["Found files:", ""]
            for match in sorted(matches)[:self.MAX_RESULTS]:
                lines.append(f"./{match}")
            
            if len(matches) > self.MAX_RESULTS:
                lines.append(f"\n... and {len(matches) - self.MAX_RESULTS} more files")
            
            return ToolResult(content="\n".join(lines))
            
        except OSError as e:
            return ToolResult(content=f"Error searching files: {e}", is_error=True)
