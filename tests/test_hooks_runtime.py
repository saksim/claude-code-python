"""Runtime tests for hooks manager, hook command, and runtime hook integration."""

from __future__ import annotations

import asyncio
import io
from pathlib import Path
from types import SimpleNamespace

import pytest
from rich.console import Console

import claude_code.services.hooks_manager as hooks_mod
from claude_code.commands.base import CommandContext, CommandResult, CommandType, SimpleCommand
from claude_code.commands.hooks import HooksCommand
from claude_code.engine.query import QueryConfig, QueryEngine, ToolCallResult, ToolUse
from claude_code.repl import REPL, REPLConfig
from claude_code.services.hooks_manager import HookEvent, HooksManager
from claude_code.tools.base import Tool, ToolContext, ToolResult
from claude_code.tools.registry import ToolRegistry


def _context(tmp_path: Path, engine: object | None = None) -> CommandContext:
    return CommandContext(
        working_directory=str(tmp_path),
        console=Console(file=io.StringIO(), force_terminal=False, width=120),
        engine=engine,
        session=None,
        config=None,
    )


class _SpyHooksManager:
    def __init__(self) -> None:
        self.events: list[tuple[HookEvent, dict]] = []

    async def trigger(self, event: HookEvent, context: dict) -> list:
        self.events.append((event, context))
        return []


class _FakeStreamEvent:
    def __init__(self, event_type: str, content: dict | None = None) -> None:
        self.type = event_type
        self.content = content
        self.usage = None
        self.error = None


class _ToolCallingAPIClient:
    def __init__(self) -> None:
        self.calls = 0

    async def create_message_streaming(self, messages, options):
        self.calls += 1
        if self.calls == 1:
            yield _FakeStreamEvent(
                "message",
                {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "tool-1",
                            "name": "echo_tool",
                            "input": {"text": "hook-me"},
                        }
                    ]
                },
            )
        else:
            yield _FakeStreamEvent(
                "message",
                {"content": [{"type": "text", "text": "done"}]},
            )

    async def create_message(self, messages, options):
        return SimpleNamespace(content=[{"type": "text", "text": "done"}])


class _EchoTool(Tool):
    @property
    def name(self) -> str:
        return "echo_tool"

    @property
    def description(self) -> str:
        return "echo text"

    @property
    def input_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {"text": {"type": "string"}},
            "required": ["text"],
        }

    async def execute(
        self,
        input_data: dict,
        context: ToolContext,
        on_progress=None,
    ) -> ToolResult:
        return ToolResult(content=input_data.get("text", ""))


def test_hooks_manager_load_save_parse_round_trip(tmp_path):
    hooks_path = tmp_path / ".claude" / "hooks.json"
    manager = HooksManager(config_path=hooks_path)
    manager.add_hook("pre-hook", HookEvent.BEFORE_TOOL, "echo pre", timeout_seconds=7)
    manager.add_hook(
        "post-disabled",
        HookEvent.AFTER_TOOL,
        "echo post",
        enabled=False,
        timeout_seconds=9,
    )

    reloaded = HooksManager(config_path=hooks_path)
    hooks = reloaded.list_hooks(include_disabled=True)
    by_name = {hook.name: hook for hook in hooks}

    assert set(by_name.keys()) == {"pre-hook", "post-disabled"}
    assert by_name["pre-hook"].event == HookEvent.BEFORE_TOOL
    assert by_name["pre-hook"].timeout_seconds == 7
    assert by_name["post-disabled"].enabled is False
    assert reloaded.get_hooks(HookEvent.AFTER_TOOL) == []


@pytest.mark.asyncio
async def test_hooks_command_roundtrip_with_runtime_manager(tmp_path):
    manager = HooksManager(config_path=tmp_path / ".claude" / "hooks.json")
    command = HooksCommand()
    engine = SimpleNamespace(hooks_manager=manager)
    context = _context(tmp_path, engine=engine)

    add_result = await command.execute("add before_tool echo pre", context)
    assert add_result.success
    assert add_result.content == "Added hook: hook-1"

    list_result = await command.execute("list", context)
    assert list_result.success
    assert "hook-1" in str(list_result.content)
    assert "before_tool" in str(list_result.content)

    remove_result = await command.execute("remove hook-1", context)
    assert remove_result.success
    assert remove_result.content == "Removed hook: hook-1"

    empty_result = await command.execute("list", context)
    assert empty_result.success
    assert empty_result.content == "No hooks configured"


@pytest.mark.asyncio
async def test_query_engine_tool_chain_triggers_before_and_after_hooks():
    registry = ToolRegistry()
    echo_tool = _EchoTool()
    registry.register(echo_tool)

    engine = QueryEngine(
        api_client=_ToolCallingAPIClient(),
        config=QueryConfig(tools=[echo_tool]),
        tool_registry=registry,
    )
    spy_hooks = _SpyHooksManager()
    engine.hooks_manager = spy_hooks

    tool_results: list[ToolCallResult] = []
    async for event in engine.query("run hookable tool"):
        if isinstance(event, ToolCallResult):
            tool_results.append(event)

    assert tool_results
    events = [event for event, _ in spy_hooks.events]
    assert HookEvent.BEFORE_TOOL in events
    assert HookEvent.AFTER_TOOL in events
    before_contexts = [ctx for event, ctx in spy_hooks.events if event == HookEvent.BEFORE_TOOL]
    assert before_contexts
    assert before_contexts[0].get("tool_name") == "echo_tool"
    assert before_contexts[0].get("tool_use_id") == "tool-1"


