"""WebSocket Support for Claude Code Python.

Provides WebSocket server and client for real-time communication.
Note: This is a framework - actual implementation requires aiohttp or websockets package.
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class WebSocketState(Enum):
    """WebSocket connection states."""

    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class WebSocketMessage:
    """WebSocket message.

    Attributes:
        type: Message type (text, binary, ping, pong, close).
        data: Message data.
        timestamp: Message timestamp.
    """

    type: str = "text"
    data: str = ""
    timestamp: float = field(default_factory=lambda: asyncio.get_event_loop().time())


class WebSocketMessageHandler:
    """Handler for WebSocket messages."""

    def __init__(self, handler: Callable[[WebSocketMessage], Any]) -> None:
        self.handler = handler
        self.message_count: int = 0

    async def handle(self, message: WebSocketMessage) -> Any:
        self.message_count += 1
        if asyncio.iscoroutinefunction(self.handler):
            return await self.handler(message)
        return self.handler(message)


class WebSocketServer:
    """WebSocket server for real-time communication.

    This is a framework class - actual implementation requires aiohttp or websockets.

    Usage:
        server = WebSocketServer(host="0.0.0.0", port=8765)

        @server.on_message
        async def handle_message(msg):
            print(f"Received: {msg.data}")

        await server.start()
        await asyncio.Event().wait()  # Keep running
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8765,
        max_connections: int = 100,
    ) -> None:
        """Initialize WebSocket server.

        Args:
            host: Server host.
            port: Server port.
            max_connections: Maximum concurrent connections.
        """
        self.host = host
        self.port = port
        self.max_connections = max_connections
        self._connections: Dict[str, Any] = {}
        self._message_handlers: List[WebSocketMessageHandler] = []
        self._connection_handlers: List[Callable[[str], Any]] = []
        self._disconnection_handlers: List[Callable[[str], Any]] = []
        self._running = False
        self._server = None

    async def start(self) -> None:
        """Start the WebSocket server."""
        if self._running:
            return

        try:
            # Try to use aiohttp if available
            import aiohttp
            from aiohttp import web

            async def websocket_handler(request):
                ws = web.WebSocketResponse()
                await ws.prepare(request)

                connection_id = id(ws)
                self._connections[connection_id] = ws

                # Notify connection handlers
                for handler in self._connection_handlers:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(connection_id)
                    else:
                        handler(connection_id)

                try:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            message = WebSocketMessage(
                                type="text",
                                data=msg.data,
                            )
                            for handler in self._message_handlers:
                                await handler.handle(message)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            break
                finally:
                    del self._connections[connection_id]
                    for handler in self._disconnection_handlers:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(connection_id)
                        else:
                            handler(connection_id)

                return ws

            app = web.Application()
            app.add_route("GET", "/ws", websocket_handler)

            self._server = web.AppRunner(app)
            await self._server.setup()
            site = web.TCPSite(self._server, self.host, self.port)
            await site.start()

            self._running = True
            print(f"WebSocket server started on {self.host}:{self.port}")

        except ImportError:
            print("WebSocket server requires aiohttp. Install with: pip install aiohttp")
            self._running = False
        except Exception as e:
            print(f"Failed to start WebSocket server: {e}")
            self._running = False

    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if not self._running:
            return

        self._running = False

        # Close all connections
        for ws in self._connections.values():
            await ws.close()

        if self._server:
            await self._server.cleanup()

        print("WebSocket server stopped")

    def on_message(self, handler: Callable[[WebSocketMessage], Any]) -> Callable:
        """Decorator to register message handler.

        Args:
            handler: Message handler function.

        Returns:
            Decorated handler.
        """
        self._message_handlers.append(WebSocketMessageHandler(handler))
        return handler

    def on_connect(self, handler: Callable[[str], Any]) -> Callable:
        """Decorator to register connection handler.

        Args:
            handler: Connection handler function.

        Returns:
            Decorated handler.
        """
        self._connection_handlers.append(handler)
        return handler

    def on_disconnect(self, handler: Callable[[str], Any]) -> Callable:
        """Decorator to register disconnection handler.

        Args:
            handler: Disconnection handler function.

        Returns:
            Decorated handler.
        """
        self._disconnection_handlers.append(handler)
        return handler

    async def broadcast(self, message: WebSocketMessage) -> None:
        """Broadcast message to all connections.

        Args:
            message: Message to broadcast.
        """
        for ws in self._connections.values():
            await ws.send_str(message.data)

    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics.

        Returns:
            Statistics dictionary.
        """
        return {
            "running": self._running,
            "connections": len(self._connections),
            "max_connections": self.max_connections,
            "message_handlers": len(self._message_handlers),
        }


class WebSocketClient:
    """WebSocket client for real-time communication.

    Usage:
        client = WebSocketClient("ws://localhost:8765/ws")

        @client.on_message
        async def handle_message(msg):
            print(f"Received: {msg.data}")

        await client.connect()
    """

    def __init__(self, url: str, max_reconnect: int = 3) -> None:
        """Initialize WebSocket client.

        Args:
            url: WebSocket URL.
            max_reconnect: Maximum reconnection attempts.
        """
        self.url = url
        self.max_reconnect = max_reconnect
        self._ws = None
        self._state = WebSocketState.DISCONNECTED
        self._message_handlers: List[WebSocketMessageHandler] = []
        self._reconnect_count = 0

    async def connect(self) -> bool:
        """Connect to WebSocket server.

        Returns:
            True if connected successfully.
        """
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                self._ws = await session.ws_connect(self.url)
                self._state = WebSocketState.CONNECTED
                self._reconnect_count = 0
                return True
        except ImportError:
            print("WebSocket client requires aiohttp. Install with: pip install aiohttp")
            return False
        except Exception as e:
            print(f"Failed to connect: {e}")
            self._state = WebSocketState.ERROR
            return False

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        if self._ws:
            await self._ws.close()
        self._state = WebSocketState.DISCONNECTED

    async def send(self, message: WebSocketMessage) -> None:
        """Send a message.

        Args:
            message: Message to send.
        """
        if self._ws and self._state == WebSocketState.CONNECTED:
            await self._ws.send_str(message.data)

    async def listen(self) -> None:
        """Listen for messages (blocking)."""
        if not self._ws:
            return

        async for msg in self._ws:
            if msg.type == "text":
                message = WebSocketMessage(type="text", data=msg.data)
                for handler in self._message_handlers:
                    await handler.handle(message)

    def on_message(self, handler: Callable[[WebSocketMessage], Any]) -> Callable:
        """Decorator to register message handler.

        Args:
            handler: Message handler function.

        Returns:
            Decorated handler.
        """
        self._message_handlers.append(WebSocketMessageHandler(handler))
        return handler

    @property
    def state(self) -> WebSocketState:
        """Get connection state."""
        return self._state


# Global WebSocket server
_ws_server: Optional[WebSocketServer] = None


def get_websocket_server(
    host: str = "0.0.0.0",
    port: int = 8765,
) -> WebSocketServer:
    """Get or create the global WebSocket server.

    Args:
        host: Server host.
        port: Server port.

    Returns:
        Global WebSocketServer instance.
    """
    global _ws_server
    if _ws_server is None:
        _ws_server = WebSocketServer(host, port)
    return _ws_server


def start_websocket_server(
    host: str = "0.0.0.0",
    port: int = 8765,
) -> asyncio.Task:
    """Start WebSocket server as background task.

    Args:
        host: Server host.
        port: Server port.

    Returns:
        asyncio Task.
    """
    server = get_websocket_server(host, port)
    return asyncio.create_task(server.start())