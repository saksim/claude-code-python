"""
Claude Code Python - Remote Transport Layer
Bidirectional streaming for remote sessions
"""

from __future__ import annotations

import asyncio
import json
import ssl
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable

from claude_code.features import FeatureConfig


class RemoteTransportType(Enum):
    """Remote transport types."""

    WEBSOCKET = "websocket"
    SSE = "sse"
    STDIO = "stdio"


@dataclass(frozen=True, slots=True)
class RemoteSessionConfig:
    """Configuration for remote session."""
    session_id: str = ""
    remote_url: str = ""
    transport: RemoteTransportType = RemoteTransportType.WEBSOCKET
    auth_token: Optional[str] = None
    headers: dict[str, str] = field(default_factory=dict)
    reconnect_attempts: int = 3
    reconnect_delay_ms: int = 1000
    ping_interval_ms: int = 30000
    ssl_verify: bool = True


class Transport(ABC):
    """Abstract transport base class."""
    
    @abstractmethod
    async def connect(self) -> None:
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        pass
    
    @abstractmethod
    async def send(self, data: dict) -> None:
        pass
    
    @abstractmethod
    async def receive(self) -> dict:
        pass
    
    @abstractmethod
    async def send_raw(self, data: str) -> None:
        pass
    
    @abstractmethod
    async def receive_raw(self) -> str:
        pass


class WebSocketTransport(Transport):
    """WebSocket transport for remote sessions."""
    
    def __init__(self, url: str, headers: dict[str, str] = None, ssl_verify: bool = True):
        self._url = url
        self._headers = headers or {}
        self._ssl_verify = ssl_verify
        self._ws = None
        self._session = None
        self._connected = False
        self._receive_queue: asyncio.Queue = asyncio.Queue()
        self._reader_task: Optional[asyncio.Task] = None
        self._on_data: Optional[Callable[[str], None]] = None
        self._on_close: Optional[Callable[[], None]] = None
    
    def set_on_data(self, callback: Callable[[str], None]) -> None:
        self._on_data = callback
    
    def set_on_close(self, callback: Callable[[], None]) -> None:
        self._on_close = callback
    
    async def connect(self) -> None:
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp required for WebSocket: pip install aiohttp")
        
        ssl_context = None if self._ssl_verify else ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        self._session = aiohttp.ClientSession()
        self._ws = await self._session.ws_connect(
            self._url,
            ssl=ssl_context if not self._ssl_verify else None,
            headers=self._headers,
        )
        self._connected = True
        self._reader_task = asyncio.create_task(self._reader_loop())
    
    async def disconnect(self) -> None:
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        if self._ws:
            await self._ws.close()
        if self._session:
            await self._session.close()
        self._connected = False
    
    async def send(self, data: dict) -> None:
        await self.send_raw(json.dumps(data))
    
    async def send_raw(self, data: str) -> None:
        if not self._ws:
            raise ConnectionError("Not connected")
        await self._ws.send_str(data)
    
    async def receive(self) -> dict:
        data = await self.receive_raw()
        return json.loads(data)
    
    async def receive_raw(self) -> str:
        return await self._receive_queue.get()
    
    async def _reader_loop(self) -> None:
        try:
            while self._connected and self._ws:
                msg = await self._ws.receive()
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = msg.data
                    if self._on_data:
                        self._on_data(data)
                    await self._receive_queue.put(data)
                elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSE):
                    break
        except asyncio.CancelledError:
            pass
        finally:
            if self._on_close:
                self._on_close()


