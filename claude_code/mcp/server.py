"""
Claude Code Python - MCP Server
Server-side implementation of the Model Context Protocol.

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
from typing import Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


# Module-level constants
DEFAULT_SERVER_VERSION: str = "1.0.0"
DEFAULT_PORT: int = 8080
DEFAULT_HOST: str = "127.0.0.1"
PROTOCOL_VERSION: str = "2024-11-05"


class MCPTransport(Enum):
    """MCP transport types.
    
    Attributes:
        STDIO: Standard input/output transport
        SSE: Server-Sent Events transport
        WEBSOCKET: WebSocket transport
    """
    STDIO = "stdio"
    SSE = "sse"
    WEBSOCKET = "websocket"


@dataclass(frozen=True, slots=True)
class MCPServerConfig:
    """Configuration for MCP server.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        name: Server name
        version: Server version
        transport: Transport type
        port: Port number for network transports
        host: Host address for network transports
    """
    name: str
    version: str = DEFAULT_SERVER_VERSION
    transport: MCPTransport = MCPTransport.STDIO
    port: int = DEFAULT_PORT
    host: str = DEFAULT_HOST


@dataclass(frozen=True, slots=True)
class MCPToolDefinition:
    """Tool definition for MCP server.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        name: Tool name
        description: Tool description
        input_schema: JSON schema for tool input
    """
    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class MCPResourceDefinition:
    """Resource definition for MCP server.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        uri: Resource URI
        name: Resource name
        description: Resource description
        mime_type: MIME type of the resource
    """
    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"


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
        self._request_handlers: dict[str, Callable] = {}
        self._notification_handlers: dict[str, Callable] = {}
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._request_id = 0
    
    def register_method(self, method: str, handler: Callable) -> None:
        """Register a method handler.
        
        Args:
            method: Method name
            handler: Async handler function
        """
        self._request_handlers[method] = handler
        
    def register_notification(self, method: str, handler: Callable) -> None:
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
    """
    MCP Server implementation.
    
    Provides tools, resources, and prompts to MCP clients.
    """
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.protocol = MCPProtocolHandler()
        self._tools: dict[str, MCPToolDefinition] = {}
        self._resources: dict[str, MCPResourceDefinition] = {}
        self._prompts: dict[str, dict] = {}
        self._server = None
        
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
    
    def add_tool(self, tool: MCPToolDefinition) -> None:
        """Add a tool to the server."""
        self._tools[tool.name] = tool
    
    def add_resource(self, resource: MCPResourceDefinition) -> None:
        """Add a resource to the server."""
        self._resources[resource.uri] = resource
    
    def add_prompt(self, name: str, description: str, template: str) -> None:
        """Add a prompt to the server."""
        self._prompts[name] = {
            "description": description,
            "template": template,
        }
    
    async def _handle_initialize(self, params: dict) -> dict:
        """Handle initialize request."""
        return {
            "protocolVersion": "2024-11-05",
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
        """Handle tools/list request."""
        return {
            "tools": [
                {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": t.input_schema,
                }
                for t in self._tools.values()
            ]
        }
    
    async def _handle_call_tool(self, params: dict) -> dict:
        """Handle tools/call request."""
        name = params.get("name")
        args = params.get("arguments", {})
        
        tool = self._tools.get(name)
        if tool is None:
            raise ValueError(f"Tool not found: {name}")
        
        result = await self._execute_tool(name, args)
        return {"content": [{"type": "text", "text": result}]}
    
    async def _execute_tool(self, name: str, args: dict) -> str:
        """Execute a tool (override in subclass)."""
        return f"Tool {name} executed with args: {args}"
    
    async def _handle_list_resources(self, params: dict) -> dict:
        """Handle resources/list request."""
        return {
            "resources": [
                {
                    "uri": r.uri,
                    "name": r.name,
                    "description": r.description,
                    "mimeType": r.mime_type,
                }
                for r in self._resources.values()
            ]
        }
    
    async def _handle_read_resource(self, params: dict) -> dict:
        """Handle resources/read request."""
        uri = params.get("uri")
        
        resource = self._resources.get(uri)
        if resource is None:
            raise ValueError(f"Resource not found: {uri}")
        
        return {
            "contents": [{
                "uri": uri,
                "mimeType": resource.mime_type,
                "text": f"Content of {uri}",
            }]
        }
    
    async def _handle_list_prompts(self, params: dict) -> dict:
        """Handle prompts/list request."""
        return {
            "prompts": [
                {
                    "name": name,
                    "description": p["description"],
                }
                for name, p in self._prompts.items()
            ]
        }
    
    async def _handle_get_prompt(self, params: dict) -> dict:
        """Handle prompts/get request."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        prompt = self._prompts.get(name)
        if prompt is None:
            raise ValueError(f"Prompt not found: {name}")
        
        template = prompt["template"]
        for key, value in arguments.items():
            template = template.replace(f"{{{key}}}", str(value))
        
        return {
            "messages": [{
                "role": "user",
                "content": {"type": "text", "text": template}
            }]
        }
    
    async def start_stdio(self) -> None:
        """Start STDIO server."""
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        
        loop = asyncio.get_event_loop()
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        while True:
            line = await reader.readline()
            if not line:
                break
            
            try:
                message = json.loads(line)
                response = await self.protocol.handle_message(message)
                if response:
                    print(json.dumps(response))
            except Exception as e:
                print(json.dumps({"error": str(e)}))
    
    async def start_http(self) -> None:
        """Start HTTP server."""
        from aiohttp import web
        
        async def handle(request):
            data = await request.json()
            response = await self.protocol.handle_message(data)
            return web.json_response(response)
        
        app = web.Application()
        app.router.add_post("/mcp", handle)
        
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.config.host, self.config.port)
        await site.start()
        
        print(f"MCP Server started on {self.config.host}:{self.config.port}")


