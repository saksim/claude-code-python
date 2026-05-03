"""Runtime tests for P1-05 hook/permission/audit convergence."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from claude_code.engine.query import QueryConfig, QueryEngine, ToolCallResult
from claude_code.services.event_journal import EventJournal
from claude_code.services.hooks_manager import HookEvent, HookResult
from claude_code.tools.base import Tool, ToolContext, ToolResult
from claude_code.tools.registry import ToolRegistry


class _FakeStreamEvent:
    def __init__(self, event_type: str, content: dict | None = None) -> None:
        self.type = event_type
        self.content = content
        self.usage = None
        self.error = None


class _TwoTurnToolApiClient:
    def __init__(self, tool_name: str) -> None:
        self._tool_name = tool_name
        self._count = 0

    async def create_message_streaming(self, messages, options):
        self._count += 1
        if self._count == 1:
            yield _FakeStreamEvent(
                "message",
                {
                    "content": [
                        {
                            "type": "tool_use",
                            "id": "tool-1",
                            "name": self._tool_name,
                            "input": {"text": "audit-me"},
                        }
                    ]
                },
            )
        else:
            yield _FakeStreamEvent("message", {"content": [{"type": "text", "text": "done"}]})

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
        return ToolResult(content=input_data.get("text", ""), is_error=False, tool_use_id="")


class _WriteProbeTool(Tool):
    def __init__(self) -> None:
        self.executed = False

    @property
    def name(self) -> str:
        return "write"

    @property
    def description(self) -> str:
        return "write probe"

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
        self.executed = True
        return ToolResult(content="write-executed", is_error=False, tool_use_id="")


class _SpyHooksManager:
    def __init__(self) -> None:
        self.calls: list[tuple[HookEvent, dict]] = []

    async def trigger(self, event: HookEvent, context: dict) -> list[HookResult]:
        self.calls.append((event, context))
        return [
            HookResult(
                hook_name=f"{event.value}-hook",
                success=True,
                output=f"{event.value}-ok",
                duration_ms=1.0,
            )
        ]


@pytest.mark.asyncio
async def test_permission_and_hook_audit_events_on_success_path(tmp_path: Path):
    registry = ToolRegistry(lazy=False)
    tool = _EchoTool()
    registry.register(tool)

    journal = EventJournal(tmp_path / "event_journal.jsonl")
    hooks = _SpyHooksManager()
    engine = QueryEngine(
        api_client=_TwoTurnToolApiClient("echo_tool"),
        config=QueryConfig(
            tools=[tool],
            session_id="session-success",
            working_directory=str(tmp_path),
            permission_mode="default",
        ),
        tool_registry=registry,
    )
    engine.event_journal = journal
    engine.hooks_manager = hooks

    tool_results: list[ToolCallResult] = []
    async for item in engine.query("run success path"):
        if isinstance(item, ToolCallResult):
            tool_results.append(item)
    assert tool_results
    assert tool_results[0].result.is_error is False

    permission_events = journal.query_events(
        session_id="session-success",
        event_types=["permission.requested", "permission.decided"],
        limit=20,
    )
    assert [event.event_type for event in permission_events] == [
        "permission.requested",
        "permission.decided",
    ]
    decision_payload = permission_events[1].payload
    assert decision_payload.get("allowed") is True
    assert decision_payload.get("decision_reason") in {"allow_name", "default_allow"}

    hook_events = journal.query_events(
        session_id="session-success",
        event_types=["hook.execution"],
        limit=20,
    )
    hook_kinds = [entry.payload.get("hook_event") for entry in hook_events]
    assert HookEvent.BEFORE_TOOL.value in hook_kinds
    assert HookEvent.AFTER_TOOL.value in hook_kinds
    assert HookEvent.ON_ERROR.value not in hook_kinds
    first_results = hook_events[0].payload.get("results", [])
    assert first_results
    assert first_results[0]["hook_name"].endswith("-hook")
    assert first_results[0]["success"] is True


@pytest.mark.asyncio
async def test_permission_denied_path_emits_decision_and_error_hook_audit(tmp_path: Path):
    registry = ToolRegistry(lazy=False)
    tool = _WriteProbeTool()
    registry.register(tool)

    journal = EventJournal(tmp_path / "event_journal.jsonl")
    hooks = _SpyHooksManager()
    engine = QueryEngine(
        api_client=_TwoTurnToolApiClient("write"),
        config=QueryConfig(
            tools=[tool],
            session_id="session-denied",
            working_directory=str(tmp_path),
            permission_mode="plan",
        ),
        tool_registry=registry,
    )
    engine.event_journal = journal
    engine.hooks_manager = hooks

    tool_results: list[ToolCallResult] = []
    async for item in engine.query("attempt denied write"):
        if isinstance(item, ToolCallResult):
            tool_results.append(item)
    assert tool_results
    assert tool_results[0].result.is_error is True
    assert "Permission denied" in str(tool_results[0].result.content)
    assert tool.executed is False

    decided_events = journal.query_events(
        session_id="session-denied",
        event_types=["permission.decided"],
        limit=20,
    )
    assert len(decided_events) == 1
    decided_payload = decided_events[0].payload
    assert decided_payload.get("allowed") is False
    assert decided_payload.get("decision_reason") == "default_deny"

    hook_events = journal.query_events(
        session_id="session-denied",
        event_types=["hook.execution"],
        limit=20,
    )
    hook_kinds = [entry.payload.get("hook_event") for entry in hook_events]
    assert HookEvent.BEFORE_TOOL.value in hook_kinds
    assert HookEvent.AFTER_TOOL.value in hook_kinds
    assert HookEvent.ON_ERROR.value in hook_kinds

    failed_events = journal.query_events(
        session_id="session-denied",
        event_types=["tool.failed"],
        limit=20,
    )
    assert failed_events
    assert failed_events[0].payload.get("is_error") is True
