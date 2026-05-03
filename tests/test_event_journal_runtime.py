"""Runtime tests for P1-02 event journal contracts."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from claude_code.engine.query import QueryConfig, QueryEngine, ToolCallResult
from claude_code.services.event_journal import (
    EVENT_JOURNAL_SCHEMA_KEY,
    EVENT_JOURNAL_SCHEMA_VERSION,
    EventJournal,
    EventJournalEntry,
    SQLiteEventJournal,
)
from claude_code.tasks.manager import TaskEvent, TaskManager
from claude_code.tasks.queue import InMemoryTaskQueue
from claude_code.tasks.types import TaskResult
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
                            "input": {"text": "hello"},
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


def test_event_journal_entry_schema_versioning_and_validation():
    entry = EventJournalEntry.from_dict(
        {
            "event_id": "evt-1",
            "version": EVENT_JOURNAL_SCHEMA_VERSION,
            "event_type": "query.started",
            "sequence": 1,
            "timestamp": 1700000000.0,
            "payload": {"x": 1},
            "metadata": {"m": 2},
        }
    )
    assert entry.version == EVENT_JOURNAL_SCHEMA_VERSION
    assert entry.event_type == "query.started"

    with pytest.raises(ValueError):
        EventJournalEntry.from_dict(
            {
                "event_id": "evt-2",
                "version": 0,
                "event_type": "query.started",
                "sequence": 2,
                "timestamp": 1700000001.0,
                "payload": {},
                "metadata": {},
            }
        )


def test_event_journal_writer_reader_and_partial_corruption_recovery(tmp_path: Path):
    journal = EventJournal(tmp_path / "event_journal.jsonl")
    first = journal.append_event(event_type="query.started", payload={"input": "hello"}, session_id="s1")
    second = journal.append_event(event_type="tool.completed", payload={"tool": "echo"}, session_id="s1")
    assert second.sequence == first.sequence + 1

    # Simulate corrupted trailing line.
    with open(journal.storage_path, "a", encoding="utf-8") as handle:
        handle.write("{invalid-json")
        handle.write("\n")

    events = journal.query_events(session_id="s1")
    assert len(events) == 2
    diagnostics = journal.get_diagnostics()
    assert diagnostics["parse_errors"] >= 1


@pytest.mark.asyncio
async def test_query_tool_task_event_chain_records_into_journal(tmp_path: Path):
    journal = EventJournal(tmp_path / "event_journal.jsonl")
    registry = ToolRegistry(lazy=False)
    registry.register(_EchoTool())
    engine = QueryEngine(
        api_client=_TwoTurnToolApiClient("echo_tool"),
        config=QueryConfig(tools=[_EchoTool()], session_id="session-chain", working_directory=str(tmp_path)),
        tool_registry=registry,
    )
    engine.event_journal = journal
    engine.conversation_id = "conversation-chain"

    tool_results: list[ToolCallResult] = []
    async for item in engine.query("run"):
        if isinstance(item, ToolCallResult):
            tool_results.append(item)
    assert tool_results

    manager = TaskManager(task_queue=InMemoryTaskQueue(), event_journal=journal)
    task = await manager.create_bash_task("echo hi")

    async def _ok_executor(_task):
        return TaskResult(code=0, stdout="ok")

    await manager.start_task(task.id, executor=_ok_executor)
    await manager.wait_for_task(task.id, timeout=2.0)

    events = journal.replay_events(session_id="session-chain")
    event_types = [entry.event_type for entry in events]
    assert "query.started" in event_types
    assert "message.user" in event_types
    assert "tool.started" in event_types
    assert "tool.completed" in event_types

    task_events = journal.query_events(event_types=["task.started", "task.completed"])
    task_event_types = [entry.event_type for entry in task_events]
    assert "task.started" in task_event_types
    assert "task.completed" in task_event_types


def test_task_event_serialization_contract():
    event = TaskEvent(task_id="task-1", event_type="started", data={"attempt": 1})
    assert event.task_id == "task-1"
    assert event.event_type == "started"
    assert event.data["attempt"] == 1


def test_sqlite_event_journal_schema_and_query_replay(tmp_path: Path):
    journal = SQLiteEventJournal(tmp_path / "runtime_state.db")
    first = journal.append_event(
        event_type="query.started",
        payload={"input": "hello"},
        session_id="s-sqlite",
    )
    second = journal.append_event(
        event_type="tool.completed",
        payload={"tool": "echo"},
        session_id="s-sqlite",
    )
    assert second.sequence == first.sequence + 1

    queried = journal.query_events(
        session_id="s-sqlite",
        event_types=["tool.completed"],
    )
    assert len(queried) == 1
    assert queried[0].event_type == "tool.completed"

    replayed = journal.replay_events(session_id="s-sqlite")
    assert [item.sequence for item in replayed] == [first.sequence, second.sequence]

    diagnostics = journal.get_diagnostics()
    assert diagnostics["backend"] == "sqlite"
    assert diagnostics["events_count"] >= 2


def test_sqlite_event_journal_schema_version_guard(tmp_path: Path):
    db_path = tmp_path / "runtime_state.db"
    journal = SQLiteEventJournal(db_path)
    journal.append_event(event_type="query.started", payload={"v": 1})

    import sqlite3

    with sqlite3.connect(db_path, timeout=5.0) as conn:
        conn.execute(
            "UPDATE journal_metadata SET value = ? WHERE key = ?",
            (str(EVENT_JOURNAL_SCHEMA_VERSION + 1), EVENT_JOURNAL_SCHEMA_KEY),
        )

    with pytest.raises(RuntimeError, match="newer than this binary"):
        SQLiteEventJournal(db_path)
