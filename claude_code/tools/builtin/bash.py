"""
Claude Code Python - Bash Tool
Execute shell commands.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Proper error handling
- Timeout support
"""

from __future__ import annotations

import os
import subprocess
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class BashTool(Tool):
    """
    Tool to execute shell commands.
    
    Following Python best practices:
    - Clear property definitions
    - Comprehensive input schema
    - Proper timeout handling
    - Error state tracking
    """
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "bash"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Execute a shell command and return the output"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to execute"
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds",
                    "default": 60
                },
                "working_directory": {
                    "type": "string",
                    "description": "Directory to run command in"
                }
            },
            "required": ["command"]
        }
    
    def is_read_only(self) -> bool:
        """Bash can run any command, not read-only."""
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute a shell command.
        
        Args:
            input_data: Dictionary with 'command' and optional 'timeout', 'working_directory'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with command output or error.
        """
        command: str = input_data.get("command", "")
        timeout: int = input_data.get("timeout", 60)
        cwd: Optional[str] = input_data.get("working_directory")
        
        if not command:
            return ToolResult(
                content="Error: command is required",
                is_error=True
            )
        
        # Use working directory from context if not specified
        if cwd is None:
            cwd = context.working_directory
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd,
                env={**os.environ, **context.environment}
            )
            
            output_parts: list[str] = []
            if result.stdout:
                output_parts.append(result.stdout)
            if result.stderr:
                output_parts.append(f"[stderr] {result.stderr}")
            
            content = "\n".join(output_parts) if output_parts else "(no output)"
            
            # Check for error state
            if result.returncode != 0 and not output_parts:
                return ToolResult(
                    content=f"Command failed with exit code {result.returncode}",
                    is_error=True
                )
            
            return ToolResult(content=content)
            
        except subprocess.TimeoutExpired:
            return ToolResult(
                content=f"Command timed out after {timeout} seconds",
                is_error=True
            )
        except Exception as e:
            return ToolResult(
                content=f"Error: {str(e)}",
                is_error=True
            )
