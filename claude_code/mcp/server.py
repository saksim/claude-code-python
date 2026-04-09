"""
Claude Code Python - MCP Server
Server-side implementation of the Model Context Protocol.
Fully integrated with the existing tool system.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- pathlib.Path for file operations
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field


# Module-level constants
DEFAULT_SERVER_VERSION: str = "1.0.0"
PROTOCOL_VERSION: str = "2024-11-05"


@dataclass(frozen=True, slots=True)
class MCPServerConfig:
    """Configuration for MCP server.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        name: Server name
        version: Server version
        working_directory: Working directory for tool execution
    """
    name: str
    version: str = DEFAULT_SERVER_VERSION
    working_directory: str = "."


class MCPProtocolHandler:
    """Handles MCP JSON-RPC protocol.
    
    Manages request/response handling, notification processing,
    and pending request tracking.
    
    Attributes:
        _request_handlers: Dictionary of method handlers
        _notification_handlers: Dictionary of notification handlers
        _pending_requests: Dictionary of pending request futures
        _request_id: Counter for request IDs
    """
    
    def __init__(self) -> None:
        """Initialize protocol handler."""
        self._request_handlers: dict[str, Any] = {}
        self._notification_handlers: dict[str, Any] = {}
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._request_id = 0
    
    def register_method(self, method: str, handler: Any) -> None:
        """Register a method handler.
        
        Args:
            method: Method name
            handler: Async handler function
        """
        self._request_handlers[method] = handler
        
    def register_notification(self, method: str, handler: Any) -> None:
        """Register a notification handler.
        
        Args:
            method: Notification method name
            handler: Handler function
        """
        self._notification_handlers[method] = handler
    
    async def handle_message(self, message: dict[str, Any]) -> Optional[dict[str, Any]]:
        """Handle incoming JSON-RPC message.
        
        Args:
            message: JSON-RPC message dictionary
            
        Returns:
            Response dictionary or None
        """
        msg_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})
        
        if "result" in message or "error" in message:
            return await self._handle_response(message)
        
        if message.get("method"):
            return await self._handle_request(msg_id, method, params)
        
        return None
    
    async def _handle_request(self, msg_id: Any, method: str, params: dict) -> dict:
        """Handle a JSON-RPC request."""
        handler = self._request_handlers.get(method)
        
        if handler is None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        try:
            result = await handler(params)
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    async def _handle_response(self, message: dict) -> None:
        """Handle a JSON-RPC response."""
        msg_id = str(message.get("id"))
        
        if msg_id in self._pending_requests:
            future = self._pending_requests.pop(msg_id)
            if "error" in message:
                future.set_exception(Exception(message["error"].get("message", "Unknown error")))
            else:
                future.set_result(message.get("result"))
    
    async def send_request(self, method: str, params: Optional[dict] = None) -> Any:
        """Send a request and wait for response."""
        msg_id = str(self._next_id())
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[msg_id] = future
        
        message = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "method": method,
        }
        if params:
            message["params"] = params
        
        return await future
    
    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id


class MCPServer:
    """MCP Server implementation integrated with Claude Code Python tool system.
    
    Provides all registered tools, resources, and prompts to MCP clients.
    This server can be exposed to external MCP clients (Cursor, Cline, Zed, etc.)
    allowing them to use Claude Code Python's tools.
    """
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.protocol = MCPProtocolHandler()
        self._tool_registry = None
        self._initialized = False
        
        self._setup_methods()
    
    def _setup_methods(self) -> None:
        """Setup protocol methods."""
        self.protocol.register_method("initialize", self._handle_initialize)
        self.protocol.register_method("tools/list", self._handle_list_tools)
        self.protocol.register_method("tools/call", self._handle_call_tool)
        self.protocol.register_method("resources/list", self._handle_list_resources)
        self.protocol.register_method("resources/read", self._handle_read_resource)
        self.protocol.register_method("prompts/list", self._handle_list_prompts)
        self.protocol.register_method("prompts/get", self._handle_get_prompt)
        
        self.protocol.register_notification("initialized", lambda p: None)
    
    def set_tool_registry(self, registry: Any) -> None:
        """Set the tool registry to expose tools via MCP.
        
        Args:
            registry: ToolRegistry instance from claude_code.tools
        """
        self._tool_registry = registry
    
    def _convert_input_schema(self, input_schema: dict[str, Any]) -> dict[str, Any]:
        """Convert Claude Code Python input schema to MCP format.
        
        Args:
            input_schema: Original input schema
            
        Returns:
            MCP-compatible input schema
        """
        return input_schema
    
    async def _handle_initialize(self, params: dict) -> dict:
        """Handle initialize request."""
        self._initialized = True
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {
                "tools": {"listChanged": True},
                "resources": {"listChanged": True},
                "prompts": {"listChanged": True},
            },
            "serverInfo": {
                "name": self.config.name,
                "version": self.config.version,
            }
        }
    
    async def _handle_list_tools(self, params: dict) -> dict:
        """Handle tools/list request.
        
        Returns all tools from the tool registry in MCP format.
        """
        if self._tool_registry is None:
            return {"tools": []}
        
        tools = []
        for tool in self._tool_registry.list_all():
            definition = tool.get_definition()
            tools.append({
                "name": definition.name,
                "description": definition.description,
                "inputSchema": self._convert_input_schema(definition.input_schema),
            })
        
        return {"tools": tools}
    
    async def _handle_call_tool(self, params: dict) -> dict:
        """Handle tools/call request.
        
        Executes a tool from the tool registry and returns the result.
        """
        name = params.get("name")
        args = params.get("arguments", {})
        
        if self._tool_registry is None:
            raise ValueError("Tool registry not initialized")
        
        tool = self._tool_registry.get(name)
        if tool is None:
            raise ValueError(f"Tool not found: {name}")
        
        result = await self._execute_tool(tool, args)
        return {"content": [{"type": "text", "text": result.content}]}
    
    async def _execute_tool(self, tool: Any, args: dict[str, Any]) -> Any:
        """Execute a tool with the given arguments.
        
        Args:
            tool: Tool instance from the registry
            args: Tool arguments
            
        Returns:
            ToolResult instance
        """
        from claude_code.tools.base import ToolContext
        
        context = ToolContext(
            working_directory=self.config.working_directory,
            environment={},
        )
        
        result = await tool.execute(args, context)
        return result
    
    async def _handle_list_resources(self, params: dict) -> dict:
        """Handle resources/list request.
        
        Returns static resources for the MCP server.
        Currently returns basic server info as a resource.
        """
        return {
            "resources": [
                {
                    "uri": "server://info",
                    "name": "server_info",
                    "description": "Information about this MCP server",
                    "mimeType": "application/json",
                },
                {
                    "uri": "server://tools",
                    "name": "tools_list",
                    "description": "List of available tools",
                    "mimeType": "application/json",
                },
            ]
        }
    
    async def _handle_read_resource(self, params: dict) -> dict:
        """Handle resources/read request."""
        uri = params.get("uri")
        
        if uri == "server://info":
            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps({
                        "name": self.config.name,
                        "version": self.config.version,
                        "protocolVersion": PROTOCOL_VERSION,
                        "toolCount": len(self._tool_registry.list_all()) if self._tool_registry else 0,
                    }),
                }]
            }
        
        if uri == "server://tools" and self._tool_registry:
            tools_data = []
            for tool in self._tool_registry.list_all():
                definition = tool.get_definition()
                tools_data.append({
                    "name": definition.name,
                    "description": definition.description,
                })
            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps({"tools": tools_data}),
                }]
            }
        
        raise ValueError(f"Resource not found: {uri}")
    
    async def _handle_list_prompts(self, params: dict) -> dict:
        """Handle prompts/list request.
        
        Returns built-in prompts for the MCP server.
        """
        return {
            "prompts": [
                {
                    "name": "tool_list",
                    "description": "Get a formatted list of all available tools",
                },
                {
                    "name": "tool_info",
                    "description": "Get detailed information about a specific tool",
                    "arguments": [
                        {"name": "tool_name", "description": "Name of the tool", "required": True},
                    ],
                },
            ]
        }
    
    async def _handle_get_prompt(self, params: dict) -> dict:
        """Handle prompts/get request."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if name == "tool_list" and self._tool_registry:
            tools = self._tool_registry.list_all()
            tool_list = "\n".join(f"- **{t.name}**: {t.description}" for t in tools)
            return {
                "messages": [{
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"# Available Tools\n\n{tool_list}"
                    }
                }]
            }
        
        if name == "tool_info":
            tool_name = arguments.get("tool_name")
            if self._tool_registry and tool_name:
                tool = self._tool_registry.get(tool_name)
                if tool:
                    definition = tool.get_definition()
                    return {
                        "messages": [{
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": f"# Tool: {definition.name}\n\n**Description:** {definition.description}\n\n**Input Schema:**\n```json\n{json.dumps(definition.input_schema, indent=2)}```"
                            }
                        }]
                    }
        
        raise ValueError(f"Prompt not found: {name}")
    
    async def start_stdio(self) -> None:
        """Start STDIO server - the most common mode for MCP.
        
        This mode is compatible with all MCP clients and allows
        the server to communicate via stdin/stdout JSON-RPC messages.
        """
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        
        loop = asyncio.get_event_loop()
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        while True:
            line = await reader.readline()
            if not line:
                break
            
            try:
                message = json.loads(line.decode("utf-8"))
                response = await self.protocol.handle_message(message)
                if response:
                    print(json.dumps(response), flush=True)
            except json.JSONDecodeError as e:
                error_response = json.dumps({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                })
                print(error_response, flush=True)
            except Exception as e:
                error_response = json.dumps({
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                })
                print(error_response, flush=True)


