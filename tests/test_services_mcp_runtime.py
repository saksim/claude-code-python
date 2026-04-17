"""Runtime tests for MCP protocol/client minimal flow."""

from __future__ import annotations

import asyncio

import pytest

from claude_code.services.mcp.client import (
    MCPClient,
    MCPConnectionConfig,
    MCPConnectionState,
    MCPProtocol,
    MCPTransport,
    MCPTransportType,
)


@pytest.mark.asyncio
async def test_mcp_protocol_send_request_uses_sender_and_resolves_response():
    protocol = MCPProtocol()

    async def _sender(message):
        protocol.handle_response(
            {
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {"ok": True, "method": message["method"]},
            }
        )

    protocol.set_sender(_sender)
    result = await protocol.send_request("ping")

    assert result == {"ok": True, "method": "ping"}


class _FakeTransport(MCPTransport):
    def __init__(self) -> None:
        self._queue: asyncio.Queue = asyncio.Queue()
        self.connected = False
        self.disconnected = False

    async def connect(self) -> None:
        self.connected = True

    async def disconnect(self) -> None:
        self.disconnected = True

    async def send(self, message: dict) -> dict:
        method = message.get("method")
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": message["id"], "result": {"capabilities": {}}}
        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {"tools": [{"name": "demo", "description": "d", "inputSchema": {}}]},
            }
        if method == "resources/list":
            return {
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {"resources": [{"uri": "file://a", "name": "a"}]},
            }
        if method == "tools/call":
            return {
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {"ok": True},
            }
        if method == "resources/read":
            return {
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {"contents": [{"text": "abc"}]},
            }
        return {"jsonrpc": "2.0", "id": message["id"], "result": {}}

    async def receive(self) -> dict:
        return await self._queue.get()

    async def send_request(self, method: str, params: dict | None = None) -> dict:
        raise RuntimeError("unused in this test")


@pytest.mark.asyncio
async def test_mcp_client_connects_and_loads_tools_with_transport_sender(monkeypatch):
    config = MCPConnectionConfig(
        server_name="demo",
        command="unused",
        transport=MCPTransportType.STDIO,
    )
    client = MCPClient(config)
    fake_transport = _FakeTransport()
    monkeypatch.setattr(client, "_create_transport", lambda: fake_transport)

    await client.connect()
    try:
        assert client.state == MCPConnectionState.CONNECTED
        assert len(client.tools) == 1
        assert client.tools[0].name == "demo"
        assert len(client.resources) == 1

        tool_result = await client.call_tool("demo", {"x": 1})
        assert tool_result == {"ok": True}
        resource_result = await client.read_resource("file://a")
        assert resource_result == {"contents": [{"text": "abc"}]}
    finally:
        await client.disconnect()

    assert fake_transport.connected
    assert fake_transport.disconnected

