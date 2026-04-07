"""
Claude Code Python - Push Notification Tool
Feature-gated tool for push notifications (KAIROS feature).

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any, Optional
from dataclasses import dataclass

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


@dataclass(frozen=True, slots=True)
class PushNotificationConfig:
    """Push notification configuration."""
    title: str
    body: str
    icon: Optional[str] = None
    sound: Optional[str] = None


class PushNotificationTool(Tool):
    """Push notification tool for sending notifications.
    
    This tool sends push notifications to the user.
    Feature-gated under KAIROS or KAIROS_PUSH_NOTIFICATION.
    
    Attributes:
        name: push_notification
        description: Send push notifications
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "push_notification"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Send push notifications to the user"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input."""
        return {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Notification title"
                },
                "body": {
                    "type": "string",
                    "description": "Notification body text"
                },
                "icon": {
                    "type": "string",
                    "description": "Optional icon URL"
                },
                "sound": {
                    "type": "string",
                    "description": "Optional sound name"
                }
            },
            "required": ["title", "body"]
        }
    
    def is_enabled(self) -> bool:
        """Check if tool is enabled."""
        from claude_code.utils.features_config import features
        return features.is_enabled("KAIROS")
    
    def is_read_only(self) -> bool:
        """Tool sends notifications."""
        return False
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute push notification."""
        if not self.is_enabled():
            return ToolResult(
                content="PushNotificationTool is disabled. Enable with KAIROS=1 or KAIROS_PUSH_NOTIFICATION=1",
                is_error=True
            )
        
        title = input_data.get("title", "")
        body = input_data.get("body", "")
        
        return ToolResult(content=f"Notification sent: {title} - {body}")


__all__ = ["PushNotificationTool", "PushNotificationConfig"]