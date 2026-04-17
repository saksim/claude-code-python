from __future__ import annotations

import asyncio
import json
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Optional, Callable
from uuid import uuid4
import os
import ssl
import hashlib
import time
from abc import ABC, abstractmethod


class MCPTransportType(Enum):
    """MCP transport types."""
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"
    WEBSOCKET = "websocket"


class MCPAuthType(Enum):
    """MCP authentication types."""
    NONE = "none"
    API_KEY = "api_key"
    OAUTH = "oauth"
    BEARER = "bearer"


@dataclass
class MCPOAuthConfig:
    """OAuth configuration for MCP server."""
    client_id: str = ""
    client_secret: str = ""
    auth_url: str = ""
    token_url: str = ""
    scopes: list[str] = field(default_factory=list)
    redirect_uri: str = "http://localhost/callback"
    _access_token: Optional[str] = None
    _refresh_token: Optional[str] = None
    _expires_at: float = 0
    
    @property
    def access_token(self) -> Optional[str]:
        return self._access_token
    
    @property
    def is_expired(self) -> bool:
        return time.time() > self._expires_at


class MCPAuthToken:
    """OAuth access token."""
    def __init__(self, access_token: str, token_type: str = "Bearer", 
                 expires_in: int = 3600, refresh_token: Optional[str] = None):
        self.access_token = access_token
        self.token_type = token_type
        self.expires_in = expires_in
        self.refresh_token = refresh_token
        self._issued_at = time.time()
    
    @property
    def expires_at(self) -> float:
        return self._issued_at + self.expires_in
    
    def is_expired(self, margin: int = 60) -> bool:
        return time.time() > (self.expires_at - margin)


class MCPTransport(ABC):
    """Abstract base for MCP transports."""
    
    @abstractmethod
    async def connect(self) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def send(self, message: dict) -> None:
        pass
    
    @abstractmethod
    async def receive(self) -> dict:
        pass
    
    @abstractmethod
    async def send_request(self, method: str, params: Optional[dict] = None) -> dict:
        pass


class MCPStdIOTransport(MCPTransport):
    """STDIO transport for MCP."""
    
    def __init__(self, command: str, args: list[str], env: dict[str, str]):
        self._command = command
        self._args = args
        self._env = env
        self._process: Optional[asyncio.subprocess.Process] = None
        self._reader_task: Optional[asyncio.Task] = None
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._request_id = 0
        self._message_queue: asyncio.Queue = asyncio.Queue()
    
    async def connect(self) -> None:
        env = {**os.environ, **self._env}
        self._process = await asyncio.create_subprocess_exec(
            self._command,
            *self._args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        self._reader_task = asyncio.create_task(self._reader_loop())
    
    async def disconnect(self) -> None:
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        if self._process:
            self._process.terminate()
            try:
                await asyncio.wait_for(self._process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self._process.kill()
    
    async def send(self, message: dict) -> None:
        if not self._process or not self._process.stdin:
            raise ConnectionError("Not connected")
        self._process.stdin.write(json.dumps(message).encode() + b"\n")
        await self._process.stdin.drain()
    
    async def receive(self) -> dict:
        return await self._message_queue.get()
    
    async def send_request(self, method: str, params: Optional[dict] = None) -> dict:
        request_id = str(self._request_id)
        self._request_id += 1
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future
        
        message = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params:
            message["params"] = params
        
        await self.send(message)
        
        return await future
    
    async def _reader_loop(self) -> None:
        if not self._process or not self._process.stdout:
            return
        try:
            while True:
                line = await self._process.stdout.readline()
                if not line:
                    break
                try:
                    message = json.loads(line.decode('utf-8'))
                    if "id" in message:
                        request_id = str(message["id"])
                        if request_id in self._pending_requests:
                            future = self._pending_requests.pop(request_id)
                            if "error" in message:
                                future.set_exception(Exception(
                                    message["error"].get("message", "Unknown error")
                                ))
                            else:
                                future.set_result(message.get("result"))
                    await self._message_queue.put(message)
                except json.JSONDecodeError:
                    pass
        except asyncio.CancelledError:
            pass


class MCPHTTPTransport(MCPTransport):
    """HTTP/SSE transport for MCP."""
    
    def __init__(self, url: str, auth: Optional[MCPAuthToken] = None,
                 ssl_context: Optional[ssl.SSLContext] = None):
        self._url = url
        self._auth = auth
        self._ssl = ssl_context
        self._session = None
        self._connected = False
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._request_id = 0
        self._sse_task: Optional[asyncio.Task] = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
    
    async def connect(self) -> None:
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp required for HTTP transport: pip install aiohttp")
        
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=self._ssl) if self._ssl else None
        )
        self._connected = True
        self._sse_task = asyncio.create_task(self._sse_listener())
    
    async def disconnect(self) -> None:
        if self._sse_task:
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass
        if self._session:
            await self._session.close()
        self._connected = False
    
    async def send(self, message: dict) -> dict[str, Any]:
        if not self._session:
            raise ConnectionError("Not connected")
        
        headers = {"Content-Type": "application/json"}
        if self._auth:
            headers["Authorization"] = f"Bearer {self._auth.access_token}"
        
        async with self._session.post(self._url, json=message, headers=headers) as resp:
            return await resp.json()
    
    async def receive(self) -> dict:
        return await self._message_queue.get()
    
    async def send_request(self, method: str, params: Optional[dict] = None) -> dict:
        request_id = str(self._request_id)
        self._request_id += 1
        
        message = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params:
            message["params"] = params
        
        return await self.send(message)
    
    async def _sse_listener(self) -> None:
        if not self._session:
            return
        
        headers = {}
        if self._auth:
            headers["Authorization"] = f"Bearer {self._auth.access_token}"
        
        try:
            async with self._session.get(self._url + "/sse", headers=headers) as resp:
                async for line in resp.content:
                    if line.startswith(b"data: "):
                        try:
                            data = json.loads(line[6:])
                            await self._message_queue.put(data)
                        except json.JSONDecodeError:
                            pass
        except asyncio.CancelledError:
            pass


