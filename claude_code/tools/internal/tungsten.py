"""
Claude Code Python - Tungsten Tool
Ant-specific internal tool placeholder.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class TungstenTool(Tool):
    """Tungsten internal tool placeholder.
    
    This is an ant-only internal tool for Anthropic-specific functionality.
    Not available in open source version.
    
    Attributes:
        name: tungsten
        description: Internal ant-only tool (not available)
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "tungsten"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Internal ant-only tool (not available in open source)"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema (no public parameters).
        """
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    
    def is_enabled(self) -> bool:
        """Check if tool is enabled.
        
        Returns:
            False - this tool is ant-only
        """
        return False
    
    def is_read_only(self) -> bool:
        """Tool is not available.
        
        Returns:
            True
        """
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute returns not available message.
        
        Args:
            input_data: Ignored
            context: Tool execution context
            on_progress: Optional progress callback
            
        Returns:
            ToolResult with not available message
        """
        return ToolResult(
            content="TungstenTool is an internal ant-only tool and is not available in the open source version.",
            is_error=True
        )


def clear_sessions_with_tungsten_usage() -> None:
    """Clear sessions that used tungsten tool (placeholder)."""
    pass


def reset_initialization_state() -> None:
    """Reset tungsten initialization state (placeholder)."""
    pass


__all__ = ["TungstenTool", "clear_sessions_with_tungsten_usage", "reset_initialization_state"]