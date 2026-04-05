"""
Claude Code Python - MCP Tools
Tools for interacting with MCP servers.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Proper error handling
"""

from __future__ import annotations

import json
from typing import Any, Optional

from claude_code.tools.base import Tool, ToolCallback, ToolContext, ToolResult


class MCPTool(Tool):
    """Tool to call MCP server tools.
    
    Executes tools provided by MCP (Model Context Protocol) servers.
    Allows Claude Code to integrate with external MCP-based services.
    """
    
    def __init__(self, tool_name: str = "", server_name: str = "") -> None:
        """Initialize MCP tool.
        
        Args:
            tool_name: Name of the MCP tool to call
            server_name: Name of the MCP server
        """
        super().__init__()
        self._tool_name = tool_name
        self._server_name = server_name
    
    @property
    def name(self) -> str:
        return f"mcp_{self._server_name}_{self._tool_name}" if self._server_name else "mcp"
    
    @property
    def description(self) -> str:
        return f"Execute an MCP tool from server '{self._server_name}'"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "server": {
                    "type": "string",
                    "description": "MCP server name"
                },
                "tool": {
                    "type": "string",
                    "description": "MCP tool name to call"
                },
                "arguments": {
                    "type": "object",
                    "description": "Arguments to pass to the MCP tool"
                }
            },
            "required": ["server", "tool"]
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the MCP tool.
        
        Args:
            input_data: Dictionary containing server, tool, and arguments
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with tool output or error message
        """
        server_name = input_data.get("server", self._server_name)
        tool_name = input_data.get("tool", self._tool_name)
        arguments = input_data.get("arguments", {})
        
        if not server_name or not tool_name:
            return ToolResult(
                content="Error: server and tool are required",
                is_error=True
            )
        
        try:
            from claude_code.services.mcp import get_mcp_manager
            
            mcp_manager = get_mcp_manager()
            if mcp_manager is None:
                return ToolResult(
                    content="Error: MCP manager not initialized",
                    is_error=True
                )
            
            client = mcp_manager.get_client(server_name)
            if client is None:
                return ToolResult(
                    content=f"Error: MCP server '{server_name}' not found",
                    is_error=True
                )
            
            result = await client.call_tool(tool_name, arguments)
            
            if isinstance(result, str):
                return ToolResult(content=result)
            return ToolResult(content=json.dumps(result, indent=2))
                
        except Exception as e:
            return ToolResult(
                content=f"Error calling MCP tool: {e}",
                is_error=True
            )


class ListMcpResourcesTool(Tool):
    """Tool to list MCP resources.
    
    Lists all available resources from connected MCP servers.
    Resources are data sources that MCP servers expose for reading.
    """
    
    @property
    def name(self) -> str:
        return "list_mcp_resources"
    
    @property
    def description(self) -> str:
        return "List available MCP resources from connected servers"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "server": {
                    "type": "string",
                    "description": "Optional server name to filter by"
                }
            },
            "required": []
        }
    
    def is_read_only(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the list MCP resources tool.
        
        Args:
            input_data: Dictionary with optional server filter
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with resource list or error message
        """
        server_filter = input_data.get("server")
        
        try:
            from claude_code.services.mcp import get_mcp_manager
            
            mcp_manager = get_mcp_manager()
            if mcp_manager is None:
                return ToolResult(content="No MCP servers connected")
            
            resources = await mcp_manager.list_resources(server_filter)
            
            if not resources:
                return ToolResult(content="No MCP resources available")
            
            lines: list[str] = ["# MCP Resources\n"]
            for resource in resources:
                lines.append(f"- {resource.uri}")
                lines.append(f"  Name: {resource.name}")
                if resource.description:
                    lines.append(f"  Description: {resource.description}")
                lines.append("")
            
            return ToolResult(content="\n".join(lines))
            
        except Exception as e:
            return ToolResult(
                content=f"Error listing MCP resources: {e}",
                is_error=True
            )