class MCPWebSocketTransport(MCPTransport):
    """WebSocket transport for MCP."""
    
    def __init__(self, url: str, auth: Optional[MCPAuthToken] = None,
                 ssl_context: Optional[ssl.SSLContext] = None):
        self._url = url
        self._auth = auth
        self._ssl = ssl_context
        self._aiohttp = None
        self._session = None
        self._ws = None
        self._connected = False
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._request_id = 0
        self._reader_task: Optional[asyncio.Task] = None
        self._message_queue: asyncio.Queue = asyncio.Queue()
    
    async def connect(self) -> None:
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp required for WebSocket transport: pip install aiohttp")
        self._aiohttp = aiohttp
        self._session = aiohttp.ClientSession()
        headers: dict[str, str] = {}
        if self._auth:
            headers["Authorization"] = f"Bearer {self._auth.access_token}"
        self._ws = await self._session.ws_connect(self._url, ssl=self._ssl, headers=headers)
        self._connected = True
        self._reader_task = asyncio.create_task(self._reader_loop())
    
    async def disconnect(self) -> None:
        self._connected = False
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
            self._reader_task = None
        if self._ws:
            await self._ws.close()
            self._ws = None
        if self._session:
            await self._session.close()
            self._session = None
    
    async def send(self, message: dict) -> None:
        if not self._ws:
            raise ConnectionError("Not connected")
        await self._ws.send_json(message)
    
    async def receive(self) -> dict:
        return await self._message_queue.get()
    
    async def send_request(self, method: str, params: Optional[dict] = None) -> dict:
        request_id = str(self._request_id)
        self._request_id += 1
        future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future
        
        message = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params:
            message["params"] = params
        
        await self.send(message)
        return await future
    
    async def _reader_loop(self) -> None:
        try:
            while self._connected:
                msg = await self._ws.receive()
                if msg.type == self._aiohttp.WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        if "id" in data:
                            request_id = str(data["id"])
                            if request_id in self._pending_requests:
                                future = self._pending_requests.pop(request_id)
                                if "error" in data:
                                    future.set_exception(Exception(
                                        data["error"].get("message", "Unknown error")
                                    ))
                                else:
                                    future.set_result(data.get("result"))
                        await self._message_queue.put(data)
                    except json.JSONDecodeError:
                        pass
                elif msg.type in (
                    self._aiohttp.WSMsgType.ERROR,
                    self._aiohttp.WSMsgType.CLOSED,
                    self._aiohttp.WSMsgType.CLOSE,
                ):
                    break
        except asyncio.CancelledError:
            pass


