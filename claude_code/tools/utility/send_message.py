"""
Claude Code Python - Send Message Tool
Send a message to the user.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any, Optional

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class SendMessageTool(Tool):
    """Tool to send a message to the user (display only).
    
    Formats and displays a message to the user with optional type styling.
    """
    
    DEFAULT_TYPE = "info"
    
    @property
    def name(self) -> str:
        return "send_message"
    
    @property
    def description(self) -> str:
        return "Send a message to the user"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to send to the user"
                },
                "type": {
                    "type": "string",
                    "enum": ["info", "warning", "error", "success"],
                    "description": "Message type",
                    "default": "info"
                }
            },
            "required": ["message"]
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the send message tool.
        
        Args:
            input_data: Dictionary containing message and type
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with formatted message
        """
        message = input_data.get("message", "")
        msg_type = input_data.get("type", self.DEFAULT_TYPE)
        
        return ToolResult(content=f"[{msg_type.upper()}] {message}")