async def create_mcp_server(
    working_directory: str = ".",
    server_name: str = "claude-code-python",
) -> MCPServer:
    """Create and configure an MCP server with the full tool registry.
    
    This is the main entry point for creating an MCP server that exposes
    all Claude Code Python tools to external MCP clients.
    
    Args:
        working_directory: Working directory for tool execution
        server_name: Name of the MCP server
        
    Returns:
        Configured MCPServer instance ready to start
    """
    from claude_code.tools import create_default_registry
    
    config = MCPServerConfig(
        name=server_name,
        version=DEFAULT_SERVER_VERSION,
        working_directory=working_directory,
    )
    
    server = MCPServer(config)
    
    registry = create_default_registry()
    server.set_tool_registry(registry)
    
    return server


async def run_mcp_server(
    working_directory: str = ".",
    server_name: str = "claude-code-python",
) -> None:
    """Run the MCP server in STDIO mode.
    
    This is the main entry point for running the MCP server as a standalone
    process that can be connected to via MCP clients.
    
    Args:
        working_directory: Working directory for tool execution
        server_name: Name of the MCP server
    """
    server = await create_mcp_server(working_directory, server_name)
    await server.start_stdio()


__all__ = [
    "MCPServer",
    "MCPServerConfig",
    "MCPProtocolHandler",
    "create_mcp_server",
    "run_mcp_server",
]