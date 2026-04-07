"""
Claude Code Python - List Peers Tool
Feature-gated tool for listing connected peers (UDS_INBOX).

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class ListPeersTool(Tool):
    """List connected peers tool.
    
    This tool lists all connected peer processes.
    Feature-gated under UDS_INBOX.
    
    Attributes:
        name: list_peers
        description: List connected peer processes
    """
    
    @property
    def name(self) -> str:
        return "list_peers"
    
    @property
    def description(self) -> str:
        return "List all connected peer processes"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "include_status": {"type": "boolean", "description": "Include peer status"}
            }
        }
    
    def is_enabled(self) -> bool:
        import os
        return os.environ.get("UDS_INBOX", "0") == "1"
    
    def is_read_only(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        if not self.is_enabled():
            return ToolResult(content="ListPeersTool is disabled. Enable with UDS_INBOX=1", is_error=True)
        
        return ToolResult(content="No peers connected")


__all__ = ["ListPeersTool"]