class FileSystemMCPServer(MCPServer):
    """MCP server for file system operations.
    
    Provides tools for reading files and listing directories.
    
    Attributes:
        root_dir: Root directory for file operations
    """
    
    def __init__(self, root_dir: str = "/"):
        super().__init__(MCPServerConfig(
            name="filesystem",
            version=DEFAULT_SERVER_VERSION,
        ))
        self._root_dir = Path(root_dir)
        
        self.add_tool(MCPToolDefinition(
            name="read_file",
            description="Read a file",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        ))
        
        self.add_tool(MCPToolDefinition(
            name="list_directory",
            description="List directory contents",
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        ))
    
    @property
    def root_dir(self) -> Path:
        """Get the root directory for file operations."""
        return self._root_dir
    
    async def _execute_tool(self, name: str, args: dict[str, Any]) -> str:
        """Execute a file system tool.
        
        Args:
            name: Tool name
            args: Tool arguments
            
        Returns:
            Tool execution result
        """
        if name == "read_file":
            file_path = self._root_dir / args["path"]
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except FileNotFoundError:
                return f"Error: File not found: {args['path']}"
            except PermissionError:
                return f"Error: Permission denied: {args['path']}"
            except Exception as e:
                return f"Error: {str(e)}"
        
        if name == "list_directory":
            dir_path = self._root_dir / args["path"]
            try:
                return "\n".join(sorted(p.name for p in dir_path.iterdir()))
            except FileNotFoundError:
                return f"Error: Directory not found: {args['path']}"
            except PermissionError:
                return f"Error: Permission denied: {args['path']}"
            except Exception as e:
                return f"Error: {str(e)}"
        
        return await super()._execute_tool(name, args)


__all__ = [
    "MCPServer",
    "MCPServerConfig",
    "MCPToolDefinition",
    "MCPResourceDefinition",
    "MCPProtocolHandler",
    "FileSystemMCPServer",
]
