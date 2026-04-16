"""Claude Code Python - Remote Transport Layer."""

from __future__ import annotations

import asyncio
import inspect
import json
import ssl
import time
import uuid
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Optional

warnings.warn(
    f"{__name__} is deprecated and will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)


class RemoteTransportType(Enum):
    """Remote transport types."""

    WEBSOCKET = "websocket"
    SSE = "sse"
    STDIO = "stdio"


@dataclass(frozen=True, slots=True)
class RemoteSessionConfig:
    """Configuration for remote session transport."""

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
    async def send(self, data: dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def receive(self) -> dict[str, Any]:
        pass

    @abstractmethod
    async def send_raw(self, data: str) -> None:
        pass

    @abstractmethod
    async def receive_raw(self) -> str:
        pass


async def _maybe_await(result: Any) -> None:
    if inspect.isawaitable(result):
        await result


class WebSocketTransport(Transport):
    """WebSocket transport for remote sessions."""

    def __init__(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        ssl_verify: bool = True,
    ) -> None:
        self._url = url
        self._headers = headers or {}
        self._ssl_verify = ssl_verify
        self._connected = False
        self._session: Any = None
        self._ws: Any = None
        self._aiohttp: Any = None
        self._receive_queue: asyncio.Queue[str] = asyncio.Queue()
        self._reader_task: Optional[asyncio.Task[None]] = None
        self._on_data: Optional[Callable[[str], Any]] = None
        self._on_close: Optional[Callable[[], Any]] = None

    def set_on_data(self, callback: Callable[[str], Any]) -> None:
        self._on_data = callback

    def set_on_close(self, callback: Callable[[], Any]) -> None:
        self._on_close = callback

    async def connect(self) -> None:
        try:
            import aiohttp
        except ImportError as exc:
            raise ImportError("aiohttp required for WebSocket transport") from exc

        ssl_context = None
        if not self._ssl_verify:
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE

        self._aiohttp = aiohttp
        self._session = aiohttp.ClientSession()
        self._ws = await self._session.ws_connect(
            self._url,
            headers=self._headers,
            ssl=ssl_context,
        )
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

        if self._ws is not None:
            await self._ws.close()
        if self._session is not None:
            await self._session.close()

    async def send(self, data: dict[str, Any]) -> None:
        await self.send_raw(json.dumps(data))

    async def send_raw(self, data: str) -> None:
        if self._ws is None:
            raise ConnectionError("WebSocket is not connected")
        await self._ws.send_str(data)

    async def receive(self) -> dict[str, Any]:
        return json.loads(await self.receive_raw())

    async def receive_raw(self) -> str:
        return await self._receive_queue.get()

    async def _reader_loop(self) -> None:
        try:
            while self._connected and self._ws is not None:
                msg = await self._ws.receive()
                if msg.type == self._aiohttp.WSMsgType.TEXT:
                    data = msg.data
                    if self._on_data is not None:
                        await _maybe_await(self._on_data(data))
                    await self._receive_queue.put(data)
                elif msg.type in {
                    self._aiohttp.WSMsgType.ERROR,
                    self._aiohttp.WSMsgType.CLOSE,
                    self._aiohttp.WSMsgType.CLOSED,
                }:
                    break
        except asyncio.CancelledError:
            pass
        finally:
            if self._on_close is not None:
                await _maybe_await(self._on_close())


class SSETransport(Transport):
    """SSE transport with POST writes + SSE reads."""

    def __init__(
        self,
        url: str,
        headers: Optional[dict[str, str]] = None,
        ssl_verify: bool = True,
    ) -> None:
        self._url = url
        self._headers = headers or {}
        self._ssl_verify = ssl_verify
        self._session: Any = None
        self._connected = False
        self._receive_queue: asyncio.Queue[str] = asyncio.Queue()
        self._listener_task: Optional[asyncio.Task[None]] = None
        self._on_data: Optional[Callable[[str], Any]] = None
        self._on_close: Optional[Callable[[], Any]] = None

    def set_on_data(self, callback: Callable[[str], Any]) -> None:
        self._on_data = callback

    def set_on_close(self, callback: Callable[[], Any]) -> None:
        self._on_close = callback

    async def connect(self) -> None:
        try:
            import aiohttp
        except ImportError as exc:
            raise ImportError("aiohttp required for SSE transport") from exc

        connector = aiohttp.TCPConnector(ssl=self._ssl_verify)
        self._session = aiohttp.ClientSession(connector=connector)
        self._connected = True
        self._listener_task = asyncio.create_task(self._sse_listener())

    async def disconnect(self) -> None:
        self._connected = False
        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._session is not None:
            await self._session.close()

    async def send(self, data: dict[str, Any]) -> None:
        await self.send_raw(json.dumps(data))

    async def send_raw(self, data: str) -> None:
        if self._session is None:
            raise ConnectionError("SSE transport is not connected")

        async with self._session.post(self._url, data=data, headers=self._headers) as resp:
            await resp.read()

    async def receive(self) -> dict[str, Any]:
        return json.loads(await self.receive_raw())

    async def receive_raw(self) -> str:
        return await self._receive_queue.get()

    async def _sse_listener(self) -> None:
        if self._session is None:
            return

        try:
            async with self._session.get(f"{self._url}/sse", headers=self._headers) as resp:
                async for raw in resp.content:
                    line = raw.decode("utf-8", errors="replace").strip()
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if not data:
                        continue
                    if self._on_data is not None:
                        await _maybe_await(self._on_data(data))
                    await self._receive_queue.put(data)
        except asyncio.CancelledError:
            pass
        finally:
            if self._on_close is not None:
                await _maybe_await(self._on_close())


class RemoteSession:
    """Remote session handler with reconnection logic."""

    def __init__(self, config: RemoteSessionConfig) -> None:
        self._config = config
        self._transport: Optional[Transport] = None
        self._connected = False
        self._session_id = config.session_id or str(uuid.uuid4())
        self._reconnect_count = 0
        self._on_message: Optional[Callable[[dict[str, Any]], Awaitable[None]]] = None
        self._on_connect: Optional[Callable[[], Awaitable[None]]] = None
        self._on_disconnect: Optional[Callable[[], Awaitable[None]]] = None
        self._ping_task: Optional[asyncio.Task[None]] = None

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def is_connected(self) -> bool:
        return self._connected

    def set_on_message(self, callback: Callable[[dict[str, Any]], Awaitable[None]]) -> None:
        self._on_message = callback

    def set_on_connect(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._on_connect = callback

    def set_on_disconnect(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._on_disconnect = callback

    async def connect(self) -> bool:
        """Connect to remote session with retry."""
        for attempt in range(self._config.reconnect_attempts):
            try:
                await self._create_transport()
                assert self._transport is not None
                await self._transport.connect()

                self._connected = True
                self._reconnect_count = 0

                if self._on_connect:
                    await self._on_connect()

                self._ping_task = asyncio.create_task(self._ping_loop())
                return True
            except Exception:
                self._reconnect_count = attempt + 1
                if attempt < self._config.reconnect_attempts - 1:
                    await asyncio.sleep(self._config.reconnect_delay_ms / 1000)

        return False

    async def disconnect(self) -> None:
        """Disconnect session and stop keepalive task."""
        self._connected = False

        if self._ping_task:
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass

        if self._transport:
            await self._transport.disconnect()

        if self._on_disconnect:
            await self._on_disconnect()

    async def send(self, data: dict[str, Any]) -> None:
        """Send message to remote endpoint."""
        if not self._connected or self._transport is None:
            raise ConnectionError("Not connected to remote session")

        payload = dict(data)
        payload.setdefault("session_id", self._session_id)
        payload.setdefault("timestamp", time.time())
        await self._transport.send(payload)

    async def receive(self) -> dict[str, Any]:
        """Receive message from remote endpoint."""
        if not self._connected or self._transport is None:
            raise ConnectionError("Not connected to remote session")
        return await self._transport.receive()

    async def _create_transport(self) -> None:
        headers = {
            **self._config.headers,
            "Content-Type": "application/json",
            "X-Session-ID": self._session_id,
        }
        if self._config.auth_token:
            headers["Authorization"] = f"Bearer {self._config.auth_token}"

        if self._config.transport == RemoteTransportType.WEBSOCKET:
            transport: Transport = WebSocketTransport(
                self._config.remote_url,
                headers,
                self._config.ssl_verify,
            )
        elif self._config.transport == RemoteTransportType.SSE:
            transport = SSETransport(
                self._config.remote_url,
                headers,
                self._config.ssl_verify,
            )
        else:
            raise ValueError(f"Unsupported transport: {self._config.transport}")

        # set_on_data / set_on_close are transport-specific extension hooks
        setattr(transport, "set_on_data", getattr(transport, "set_on_data"))
        getattr(transport, "set_on_data")(self._handle_data)
        getattr(transport, "set_on_close")(self._handle_close)

        self._transport = transport

    async def _handle_data(self, data: str) -> None:
        try:
            message = json.loads(data)
        except json.JSONDecodeError:
            return

        if self._on_message:
            await self._on_message(message)

    async def _handle_close(self) -> None:
        was_connected = self._connected
        self._connected = False

        if was_connected and self._on_disconnect:
            await self._on_disconnect()

        if (
            self._config.reconnect_attempts > 0
            and self._reconnect_count < self._config.reconnect_attempts
        ):
            await asyncio.sleep(self._config.reconnect_delay_ms / 1000)
            await self.connect()

    async def _ping_loop(self) -> None:
        while self._connected:
            try:
                await asyncio.sleep(self._config.ping_interval_ms / 1000)
                if self._connected:
                    await self.send({"type": "ping"})
            except asyncio.CancelledError:
                break


class RemoteIO:
    """Bidirectional remote I/O helper."""

    def __init__(self, remote_url: str, auth_token: Optional[str] = None) -> None:
        self._remote_url = remote_url
        self._auth_token = auth_token
        self._session: Optional[RemoteSession] = None
        self._input_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._reader_task: Optional[asyncio.Task[None]] = None

    @property
    def input_stream(self) -> asyncio.Queue[dict[str, Any]]:
        return self._input_queue

    async def connect(self) -> bool:
        transport = (
            RemoteTransportType.WEBSOCKET
            if self._remote_url.startswith(("ws://", "wss://"))
            else RemoteTransportType.SSE
        )
        config = RemoteSessionConfig(
            remote_url=self._remote_url,
            auth_token=self._auth_token,
            transport=transport,
        )

        self._session = RemoteSession(config)
        self._session.set_on_message(self._handle_message)

        connected = await self._session.connect()
        if connected:
            self._reader_task = asyncio.create_task(self._reader_loop())
        return connected

    async def disconnect(self) -> None:
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass

        if self._session:
            await self._session.disconnect()

    async def send(self, data: dict[str, Any]) -> None:
        if self._session:
            await self._session.send(data)

    async def write(self, data: str) -> None:
        if self._session:
            await self._session.send({"type": "message", "content": data})

    async def _handle_message(self, message: dict[str, Any]) -> None:
        await self._input_queue.put(message)

    async def _reader_loop(self) -> None:
        while self._session and self._session.is_connected:
            try:
                message = await self._session.receive()
                await self._input_queue.put(message)
            except asyncio.CancelledError:
                break
            except Exception:
                break


def get_transport_for_url(
    url: str,
    headers: Optional[dict[str, str]] = None,
) -> Transport:
    """Create transport implementation from URL scheme."""
    if url.startswith(("ws://", "wss://")):
        return WebSocketTransport(url, headers)
    if url.startswith(("http://", "https://")):
        return SSETransport(url, headers)
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