class MCPConnectionState(Enum):
    """MCP connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class MCPTool:
    """An MCP tool definition."""
    name: str
    description: str
    input_schema: dict = field(default_factory=dict)
    server_name: str = ""


@dataclass
class MCPResource:
    """An MCP resource definition."""
    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"
    server_name: str = ""


@dataclass
class MCPConnectionConfig:
    """Configuration for an MCP connection."""
    server_name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    transport: MCPTransportType = MCPTransportType.STDIO
    url: Optional[str] = None
    auth_type: MCPAuthType = MCPAuthType.NONE
    api_key: Optional[str] = None
    oauth_config: Optional[MCPOAuthConfig] = None
    ssl_verify: bool = True
    headers: dict[str, str] = field(default_factory=dict)


class MCPProtocol:
    """
    MCP protocol handler.
    
    Implements the JSON-RPC based MCP protocol.
    """
    
    def __init__(self):
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._request_id = 0
        self._notification_handlers: dict[str, Callable] = {}
        self._sender: Optional[Callable[[dict[str, Any]], Awaitable[Any]]] = None
    
    def _next_request_id(self) -> str:
        """Generate the next request ID."""
        self._request_id += 1
        return str(self._request_id)

    def set_sender(self, sender: Callable[[dict[str, Any]], Awaitable[Any]]) -> None:
        """Set async sender used for outbound JSON-RPC messages."""
        self._sender = sender
    
    async def send_request(
        self,
        method: str,
        params: Optional[dict] = None,
    ) -> Any:
        """Send a JSON-RPC request and wait for response."""
        request_id = self._next_request_id()
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future
        
        message = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            message["params"] = params

        if self._sender is None:
            raise RuntimeError("MCPProtocol sender not configured")
        await self._sender(message)
        return await future
    
    async def send_notification(self, method: str, params: Optional[dict] = None) -> None:
        """Send a JSON-RPC notification (no response expected)."""
        message = {
            "jsonrpc": "2.0",
            "method": method,
        }
        if params:
            message["params"] = params
        if self._sender is None:
            raise RuntimeError("MCPProtocol sender not configured")
        await self._sender(message)
    
    def handle_response(self, response: dict) -> None:
        """Handle a JSON-RPC response."""
        request_id = str(response.get("id"))
        if request_id in self._pending_requests:
            future = self._pending_requests.pop(request_id)
            if "error" in response:
                future.set_exception(Exception(response["error"].get("message", "Unknown error")))
            else:
                future.set_result(response.get("result"))
    
    def register_notification_handler(self, method: str, handler: Callable) -> None:
        """Register a handler for a notification."""
        self._notification_handlers[method] = handler
    
    def handle_notification(self, notification: dict) -> None:
        """Handle a JSON-RPC notification."""
        method = notification.get("method")
        params = notification.get("params", {})
        
        if method in self._notification_handlers:
            self._notification_handlers[method](params)


class MCPClient:
    """
    MCP client for connecting to MCP servers.
    
    Supports STDIO, SSE, and HTTP transports.
    """
    
    def __init__(self, config: MCPConnectionConfig):
        self.config = config
        self.protocol = MCPProtocol()
        self._transport: Optional[MCPTransport] = None
        self._receiver_task: Optional[asyncio.Task] = None
        self._state = MCPConnectionState.DISCONNECTED
        self._tools: list[MCPTool] = []
        self._resources: list[MCPResource] = []
        self._tools_lock = asyncio.Lock()
    
    @property
    def state(self) -> MCPConnectionState:
        """Get current connection state."""
        return self._state
    
    @property
    def tools(self) -> list[MCPTool]:
        """Get available tools from this server."""
        return self._tools.copy()
    
    @property
    def resources(self) -> list[MCPResource]:
        """Get available resources from this server."""
        return self._resources.copy()
    
    async def connect(self) -> None:
        """Connect to the MCP server."""
        if self._state == MCPConnectionState.CONNECTED:
            return
        
        self._state = MCPConnectionState.CONNECTING

        try:
            self._transport = self._create_transport()
            self.protocol.set_sender(self._send_with_transport)
            await self._transport.connect()
            self._receiver_task = asyncio.create_task(self._receive_loop())
            await self._initialize()
            self._state = MCPConnectionState.CONNECTED
        except Exception as e:
            self._state = MCPConnectionState.ERROR
            await self._cleanup_transport()
            raise ConnectionError(f"Failed to connect to MCP server: {e}")

    def _create_transport(self) -> MCPTransport:
        """Create transport instance from connection config."""
        auth = self._build_auth_token()
        ssl_context = self._build_ssl_context()

        if self.config.transport == MCPTransportType.STDIO:
            if not self.config.command:
                raise ValueError("STDIO transport requires 'command'")
            return MCPStdIOTransport(
                command=self.config.command,
                args=self.config.args,
                env=self.config.env,
            )

        endpoint = self.config.url or self.config.command
        if not endpoint:
            raise ValueError("HTTP/SSE/WebSocket transport requires 'url' (or command fallback)")

        if self.config.transport in (MCPTransportType.SSE, MCPTransportType.HTTP):
            return MCPHTTPTransport(endpoint, auth=auth, ssl_context=ssl_context)
        if self.config.transport == MCPTransportType.WEBSOCKET:
            return MCPWebSocketTransport(endpoint, auth=auth, ssl_context=ssl_context)

        raise NotImplementedError(f"Transport {self.config.transport} not supported")

    def _build_auth_token(self) -> Optional[MCPAuthToken]:
        """Build auth token from connection config."""
        if self.config.auth_type in (MCPAuthType.API_KEY, MCPAuthType.BEARER):
            if self.config.api_key:
                return MCPAuthToken(access_token=self.config.api_key)
            return None

        if self.config.auth_type == MCPAuthType.OAUTH and self.config.oauth_config:
            token = self.config.oauth_config.access_token
            if token:
                return MCPAuthToken(access_token=token)
        return None

    def _build_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Build SSL context according to config.ssl_verify."""
        if self.config.ssl_verify:
            return None
        insecure_context = ssl.create_default_context()
        insecure_context.check_hostname = False
        insecure_context.verify_mode = ssl.CERT_NONE
        return insecure_context

    async def _send_with_transport(self, message: dict[str, Any]) -> None:
        """Send JSON-RPC message through active transport."""
        if self._transport is None:
            raise ConnectionError("MCP transport is not connected")
        response = await self._transport.send(message)
        if isinstance(response, dict) and "id" in response:
            self.protocol.handle_response(response)

    async def _receive_loop(self) -> None:
        """Dispatch inbound transport messages to MCPProtocol."""
        if self._transport is None:
            return
        try:
            while True:
                message = await self._transport.receive()
                if not isinstance(message, dict):
                    continue
                if "id" in message:
                    self.protocol.handle_response(message)
                else:
                    self.protocol.handle_notification(message)
        except asyncio.CancelledError:
            pass
        except Exception:
            # Transport failures are surfaced through operation-level calls.
            pass

    async def _cleanup_transport(self) -> None:
        """Cleanup transport and receiver task."""
        if self._receiver_task:
            self._receiver_task.cancel()
            try:
                await self._receiver_task
            except asyncio.CancelledError:
                pass
            self._receiver_task = None
        if self._transport:
            await self._transport.disconnect()
            self._transport = None
    
    async def _initialize(self) -> None:
        """Initialize the MCP connection."""
        result = await self.protocol.send_request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {},
                },
                "clientInfo": {
                    "name": "claude-code-python",
                    "version": "1.0.0",
                },
            }
        )
        
        # Store capabilities
        _capabilities = result.get("capabilities", {}) if isinstance(result, dict) else {}
        
        # Fetch tools and resources
        await self._fetch_tools()
        await self._fetch_resources()
    
    async def _fetch_tools(self) -> None:
        """Fetch available tools from the server."""
        try:
            result = await self.protocol.send_request("tools/list")
            tools_list = result.get("tools", [])
            
            async with self._tools_lock:
                self._tools = [
                    MCPTool(
                        name=t["name"],
                        description=t.get("description", ""),
                        input_schema=t.get("inputSchema", {}),
                        server_name=self.config.server_name,
                    )
                    for t in tools_list
                ]
        except Exception:
            pass
    
    async def _fetch_resources(self) -> None:
        """Fetch available resources from the server."""
        try:
            result = await self.protocol.send_request("resources/list")
            resources_list = result.get("resources", [])
            
            self._resources = [
                MCPResource(
                    uri=r["uri"],
                    name=r.get("name", r["uri"]),
                    description=r.get("description", ""),
                    mime_type=r.get("mimeType", "text/plain"),
                    server_name=self.config.server_name,
                )
                for r in resources_list
            ]
        except Exception:
            pass
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        """Call a tool on the MCP server."""
        if self._state != MCPConnectionState.CONNECTED:
            raise ConnectionError("Not connected to MCP server")
        
        result = await self.protocol.send_request(
            "tools/call",
            {
                "name": tool_name,
                "arguments": arguments,
            }
        )
        
        return result
    
    async def read_resource(self, uri: str) -> dict[str, Any]:
        """Read a resource from the MCP server."""
        if self._state != MCPConnectionState.CONNECTED:
            raise ConnectionError("Not connected to MCP server")
        
        result = await self.protocol.send_request(
            "resources/read",
            {"uri": uri}
        )
        
        return result
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        await self._cleanup_transport()
        self._state = MCPConnectionState.DISCONNECTED
        self._tools.clear()
        self._resources.clear()