class SSETransport(Transport):
    """SSE (Server-Sent Events) transport with POST for remote sessions."""
    
    def __init__(self, url: str, headers: dict[str, str] = None, ssl_verify: bool = True):
        self._url = url
        self._headers = headers or {}
        self._ssl_verify = ssl_verify
        self._session = None
        self._connected = False
        self._receive_queue: asyncio.Queue = asyncio.Queue()
        self._sse_task: Optional[asyncio.Task] = None
        self._on_data: Optional[Callable[[str], None]] = None
        self._on_close: Optional[Callable[[], None]] = None
    
    def set_on_data(self, callback: Callable[[str], None]) -> None:
        self._on_data = callback
    
    def set_on_close(self, callback: Callable[[], None]) -> None:
        self._on_close = callback
    
    async def connect(self) -> None:
        try:
            import aiohttp
        except ImportError:
            raise ImportError("aiohttp required for SSE: pip install aiohttp")
        
        self._session = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(ssl=self._ssl_verify)
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
    
    async def send(self, data: dict) -> None:
        await self.send_raw(json.dumps(data))
    
    async def send_raw(self, data: str) -> None:
        if not self._session:
            raise ConnectionError("Not connected")
        
        async with self._session.post(self._url, data=data, headers=self._headers) as resp:
            await resp.text()
    
    async def receive(self) -> dict:
        data = await self.receive_raw()
        return json.loads(data)
    
    async def receive_raw(self) -> str:
        return await self._receive_queue.get()
    
    async def _sse_listener(self) -> None:
        if not self._session:
            return
        
        try:
            async with self._session.get(self._url + "/sse", headers=self._headers) as resp:
                async for line in resp.content:
                    if line.startswith(b"data: "):
                        data = line[6:].decode("utf-8").strip()
                        if data:
                            if self._on_data:
                                self._on_data(data)
                            await self._receive_queue.put(data)
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
        finally:
            if self._on_close:
                self._on_close()