@pytest.mark.asyncio
async def test_query_engine_error_path_triggers_on_error_hook():
    engine = QueryEngine(api_client=SimpleNamespace(), config=QueryConfig())
    spy_hooks = _SpyHooksManager()
    engine.hooks_manager = spy_hooks

    result = await engine._execute_tool(ToolUse(id="tool-x", name="missing_tool", input={}))

    assert result.result.is_error is True
    events = [event for event, _ in spy_hooks.events]
    assert HookEvent.BEFORE_TOOL in events
    assert HookEvent.AFTER_TOOL in events
    assert HookEvent.ON_ERROR in events


@pytest.mark.asyncio
async def test_repl_command_hooks_trigger_before_after_and_on_error(tmp_path):
    spy_hooks = _SpyHooksManager()
    engine = SimpleNamespace(
        hooks_manager=spy_hooks,
        config=SimpleNamespace(session_id="session-1", model="claude-test-model"),
    )
    repl = REPL(
        engine=engine,
        config=REPLConfig(working_directory=str(tmp_path), welcome_message=False),
    )

    async def _ok_handler(args: str, context: CommandContext) -> CommandResult:
        return CommandResult(success=True, content=f"ok:{args}")

    async def _fail_handler(args: str, context: CommandContext) -> CommandResult:
        return CommandResult(success=False, error="intentional-failure")

    async def _boom_handler(args: str, context: CommandContext) -> CommandResult:
        raise RuntimeError("command exploded")

    repl._commands = {
        "ok": SimpleCommand(
            name="ok",
            description="ok command",
            handler=_ok_handler,
            command_type=CommandType.LOCAL,
        ),
        "fail": SimpleCommand(
            name="fail",
            description="fail command",
            handler=_fail_handler,
            command_type=CommandType.LOCAL,
        ),
        "boom": SimpleCommand(
            name="boom",
            description="boom command",
            handler=_boom_handler,
            command_type=CommandType.LOCAL,
        ),
    }

    assert await repl.run_command("/ok payload") is True
    assert await repl.run_command("/fail") is True
    assert await repl.run_command("/boom") is True

    events = [event for event, _ in spy_hooks.events]
    assert events.count(HookEvent.BEFORE_COMMAND) >= 3
    assert events.count(HookEvent.AFTER_COMMAND) >= 2
    assert events.count(HookEvent.ON_ERROR) >= 2
    error_contexts = [ctx for event, ctx in spy_hooks.events if event == HookEvent.ON_ERROR]
    assert any(ctx.get("command_name") == "fail" for ctx in error_contexts)
    assert any(ctx.get("command_name") == "boom" for ctx in error_contexts)


@pytest.mark.asyncio
async def test_hooks_manager_timeout_failure_and_disabled_paths(monkeypatch, tmp_path):
    manager = HooksManager(config_path=tmp_path / ".claude" / "hooks.json")
    manager.add_hook("timeout-hook", HookEvent.BEFORE_TOOL, "timeout-cmd", timeout_seconds=1)
    manager.add_hook("failure-hook", HookEvent.BEFORE_TOOL, "failure-cmd")
    manager.add_hook("disabled-hook", HookEvent.BEFORE_TOOL, "disabled-cmd", enabled=False)

    calls: list[str] = []
    wait_for_calls = {"count": 0}

    class _FakeProcess:
        def __init__(self, command: str):
            self.command = command
            self.returncode = 0 if "timeout-cmd" in command else 1

        async def communicate(self):
            if "failure-cmd" in self.command:
                return b"", b"hook command failed"
            return b"ok", b""

    async def _fake_create_subprocess_shell(command, **kwargs):
        calls.append(command)
        return _FakeProcess(command)

    async def _fake_wait_for(awaitable, timeout):
        wait_for_calls["count"] += 1
        if wait_for_calls["count"] == 1:
            close = getattr(awaitable, "close", None)
            if callable(close):
                close()
            raise asyncio.TimeoutError()
        return await awaitable

    monkeypatch.setattr(hooks_mod.asyncio, "create_subprocess_shell", _fake_create_subprocess_shell)
    monkeypatch.setattr(hooks_mod.asyncio, "wait_for", _fake_wait_for)

    results = await manager.trigger(HookEvent.BEFORE_TOOL, {"tool_name": "read"})

    assert len(results) == 2
    assert any("Timeout after 1s" in (item.error or "") for item in results)
    assert any("hook command failed" in (item.error or "") for item in results)
    assert all("disabled-cmd" not in command for command in calls)