class MCPManager:
    """
    Manager for multiple MCP server connections.
    """
    
    def __init__(self):
        self._clients: dict[str, MCPClient] = {}
        self._lock = asyncio.Lock()
    
    async def add_server(self, config: MCPConnectionConfig) -> MCPClient:
        """Add and connect an MCP server."""
        async with self._lock:
            if config.server_name in self._clients:
                raise ValueError(f"Server {config.server_name} already exists")
            
            client = MCPClient(config)
            await client.connect()
            self._clients[config.server_name] = client
            
            return client
    
    async def remove_server(self, server_name: str) -> None:
        """Remove and disconnect an MCP server."""
        async with self._lock:
            if server_name in self._clients:
                await self._clients[server_name].disconnect()
                del self._clients[server_name]
    
    def get_client(self, server_name: str) -> Optional[MCPClient]:
        """Get a connected MCP client."""
        return self._clients.get(server_name)
    
    def get_all_tools(self) -> list[MCPTool]:
        """Get all tools from all connected servers."""
        tools = []
        for client in self._clients.values():
            tools.extend(client.tools)
        return tools
    
    def get_all_resources(self) -> list[MCPResource]:
        """Get all resources from all connected servers."""
        resources = []
        for client in self._clients.values():
            resources.extend(client.resources)
        return resources
    
    async def disconnect_all(self) -> None:
        """Disconnect all MCP servers."""
        for client in list(self._clients.values()):
            await client.disconnect()
        self._clients.clear()
    
    def list_servers(self) -> dict[str, dict]:
        """List all configured servers and their status."""
        return {
            name: {
                "connected": client.state == MCPConnectionState.CONNECTED,
                "tools": len(client.tools),
                "resources": len(client.resources),
            }
            for name, client in self._clients.items()
        }
    
    async def list_resources(self, server_name: Optional[str] = None) -> list[MCPResource]:
        """List resources from all or specific server."""
        if server_name:
            client = self._clients.get(server_name)
            return client.resources if client else []
        return self.get_all_resources()
    
    async def read_resource(self, uri: str) -> Optional[dict[str, Any]]:
        """Read a resource by URI."""
        for client in self._clients.values():
            for resource in client.resources:
                if resource.uri == uri:
                    return await client.read_resource(uri)
        return None
    
    async def authenticate(
        self,
        server_name: str,
        auth_type: str,
        credentials: dict[str, Any],
    ) -> None:
        """Authenticate with an MCP server."""
        client = self._clients.get(server_name)
        if client is None:
            raise ValueError(f"Server {server_name} not found")
        
        if auth_type == "api_key":
            api_key = credentials.get("api_key")
            if api_key:
                client.config.env["API_KEY"] = api_key
                client.config.auth_type = MCPAuthType.API_KEY
        elif auth_type == "oauth":
            oauth_config = MCPOAuthConfig(
                client_id=credentials.get("client_id", ""),
                client_secret=credentials.get("client_secret", ""),
                auth_url=credentials.get("auth_url", ""),
                token_url=credentials.get("token_url", ""),
                scopes=credentials.get("scopes", []),
            )
            client.config.oauth_config = oauth_config
            client.config.auth_type = MCPAuthType.OAUTH

    async def refresh_oauth_token(self, server_name: str) -> Optional[MCPAuthToken]:
        """Refresh OAuth token for a server."""
        client = self._clients.get(server_name)
        if client is None or not client.config.oauth_config:
            return None
        
        oauth_cfg = client.config.oauth_config
        try:
            import aiohttp
        except ImportError:
            return None
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                oauth_cfg.token_url,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": oauth_cfg._refresh_token,
                    "client_id": oauth_cfg.client_id,
                    "client_secret": oauth_cfg.client_secret,
                },
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    token = MCPAuthToken(
                        access_token=data["access_token"],
                        token_type=data.get("token_type", "Bearer"),
                        expires_in=data.get("expires_in", 3600),
                        refresh_token=data.get("refresh_token", oauth_cfg._refresh_token),
                    )
                    oauth_cfg._access_token = token.access_token
                    oauth_cfg._refresh_token = token.refresh_token
                    oauth_cfg._expires_at = token.expires_at
                    return token
        return None

    async def start_oauth_flow(
        self,
        server_name: str,
    ) -> tuple[str, str]:
        """Start OAuth flow, return (authorization_url, redirect_uri)."""
        client = self._clients.get(server_name)
        if client is None or not client.config.oauth_config:
            raise ValueError(f"Server {server_name} not configured for OAuth")
        
        oauth_cfg = client.config.oauth_config
        state = hashlib.sha256(str(uuid4()).encode()).hexdigest()[:16]
        
        auth_url = f"{oauth_cfg.auth_url}?client_id={oauth_cfg.client_id}&redirect_uri={oauth_cfg.redirect_uri}&response_type=code&scope={' '.join(oauth_cfg.scopes)}&state={state}"
        
        return auth_url, oauth_cfg.redirect_uri

    async def complete_oauth_flow(
        self,
        server_name: str,
        authorization_code: str,
    ) -> MCPAuthToken:
        """Complete OAuth flow with authorization code."""
        client = self._clients.get(server_name)
        if client is None or not client.config.oauth_config:
            raise ValueError(f"Server {server_name} not configured for OAuth")
        
        oauth_cfg = client.config.oauth_config
        
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp required for OAuth: pip install aiohttp")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                oauth_cfg.token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": authorization_code,
                    "redirect_uri": oauth_cfg.redirect_uri,
                    "client_id": oauth_cfg.client_id,
                    "client_secret": oauth_cfg.client_secret,
                },
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"OAuth failed: {resp.status}")
                
                data = await resp.json()
                token = MCPAuthToken(
                    access_token=data["access_token"],
                    token_type=data.get("token_type", "Bearer"),
                    expires_in=data.get("expires_in", 3600),
                    refresh_token=data.get("refresh_token"),
                )
                oauth_cfg._access_token = token.access_token
                oauth_cfg._refresh_token = token.refresh_token
                oauth_cfg._expires_at = token.expires_at
                return token


# Global MCP manager instance
_mcp_manager: Optional[MCPManager] = None


def get_mcp_manager() -> MCPManager:
    """Get the global MCP manager instance."""
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPManager()
    return _mcp_manager


def set_mcp_manager(manager: MCPManager) -> None:
    """Set the global MCP manager instance."""
    global _mcp_manager
    _mcp_manager = manager
