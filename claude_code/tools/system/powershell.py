"""
Claude Code Python - PowerShell Tool
Execute PowerShell commands on Windows.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Proper exception handling
"""

from __future__ import annotations

import subprocess
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class PowerShellTool(Tool):
    """Tool to execute PowerShell commands on Windows.
    
    Executes PowerShell commands and returns stdout/stderr output.
    Only available on Windows systems.
    """
    
    DEFAULT_TIMEOUT: int = 60
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "powershell"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Execute a PowerShell command on Windows"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "PowerShell command to execute"
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds",
                    "default": 60
                }
            },
            "required": ["command"]
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the PowerShell command.
        
        Args:
            input_data: Dictionary containing command and timeout
            context: Tool execution context with working directory
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with command output or error message
        """
        command = input_data.get("command", "")
        timeout = input_data.get("timeout", self.DEFAULT_TIMEOUT)
        
        if not command:
            return ToolResult(content="Error: command is required", is_error=True)
        
        try:
            result = subprocess.run(
                ["powershell", "-Command", command],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=context.working_directory
            )
            
            output_parts: list[str] = []
            if result.stdout:
                output_parts.append(result.stdout)
            if result.stderr:
                output_parts.append(f"[stderr] {result.stderr}")
            
            content = "\n".join(output_parts) if output_parts else "(no output)"
            return ToolResult(content=content)
            
        except subprocess.TimeoutExpired:
            return ToolResult(content=f"Command timed out after {timeout} seconds", is_error=True)
        except OSError as e:
            return ToolResult(content=f"Error: {e}", is_error=True)
