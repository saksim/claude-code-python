"""
Claude Code Python - Bash Tool
Execute shell commands asynchronously.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Proper error handling
- Async execution using asyncio
"""

import asyncio
import os
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class BashTool(Tool):
    """Tool to execute shell commands asynchronously.
    
    Following Python best practices:
    - Clear property definitions
    - Comprehensive input schema
    - Proper timeout handling
    - Async execution (non-blocking)
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
    def input_schema(self) -> dict:
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
                },
                "shell": {
                    "type": "boolean",
                    "description": "Use shell (default: True)",
                    "default": True
                }
            },
            "required": ["command"]
        }
    
    def is_read_only(self) -> bool:
        """Bash can run any command, not read-only."""
        return False
    
    async def execute(
        self,
        input_data: dict,
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute a shell command asynchronously.
        
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
        use_shell: bool = input_data.get("shell", True)
        
        if not command:
            return ToolResult(
                content="Error: command is required",
                is_error=True
            )
        
        # Use working directory from context if not specified
        if cwd is None:
            cwd = context.working_directory
        
        # Merge environment variables
        env = os.environ.copy()
        env.update(context.environment)
        
        try:
            # Use asyncio subprocess for true async execution
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=env,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return ToolResult(
                    content=f"Command timed out after {timeout} seconds",
                    is_error=True
                )
            
            output_parts = []
            if stdout:
                output_parts.append(stdout.decode("utf-8", errors="replace"))
            if stderr:
                output_parts.append(f"[stderr] {stderr.decode('utf-8', errors='replace')}")
            
            content = "\n".join(output_parts) if output_parts else "(no output)"
            
            # Check for error state
            if process.returncode != 0 and not output_parts:
                return ToolResult(
                    content=f"Command failed with exit code {process.returncode}",
                    is_error=True
                )
            
            return ToolResult(content=content)
            
        except FileNotFoundError:
            return ToolResult(
                content="Error: Command not found",
                is_error=True
            )
        except PermissionError:
            return ToolResult(
                content="Error: Permission denied",
                is_error=True
            )
        except Exception as e:
            return ToolResult(
                content="Error: {}".format(str(e)),
                is_error=True
            )


class PowerShellTool(Tool):
    """Tool to execute PowerShell commands asynchronously."""
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "powershell"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Execute a PowerShell command and return the output"
    
    @property
    def input_schema(self) -> dict:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The PowerShell command to execute"
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
        """PowerShell can run any command, not read-only."""
        return False
    
    async def execute(
        self,
        input_data: dict,
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute a PowerShell command asynchronously.
        
        Args:
            input_data: Dictionary with 'command' and optional 'timeout'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with command output or error.
        """
        command: str = input_data.get("command", "")
        timeout: int = input_data.get("timeout", 60)
        
        if not command:
            return ToolResult(
                content="Error: command is required",
                is_error=True
            )
        
        # PowerShell command prefix
        ps_command = "powershell -NoProfile -ExecutionPolicy Bypass -Command \"{}\"".format(
            command.replace("\"", "\\\"")
        )
        
        # Use BashTool to execute
        bash_tool = BashTool()
        result = await bash_tool.execute(
            {"command": ps_command, "timeout": timeout},
            context,
            on_progress
        )
        
        return result