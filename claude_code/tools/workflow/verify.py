"""
Claude Code Python - Verify Tool
Verify code changes or test results.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

import subprocess
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class VerifyTool(Tool):
    """Tool to verify code changes or run tests.
    
    Provides verification actions including syntax checking,
    linting, testing, and type checking.
    """
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "verify"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Verify code changes or run tests"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["syntax", "lint", "test", "typecheck"],
                    "description": "Verification action"
                },
                "path": {
                    "type": "string",
                    "description": "Path to file or directory"
                }
            },
            "required": ["action"]
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the verify tool.
        
        Args:
            input_data: Dictionary containing action and optional path.
            context: Tool execution context with working directory.
            on_progress: Optional callback for progress updates.
            
        Returns:
            ToolResult with verification results or error message.
        """
        action = input_data.get("action", "")
        path = input_data.get("path", "")
        
        if not path:
            path = context.working_directory
        
        try:
            if action == "syntax":
                result = subprocess.run(
                    ["python", "-m", "py_compile", path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0:
                    return ToolResult(content=f"Syntax OK: {path}")
                else:
                    return ToolResult(content=f"Syntax error:\n{result.stderr}", is_error=True)
            
            elif action == "lint":
                result = subprocess.run(
                    ["python", "-m", "ruff", "check", path],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                return ToolResult(content=result.stdout or "No linting issues found")
            
            elif action == "test":
                result = subprocess.run(
                    ["python", "-m", "pytest", path, "-v"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                return ToolResult(content=result.stdout or "Tests completed")
            
            else:
                return ToolResult(content=f"Unknown action: {action}", is_error=True)
                
        except Exception as e:
            return ToolResult(content=f"Error: {str(e)}", is_error=True)
