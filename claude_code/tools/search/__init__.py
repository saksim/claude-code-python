"""
Claude Code Python - Tool Search and Remote Trigger Tools
Tools for searching available tools and triggering remote sessions.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- pathlib.Path for file operations
"""

from __future__ import annotations

import re
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolContext, ToolResult, ToolCallback


class ToolSearchTool(Tool):
    """Search for registered tools by name or description.
    
    This tool allows users to discover and search through all available
    tools in the tool registry. It performs case-insensitive matching
    against tool names and descriptions.
    
    Attributes:
        name: tool_search
        description: Search for available tools
    
    Example:
        >>> # Search for file-related tools
        >>> result = await tool.execute(
        ...     {"query": "file", "limit": 5},
        ...     context,
        ... )
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "tool_search"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Search for available tools"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to match against tool names and descriptions"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10
                }
            },
            "required": ["query"]
        }
    
    def is_read_only(self) -> bool:
        """Tool only reads data, never modifies.
        
        Returns:
            True since tool search is a read-only operation.
        """
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the tool search.
        
        Args:
            input_data: Dictionary with 'query' and optional 'limit'.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with search results formatted as markdown.
        """
        query = input_data.get("query", "").lower()
        limit = input_data.get("limit", 10)
        
        if not query:
            return ToolResult(content="Error: query is required", is_error=True)
        
        from claude_code.tools.registry import create_default_registry
        
        registry = create_default_registry()
        
        all_tools = registry.list_all()
        
        matches: list[dict[str, str]] = []
        for tool in all_tools:
            name = tool.name.lower()
            desc = tool.description.lower()
            
            if query in name or query in desc:
                matches.append({
                    "name": tool.name,
                    "description": tool.description,
                })
        
        if not matches:
            return ToolResult(content=f"No tools found matching: {query}")
        
        lines: list[str] = [f"# Tool Search: {query}\n"]
        
        for m in matches[:limit]:
            lines.append(f"\n## {m['name']}")
            lines.append(f"{m['description']}")
        
        return ToolResult(content="\n".join(lines))


class RemoteTriggerTool(Tool):
    """Trigger remote Claude Code sessions.
    
    This tool provides functionality to manage remote Claude Code sessions
    via the CCR (Claude Code Remote) API. Currently provides a stub 
    implementation that indicates CCR API configuration is required.
    
    Supported actions:
        - list: List all active remote sessions
        - create: Create a new remote session
        - run: Execute a prompt on a remote session
        - stop: Stop an active remote session
        - status: Get status of a specific session
    
    Attributes:
        name: remote_trigger
        description: Trigger remote Claude Code session
    """
    
    @property
    def name(self) -> str:
        """Tool name identifier."""
        return "remote_trigger"
    
    @property
    def description(self) -> str:
        """Human-readable description of the tool."""
        return "Trigger remote Claude Code session"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema defining the input parameters.
        """
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "create", "run", "stop", "status"],
                    "description": "Action to perform on remote session"
                },
                "session_id": {
                    "type": "string",
                    "description": "ID of the session to operate on"
                },
                "prompt": {
                    "type": "string",
                    "description": "Prompt to execute (for 'run' action)"
                },
                "config": {
                    "type": "object",
                    "description": "Configuration for session creation"
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
        """Execute remote trigger action.
        
        Args:
            input_data: Dictionary with 'action' and action-specific parameters.
            context: Tool execution context.
            on_progress: Optional progress callback.
            
        Returns:
            ToolResult with action result or error message.
        """
        action = input_data.get("action", "")
        
        if action == "list":
            return ToolResult(content="""# Remote Sessions

No active remote sessions.

This feature requires claude.ai CCR API configuration.""")
        
        elif action == "create":
            return ToolResult(content="""# Create Remote Session

Remote session creation requires:
- CCR API credentials
- Network connectivity to claude.ai

This is an Enterprise feature.""")
        
        elif action == "run":
            prompt = input_data.get("prompt", "")
            if not prompt:
                return ToolResult(content="Error: prompt is required", is_error=True)
            
            return ToolResult(content="Remote execution requires CCR API configuration")
        
        elif action == "stop":
            session_id = input_data.get("session_id", "")
            if not session_id:
                return ToolResult(content="Error: session_id is required", is_error=True)
            
            return ToolResult(content=f"Stopped remote session: {session_id}")
        
        elif action == "status":
            session_id = input_data.get("session_id", "")
            
            if session_id:
                return ToolResult(content=f"Session {session_id}: Unknown (CCR API not configured)")
            
            return ToolResult(content="No remote sessions active")
        
        return ToolResult(content=f"Unknown action: {action}", is_error=True)


__all__ = ["ToolSearchTool", "RemoteTriggerTool"]
