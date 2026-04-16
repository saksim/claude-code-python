"""Runtime flow tests for QueryEngine tool orchestration."""

from __future__ import annotations

import asyncio
import pytest

from claude_code.engine.query import QueryConfig, QueryEngine, ToolCallResult
from claude_code.tools.base import Tool, ToolContext, ToolResult
from claude_code.tools.registry import ToolRegistry
from claude_code.permissions import PermissionMode


class _FakeStreamEvent:
    def __init__(self, event_type: str, content: dict | None = None) -> None:
        self.type = event_type
        self.content = content
        self.usage = None
        self.error = None


class _FakeAPIClient:
    """Simple deterministic API client for multi-turn tool flow tests."""

    def __init__(self, tool_name: str) -> None:
        self._call_count = 0
        self._tool_name = tool_name

    async def create_message_streaming(self, messages, options):
        self._call_count += 1
        if self._call_count == 1:
            yield _FakeStreamEvent(
                "message",
                {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "tool-1",
                            "name": self._tool_name,
                            "input": {"text": "hello"},
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
        class _Response:
            content = [{"type": "text", "text": "done"}]

        return _Response()


class _FallbackAPIClient:
    """Streaming path yields no final message; engine must fallback to create_message()."""

    async def create_message_streaming(self, messages, options):
        if False:
            yield None

    async def create_message(self, messages, options):
        class _Response:
            content = [{"type": "text", "text": "fallback-ok"}]

        return _Response()


class _EchoTool(Tool):
    @property
    def name(self) -> str:
        return "echo_tool"

    @property
    def description(self) -> str:
        return "echo input text"

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


class _WriteTool(Tool):
    @property
    def name(self) -> str:
        return "write"

    @property
    def description(self) -> str:
        return "mock write tool"

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
        return ToolResult(content="should-not-run")


class _SleepToolA(Tool):
    @property
    def name(self) -> str:
        return "sleep_a"

    @property
    def description(self) -> str:
        return "sleep tool a"

    @property
    def input_schema(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    def is_concurrency_safe(self) -> bool:
        return True

    async def execute(self, input_data: dict, context: ToolContext, on_progress=None) -> ToolResult:
        await asyncio.sleep(0.1)
        return ToolResult(content="a")


class _SleepToolB(Tool):
    @property
    def name(self) -> str:
        return "sleep_b"

    @property
    def description(self) -> str:
        return "sleep tool b"

    @property
    def input_schema(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    def is_concurrency_safe(self) -> bool:
        return True

    async def execute(self, input_data: dict, context: ToolContext, on_progress=None) -> ToolResult:
        await asyncio.sleep(0.1)
        return ToolResult(content="b")


def test_query_engine_populates_tools_from_registry_when_config_empty():
    registry = ToolRegistry()
    registry.register(_EchoTool())

    engine = QueryEngine(
        api_client=_FakeAPIClient("echo_tool"),
        config=QueryConfig(),
        tool_registry=registry,
    )

    assert any(tool.name == "echo_tool" for tool in engine.config.tools)


def test_query_engine_skips_failing_lazy_tools_when_populating_config():
    registry = ToolRegistry()
    registry.register_lazy("broken", lambda: (_ for _ in ()).throw(ImportError("missing dep")))
    registry.register(_EchoTool())

    engine = QueryEngine(
        api_client=_FakeAPIClient("echo_tool"),
        config=QueryConfig(),
        tool_registry=registry,
    )

    names = [tool.name for tool in engine.config.tools]
    assert "echo_tool" in names
    assert "broken" not in names


@pytest.mark.asyncio
async def test_query_engine_executes_tool_use_blocks():
    registry = ToolRegistry()
    registry.register(_EchoTool())
    engine = QueryEngine(
        api_client=_FakeAPIClient("echo_tool"),
        config=QueryConfig(tools=[_EchoTool()]),
        tool_registry=registry,
    )

    tool_results: list[ToolCallResult] = []
    async for event in engine.query("run tool"):
        if isinstance(event, ToolCallResult):
            tool_results.append(event)

    assert tool_results
    assert tool_results[0].result.is_error is False
    assert tool_results[0].result.content == "hello"


@pytest.mark.asyncio
async def test_query_engine_enforces_plan_mode_permissions():
    registry = ToolRegistry()
    registry.register(_WriteTool())
    engine = QueryEngine(
        api_client=_FakeAPIClient("write"),
        config=QueryConfig(
            tools=[_WriteTool()],
            permission_mode="plan",
        ),
        tool_registry=registry,
    )

    tool_results: list[ToolCallResult] = []
    async for event in engine.query("attempt write"):
        if isinstance(event, ToolCallResult):
            tool_results.append(event)

    assert tool_results
    assert tool_results[0].result.is_error is True
    assert "Permission denied" in str(tool_results[0].result.content)


def test_query_engine_get_last_message_handles_content_blocks():
    registry = ToolRegistry()
    registry.register(_EchoTool())
    engine = QueryEngine(
        api_client=_FakeAPIClient("echo_tool"),
        config=QueryConfig(tools=[_EchoTool()]),
        tool_registry=registry,
    )
    engine.messages.append(
        type(
            "_Msg",
            (),
            {
                "role": "assistant",
                "content": [{"type": "text", "text": "abc"}, {"type": "tool_use", "name": "x"}],
            },
        )()
    )
    assert engine.get_last_message() == "abc"


def test_set_permission_mode_updates_engine_config():
    registry = ToolRegistry()
    registry.register(_EchoTool())
    engine = QueryEngine(
        api_client=_FakeAPIClient("echo_tool"),
        config=QueryConfig(tools=[_EchoTool()], permission_mode="default"),
        tool_registry=registry,
    )

    engine.set_permission_mode(PermissionMode.PLAN)
    assert engine.config.permission_mode == "plan"


@pytest.mark.asyncio
async def test_query_engine_falls_back_to_non_streaming_when_stream_has_no_final_message():
    registry = ToolRegistry()
    registry.register(_EchoTool())
    engine = QueryEngine(
        api_client=_FallbackAPIClient(),
        config=QueryConfig(tools=[_EchoTool()]),
        tool_registry=registry,
    )

    assistant_texts: list[str] = []
    async for event in engine.query("hello"):
        if hasattr(event, "role") and getattr(event, "role", None) == "assistant":
            content = getattr(event, "content", "")
            if isinstance(content, str):
                assistant_texts.append(content)
            elif isinstance(content, list):
                assistant_texts.extend(
                    str(block.get("text", ""))
                    for block in content
                    if isinstance(block, dict) and block.get("type") == "text"
                )

    assert "fallback-ok" in "".join(assistant_texts)


@pytest.mark.asyncio
async def test_query_engine_executes_multiple_safe_tools_in_parallel():
    class _TwoToolAPIClient:
        def __init__(self):
            self.calls = 0

        async def create_message_streaming(self, messages, options):
            self.calls += 1
            if self.calls == 1:
                yield _FakeStreamEvent(
                    "message",
                    {
                        "content": [
                            {"type": "tool_use", "id": "a1", "name": "sleep_a", "input": {}},
                            {"type": "tool_use", "id": "b1", "name": "sleep_b", "input": {}},
                        ]
                    },
                )
            else:
                yield _FakeStreamEvent("message", {"content": [{"type": "text", "text": "done"}]})

        async def create_message(self, messages, options):
            class _Response:
                content = [{"type": "text", "text": "done"}]

            return _Response()

    registry = ToolRegistry()
    tool_a = _SleepToolA()
    tool_b = _SleepToolB()
    registry.register(tool_a)
    registry.register(tool_b)
    engine = QueryEngine(
        api_client=_TwoToolAPIClient(),
        config=QueryConfig(tools=[tool_a, tool_b]),
        tool_registry=registry,
    )

    start = asyncio.get_event_loop().time()
    async for _ in engine.query("run two tools"):
        pass
    elapsed = asyncio.get_event_loop().time() - start

    # Sequential execution would be roughly >= 0.2s; parallel should be clearly lower.
    assert elapsed < 0.19
