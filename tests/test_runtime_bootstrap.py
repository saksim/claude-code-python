"""Runtime bootstrap tests for unified entrypoint assembly."""

from __future__ import annotations

import pytest

import claude_code.main as main_mod
from claude_code.mcp.server import create_mcp_server


@pytest.mark.asyncio
async def test_runtime_entrypoints_reuse_create_engine(monkeypatch):
    calls: list[tuple[str | None, str | None]] = []

    class _FakeEngine:
        async def query(self, user_input: str):
            yield {"type": "text", "content": "ok"}

    class _FakeREPL:
        def __init__(self, engine, config):
            self.engine = engine
            self.config = config

        async def run(self):
            return None

    class _FakePipeMode:
        def __init__(self, engine):
            self.engine = engine

        async def run(self):
            return 0

    def _fake_create_engine(model=None, working_dir=None):
        calls.append((model, working_dir))
        return _FakeEngine()

    monkeypatch.setattr(main_mod, "create_engine", _fake_create_engine)
    monkeypatch.setattr(main_mod, "REPL", _FakeREPL)
    monkeypatch.setattr(main_mod, "PipeMode", _FakePipeMode)
    monkeypatch.setattr(main_mod.os, "getcwd", lambda: "D:/workspace")

    await main_mod.run_repl(model="claude-a")
    await main_mod.run_pipe_mode(model="claude-b")
    await main_mod.run_single_query(query="hello", model="claude-c")

    assert calls == [
        ("claude-a", "D:/workspace"),
        ("claude-b", "D:/workspace"),
        ("claude-c", "D:/workspace"),
    ]


@pytest.mark.asyncio
async def test_create_mcp_server_uses_injected_tool_registry():
    sentinel_registry = object()
    server = await create_mcp_server(
        working_directory="D:/workspace",
        server_name="runtime-test",
        tool_registry=sentinel_registry,
    )

    assert server._tool_registry is sentinel_registry
