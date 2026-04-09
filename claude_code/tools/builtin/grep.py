"""
Claude Code Python - Grep Tool
Search for patterns in files.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional
from functools import lru_cache

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


@lru_cache(maxsize=64)
def _compile_pattern(pattern: str, flags: int) -> re.Pattern:
    """Cache compiled regex patterns to avoid recompilation.
    
    Args:
        pattern: Regex pattern string
        flags: Regex flags
        
    Returns:
        Compiled regex Pattern object
    """
    return re.compile(pattern, flags)


class GrepTool(Tool):
    """Tool to search for patterns in files.
    
    This tool performs regex-based search across files in a directory.
    It supports case sensitivity control and file filtering by pattern.
    Uses cached regex compilation for repeated pattern searches.
    """
    
    MAX_MATCHES = 100
    MAX_DISPLAY = 50
    MAX_FILE_SIZE = 10 * 1024 * 1024  # Skip files larger than 10MB
    
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
            regex = _compile_pattern(pattern, flags)
        except re.error as e:
            return ToolResult(content=f"Invalid regex: {e}", is_error=True)
        
        if not os.path.isabs(path):
            path = os.path.join(context.working_directory, path)
        
        matches: list[str] = []
        files_searched = 0
        
        _SKIP_DIRS = frozenset({'.git', 'node_modules', '__pycache__', '.svn', '.hg', 'vendor', 'venv', '.venv', 'dist', 'build'})
        
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in _SKIP_DIRS and not d.startswith('.')]
            
            for file in files:
                if include and not file.endswith(include.replace('*', '')):
                    continue
                
                files_searched += 1
                file_path = os.path.join(root, file)
                
                # Skip files that are too large
                try:
                    if os.path.getsize(file_path) > self.MAX_FILE_SIZE:
                        continue
                except OSError:
                    continue
                
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