class RemoteSession:
    """Remote session handler with reconnection logic."""
    
    def __init__(self, config: RemoteSessionConfig):
        self._config = config
        self._transport: Optional[Transport] = None
        self._connected = False
        self._session_id = config.session_id or str(uuid.uuid4())
        self._reconnect_count = 0
        self._on_message: Optional[Callable[[dict], Awaitable[None]]] = None
        self._on_connect: Optional[Callable[[], Awaitable[None]]] = None
        self._on_disconnect: Optional[Callable[[], Awaitable[None]]] = None
        self._ping_task: Optional[asyncio.Task] = None
    
    @property
    def session_id(self) -> str:
        return self._session_id
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    def set_on_message(self, callback: Callable[[dict], Awaitable[None]]) -> None:
        self._on_message = callback
    
    def set_on_connect(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._on_connect = callback
    
    def set_on_disconnect(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._on_disconnect = callback
    
    async def connect(self) -> bool:
        """Connect to remote session with reconnection logic."""
        for attempt in range(self._config.reconnect_attempts):
            try:
                await self._create_transport()
                await self._transport.connect()
                
                self._connected = True
                self._reconnect_count = 0
                
                if self._on_connect:
                    await self._on_connect()
                
                self._ping_task = asyncio.create_task(self._ping_loop())
                return True
            
            except Exception as e:
                self._reconnect_count = attempt + 1
                if attempt < self._config.reconnect_attempts - 1:
                    await asyncio.sleep(self._config.reconnect_delay_ms / 1000)
        
        return False
    
    async def disconnect(self) -> None:
        """Disconnect from remote session."""
        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
        
        if self._transport:
            await self._transport.disconnect()
        
        self._connected = False
        
        if self._on_disconnect:
            await self._on_disconnect()
    
    async def send(self, data: dict) -> None:
        """Send message to remote session."""
        if not self._connected:
            raise ConnectionError("Not connected to remote session")
        
        data["session_id"] = self._session_id
        data["timestamp"] = time.time()
        await self._transport.send(data)
    
    async def receive(self) -> dict:
        """Receive message from remote session."""
        if not self._connected:
            raise ConnectionError("Not connected to remote session")
        
        return await self._transport.receive()
    
    async def _create_transport(self) -> None:
        """Create transport based on configuration."""
        headers = {
            **self._config.headers,
            "Content-Type": "application/json",
        }
        if self._config.auth_token:
            headers["Authorization"] = f"Bearer {self._config.auth_token}"
        headers["X-Session-ID"] = self._session_id
        
        if self._config.transport == RemoteTransportType.WEBSOCKET:
            self._transport = WebSocketTransport(
                self._config.remote_url,
                headers,
                self._config.ssl_verify,
            )
        elif self._config.transport == RemoteTransportType.SSE:
            self._transport = SSETransport(
                self._config.remote_url,
                headers,
                self._config.ssl_verify,
            )
        else:
            raise ValueError(f"Unsupported transport: {self._config.transport}")
        
        self._transport.set_on_data(self._handle_data)
        self._transport.set_on_close(self._handle_close)
    
    async def _handle_data(self, data: str) -> None:
        """Handle incoming data."""
        try:
            message = json.loads(data)
            if self._on_message:
                await self._on_message(message)
        except json.JSONDecodeError:
            pass
    
    async def _handle_close(self) -> None:
        """Handle connection close."""
        was_connected = self._connected
        self._connected = False
        
        if was_connected and self._on_disconnect:
            await self._on_disconnect()
        
        if self._config.reconnect_attempts > 0 and self._reconnect_count < self._config.reconnect_attempts:
            await asyncio.sleep(self._config.reconnect_delay_ms / 1000)
            await self.connect()
    
    async def _ping_loop(self) -> None:
        """Send periodic pings to keep connection alive."""
        while self._connected:
            try:
                await asyncio.sleep(self._config.ping_interval_ms / 1000)
                if self._connected:
                    await self.send({"type": "ping"})
            except asyncio.CancelledError:
                break


class RemoteIO:
    """
    Remote I/O handler for bidirectional streaming.
    Supports WebSocket and SSE transports.
    """
    
    def __init__(self, remote_url: str, auth_token: Optional[str] = None):
        self._remote_url = remote_url
        self._auth_token = auth_token
        self._session: Optional[RemoteSession] = None
        self._input_queue: asyncio.Queue = asyncio.Queue()
        self._reader_task: Optional[asyncio.Task] = None
    
    @property
    def input_stream(self) -> asyncio.Queue:
        return self._input_queue
    
    async def connect(self) -> bool:
        """Connect to remote session."""
        config = RemoteSessionConfig(
            remote_url=self._remote_url,
            auth_token=self._auth_token,
            transport=RemoteTransportType.WEBSOCKET if "ws://" in self._remote_url else RemoteTransportType.SSE,
        )
        
        self._session = RemoteSession(config)
        self._session.set_on_message(self._handle_message)
        
        connected = await self._session.connect()
        if connected:
            self._reader_task = asyncio.create_task(self._reader_loop())
        
        return connected
    
    async def disconnect(self) -> None:
        """Disconnect from remote session."""
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        
        if self._session:
            await self._session.disconnect()
    
    async def send(self, data: dict) -> None:
        """Send message to remote."""
        if self._session:
            await self._session.send(data)
    
    async def write(self, data: str) -> None:
        """Write raw data to remote."""
        if self._session:
            await self._session.send({"type": "message", "content": data})
    
    async def _handle_message(self, message: dict) -> None:
        """Handle incoming message."""
        await self._input_queue.put(message)
    
    async def _reader_loop(self) -> None:
        """Internal reader loop."""
        while self._session and self._session.is_connected:
            try:
                message = await self._session.receive()
                await self._input_queue.put(message)
            except asyncio.CancelledError:
                break
            except Exception:
                break


def get_transport_for_url(url: str, headers: dict = None) -> Transport:
    """Get appropriate transport based on URL protocol."""
    if url.startswith("ws://") or url.startswith("wss://"):
        return WebSocketTransport(url, headers)
    elif url.startswith("http://") or url.startswith("https://"):
        return SSETransport(url, headers)
    else:
        raise ValueError(f"Unsupported URL scheme: {url}")


__all__ = [
    "RemoteTransportType",
    "RemoteSessionConfig",
    "Transport",
    "WebSocketTransport",
    "SSETransport",
    "RemoteSession",
    "RemoteIO",
    "get_transport_for_url",
]
