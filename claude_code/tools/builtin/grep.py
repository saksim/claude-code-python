"""
Claude Code Python - Grep Tool
Search for patterns in files.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class GrepTool(Tool):
    """Tool to search for patterns in files.
    
    This tool performs regex-based search across files in a directory.
    It supports case sensitivity control and file filtering by pattern.
    """
    
    MAX_MATCHES = 100
    MAX_DISPLAY = 50
    
    @property
    def name(self) -> str:
        return "grep"
    
    @property
    def description(self) -> str:
        return "Search for patterns in files using regex"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for"
                },
                "path": {
                    "type": "string",
                    "description": "Directory or file to search in"
                },
                "include": {
                    "type": "string",
                    "description": "Only search in files matching this pattern (e.g., '*.py')"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Case sensitive search",
                    "default": True
                }
            },
            "required": ["pattern"]
        }
    
    def is_read_only(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the grep tool.
        
        Args:
            input_data: Dictionary containing pattern, path, include, and case_sensitive
            context: Tool execution context with working directory
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with matching lines or error message
            
        Raises:
            re.error: If the provided regex pattern is invalid
        """
        pattern = input_data.get("pattern", "")
        path = input_data.get("path") or context.working_directory
        include = input_data.get("include")
        case_sensitive = input_data.get("case_sensitive", True)
        
        if not pattern:
            return ToolResult(content="Error: pattern is required", is_error=True)
        
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(pattern, flags)
        except re.error as e:
            return ToolResult(content=f"Invalid regex: {e}", is_error=True)
        
        if not os.path.isabs(path):
            path = os.path.join(context.working_directory, path)
        
        matches: list[str] = []
        files_searched = 0
        
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ('node_modules', '__pycache__')]
            
            for file in files:
                if include and not file.endswith(include.replace('*', '')):
                    continue
                
                files_searched += 1
                file_path = os.path.join(root, file)
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                        for line_num, line in enumerate(f, 1):
                            if regex.search(line):
                                rel_path = os.path.relpath(file_path, path)
                                matches.append(f"{rel_path}:{line_num}: {line.rstrip()}")
                                
                                if len(matches) >= self.MAX_MATCHES:
                                    break
                except OSError:
                    pass
                
                if len(matches) >= self.MAX_MATCHES:
                    break
            else:
                continue
            break
        
        if not matches:
            return ToolResult(content=f"No matches found in {files_searched} files")
        
        lines = [f"Found {len(matches)} matches:", ""]
        lines.extend(matches[:self.MAX_DISPLAY])
        
        if len(matches) > self.MAX_DISPLAY:
            lines.append(f"\n... and {len(matches) - self.MAX_DISPLAY} more matches")
        
        return ToolResult(content="\n".join(lines))
