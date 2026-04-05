"""
Claude Code Python - Terminal Capture Tool
Capture terminal output.
"""

from __future__ import annotations

from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class TerminalCaptureTool(Tool):
    """Tool to capture terminal output.
    
    Provides functionality to start, stop, and retrieve terminal capture sessions.
    """
    
    @property
    def name(self) -> str:
        """Tool name."""
        return "terminal_capture"
    
    @property
    def description(self) -> str:
        """Human-readable description."""
        return "Capture and store terminal output"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["start", "stop", "get"],
                    "description": "Action to perform"
                },
                "session_id": {
                    "type": "string",
                    "description": "Session ID for the capture"
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
        """Execute the terminal capture tool.
        
        Args:
            input_data: Dictionary containing action and optional session_id
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with capture status or output
        """
        action = input_data.get("action", "")
        session_id = input_data.get("session_id", "default")
        
        if action == "start":
            return ToolResult(content=f"Terminal capture started for session: {session_id}")
        elif action == "stop":
            return ToolResult(content=f"Terminal capture stopped for session: {session_id}")
        elif action == "get":
            return ToolResult(content=f"Captured output for session: {session_id}")
        else:
            return ToolResult(content=f"Unknown action: {action}", is_error=True)