class ReadMcpResourceTool(Tool):
    """Tool to read an MCP resource.
    
    Reads content from a specific MCP resource by URI.
    """
    
    @property
    def name(self) -> str:
        return "read_mcp_resource"
    
    @property
    def description(self) -> str:
        return "Read content from an MCP resource"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": "URI of the resource to read"
                }
            },
            "required": ["uri"]
        }
    
    def is_read_only(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the read MCP resource tool.
        
        Args:
            input_data: Dictionary containing uri
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with resource content or error message
        """
        uri = input_data.get("uri", "")
        
        if not uri:
            return ToolResult(
                content="Error: uri is required",
                is_error=True
            )
        
        try:
            from claude_code.services.mcp import get_mcp_manager
            
            mcp_manager = get_mcp_manager()
            if mcp_manager is None:
                return ToolResult(
                    content="Error: MCP manager not initialized",
                    is_error=True
                )
            
            result = await mcp_manager.read_resource(uri)
            
            if result is None:
                return ToolResult(
                    content=f"Resource not found: {uri}",
                    is_error=True
                )
            
            content = result.get("contents", "")
            if isinstance(content, list):
                content = "\n".join(c.get("text", "") for c in content)
            
            return ToolResult(content=content)
            
        except Exception as e:
            return ToolResult(
                content=f"Error reading MCP resource: {e}",
                is_error=True
            )


class McpAuthTool(Tool):
    """Tool to authenticate with MCP servers.
    
    Provides authentication configuration for MCP servers.
    Supports OAuth and API key authentication.
    """
    
    @property
    def name(self) -> str:
        return "mcp_auth"
    
    @property
    def description(self) -> str:
        return "Authenticate with an MCP server"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "server": {
                    "type": "string",
                    "description": "Server name"
                },
                "auth_type": {
                    "type": "string",
                    "description": "Authentication type (oauth, api_key, none)",
                    "enum": ["oauth", "api_key", "none"]
                },
                "credentials": {
                    "type": "object",
                    "description": "Authentication credentials"
                }
            },
            "required": ["server", "auth_type"]
        }
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the MCP auth tool.
        
        Args:
            input_data: Dictionary containing server, auth_type, credentials
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with success or error message
        """
        server = input_data.get("server", "")
        auth_type = input_data.get("auth_type", "none")
        credentials = input_data.get("credentials", {})
        
        if not server:
            return ToolResult(
                content="Error: server is required",
                is_error=True
            )
        
        try:
            from claude_code.services.mcp import get_mcp_manager
            
            mcp_manager = get_mcp_manager()
            if mcp_manager is None:
                return ToolResult(
                    content="Error: MCP manager not initialized",
                    is_error=True
                )
            
            await mcp_manager.authenticate(server, auth_type, credentials)
            
            return ToolResult(content=f"Successfully authenticated with {server}")
            
        except Exception as e:
            return ToolResult(
                content=f"Error authenticating: {e}",
                is_error=True
            )


def create_mcp_tool(tool_name: str, server_name: str) -> MCPTool:
    """Factory function to create an MCP tool for a specific server/tool.
    
    Args:
        tool_name: Name of the MCP tool
        server_name: Name of the MCP server
        
    Returns:
        MCPTool instance configured for the specific tool/server
    """
    return MCPTool(tool_name=tool_name, server_name=server_name)


class ListMcpToolsTool(Tool):
    """Tool to list MCP tools from servers.
    
    Lists all available tools from connected MCP servers.
    """
    
    @property
    def name(self) -> str:
        return "list_mcp_tools"
    
    @property
    def description(self) -> str:
        return "List available tools from MCP servers"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "server": {
                    "type": "string",
                    "description": "Optional server name to filter by"
                }
            },
            "required": []
        }
    
    def is_read_only(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the list MCP tools tool.
        
        Args:
            input_data: Dictionary with optional server filter
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with tools list or error message
        """
        server_filter = input_data.get("server")
        
        try:
            from claude_code.services.mcp import get_mcp_manager
            
            mcp_manager = get_mcp_manager()
            if mcp_manager is None:
                return ToolResult(content="No MCP servers connected")
            
            if server_filter:
                client = mcp_manager.get_client(server_filter)
                tools = client.tools if client else []
            else:
                tools = mcp_manager.get_all_tools()
            
            if not tools:
                return ToolResult(content="No MCP tools available")
            
            lines: list[str] = ["# MCP Tools\n"]
            for tool in tools:
                lines.append(f"\n## {tool.name}")
                lines.append(f"Server: {tool.server_name}")
                lines.append(f"Description: {tool.description}")
            
            return ToolResult(content="\n".join(lines))
            
        except Exception as e:
            return ToolResult(content=f"Error: {e}", is_error=True)


class ListMcpPromptsTool(Tool):
    """Tool to list MCP prompts.
    
    Lists available prompts from MCP servers.
    """
    
    @property
    def name(self) -> str:
        return "list_mcp_prompts"
    
    @property
    def description(self) -> str:
        return "List available prompts from MCP servers"
    
    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "server": {
                    "type": "string",
                    "description": "Optional server name to filter by"
                }
            },
            "required": []
        }
    
    def is_read_only(self) -> bool:
        return True
    
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the list MCP prompts tool.
        
        Args:
            input_data: Dictionary with optional server filter
            context: Tool execution context
            on_progress: Optional callback for progress updates
            
        Returns:
            ToolResult with prompts list or error message
        """
        server_filter = input_data.get("server")
        
        try:
            from claude_code.services.mcp import get_mcp_manager
            
            mcp_manager = get_mcp_manager()
            if mcp_manager is None:
                return ToolResult(content="No MCP servers connected")
            
            lines: list[str] = ["# MCP Prompts\n"]
            
            for name, client in mcp_manager._clients.items():
                if server_filter and name != server_filter:
                    continue
                lines.append(f"\n## Server: {name}")
                lines.append("(No prompts available - MCP prompt support limited)")
            
            return ToolResult(content="\n".join(lines))
            
        except Exception as e:
            return ToolResult(content=f"Error: {e}", is_error=True)


__all__ = [
    "MCPTool",
    "ListMcpResourcesTool",
    "ReadMcpResourceTool",
    "McpAuthTool",
    "ListMcpToolsTool",
    "ListMcpPromptsTool",
    "create_mcp_tool",
]
