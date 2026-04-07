"""
Claude Code Python - Context Inspection Tool
Feature-gated tool for context inspection (CONTEXT_COLLAPSE).

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class CtxInspectTool(Tool):
    """Context inspection tool for debugging context usage.
    
    This tool provides visibility into context collapse state.
    Feature-gated under CONTEXT_COLLAPSE.
    
    Attributes:
        name: ctx_inspect
        description: Inspect context state and collapse info
    """
    
    @property
    def name(self) -> str:
        return "ctx_inspect"
    
    @property
    def description(self) -> str:
        return "Inspect context state, collapse info, and token usage"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "show_tokens": {"type": "boolean", "description": "Show token breakdown"},
                "show_messages": {"type": "boolean", "description": "Show message list"},
                "show_collapse": {"type": "boolean", "description": "Show collapse state"}
            }
        }
    
    def is_enabled(self) -> bool:
        import os
        return os.environ.get("CONTEXT_COLLAPSE", "0") == "1"
    
    def is_read_only(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        if not self.is_enabled():
            return ToolResult(content="CtxInspectTool is disabled", is_error=True)
        
        return ToolResult(content="Context inspection placeholder")


__all__ = ["CtxInspectTool"]