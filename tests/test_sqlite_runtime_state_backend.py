"""Runtime tests for P1-03 SQLite state backend contracts."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import SimpleNamespace

import pytest

import claude_code.main as main_mod
from claude_code.engine.query import QueryConfig, QueryEngine
from claude_code.engine.session import SessionManager, SQLiteSessionStore
from claude_code.services.event_journal import (
    EVENT_JOURNAL_SCHEMA_KEY,
    EVENT_JOURNAL_SCHEMA_VERSION,
    SQLiteEventJournal,
)
from claude_code.tasks.factory import create_runtime_repository
from claude_code.tasks.repository import (
    RUNTIME_TASKS_SCHEMA_KEY,
    RUNTIME_TASKS_SCHEMA_VERSION,
    SQLiteRuntimeTaskRepository,
)
from claude_code.tasks.types import BashTask, TaskResult, TaskStatus
from claude_code.tools.registry import ToolRegistry


class _SingleTurnApiClient:
    async def create_message_streaming(self, messages, options):
        yield SimpleNamespace(
            type="message",
            content={"content": [{"type": "text", "text": "ack"}]},
            usage=None,
            error=None,
        )

    async def create_message(self, messages, options):
        return SimpleNamespace(content=[{"type": "text", "text": "ack"}])


def test_sqlite_runtime_repository_init_and_crud_contract(tmp_path: Path):
    repo = create_runtime_repository(tmp_path, "sqlite")
    assert isinstance(repo, SQLiteRuntimeTaskRepository)

    task = BashTask(id="task-sqlite-crud", command="echo sqlite", status=TaskStatus.COMPLETED)
    task.result = TaskResult(code=0, stdout="ok", stderr="")
    repo.upsert_task(task)

    loaded = repo.get_task_record(task.id)
    assert loaded is not None
    assert loaded["status"] == "completed"
    assert loaded["result"]["stdout"] == "ok"

    listed = repo.list_task_records()
    assert any(item["id"] == task.id for item in listed)


def test_sqlite_runtime_repository_schema_version_guard(tmp_path: Path):
    repo = create_runtime_repository(tmp_path, "sqlite")
    assert isinstance(repo, SQLiteRuntimeTaskRepository)

    with sqlite3.connect(repo.db_path, timeout=5.0) as conn:
        conn.execute(
            "UPDATE runtime_tasks_metadata SET value = ? WHERE key = ?",
            (str(RUNTIME_TASKS_SCHEMA_VERSION + 1), RUNTIME_TASKS_SCHEMA_KEY),
        )

    with pytest.raises(RuntimeError, match="newer than this binary"):
        create_runtime_repository(tmp_path, "sqlite")


def test_sqlite_event_journal_schema_version_guard(tmp_path: Path):
    db_path = tmp_path / "runtime_state.db"
    journal = SQLiteEventJournal(db_path)
    journal.append_event(event_type="query.started", payload={"input": "x"})

    with sqlite3.connect(db_path, timeout=5.0) as conn:
        conn.execute(
            "UPDATE journal_metadata SET value = ? WHERE key = ?",
            (str(EVENT_JOURNAL_SCHEMA_VERSION + 1), EVENT_JOURNAL_SCHEMA_KEY),
        )

    with pytest.raises(RuntimeError, match="newer than this binary"):
        SQLiteEventJournal(db_path)


def test_sqlite_session_store_persist_and_load(tmp_path: Path):
    db_path = tmp_path / "runtime_state.db"
    session_store = SQLiteSessionStore(db_path)
    manager = SessionManager.from_store(session_store)

    session = manager.create_session()
    session.add_user_message("hello")
    session.add_assistant_message("world")
    session.save()

    reloaded = manager.load_session(session.id)
    assert reloaded is not None
    assert len(reloaded.messages) == 2
    assert reloaded.messages[0].role == "user"
    assert reloaded.messages[1].role == "assistant"


@pytest.mark.asyncio
async def test_query_chain_with_sqlite_event_journal_and_session_store(tmp_path: Path):
    db_path = tmp_path / "runtime_state.db"
    session_store = SQLiteSessionStore(db_path)
    manager = SessionManager.from_store(session_store)
    session = manager.create_session()

    journal = SQLiteEventJournal(db_path)
    engine = QueryEngine(
        api_client=_SingleTurnApiClient(),
        config=QueryConfig(session_id=session.id, working_directory=str(tmp_path)),
        tool_registry=ToolRegistry(lazy=False),
    )
    engine.session_manager = manager
    engine.event_journal = journal

    async for _ in engine.query("hello sqlite"):
        pass

    queried = journal.query_events(session_id=session.id)
    event_types = [item.event_type for item in queried]
    assert "query.started" in event_types
    assert "message.user" in event_types
    assert "message.assistant" in event_types
    assert "query.completed" in event_types


def test_create_runtime_wires_sqlite_state_backend(monkeypatch):
    class _FakeSession:
        def __init__(self):
            self.id = "session-xyz"
            self.metadata = type(
                "_Metadata",
                (),
                {"working_directory": "D:/init", "model": "claude-init"},
            )()

    class _FakeSessionManager:
        def __init__(self):
            self.session = _FakeSession()

        @classmethod
        def from_store(cls, store):
            return cls()

        def ensure_current_session(self):
            return self.session

    class _FakeQueryEngine:
        def __init__(self, api_client, config, tool_registry):
            self.api_client = api_client
            self.config = config
            self.tool_registry = tool_registry

    captured = {}
    fake_api = object()
    fake_registry = object()
    fake_history = object()
    fake_task_manager = object()
    fake_hooks = object()
    fake_memory = object()
    fake_event_journal = object()
    fake_application = object()

    monkeypatch.setattr(main_mod, "get_config", lambda: main_mod.Config(model="claude-runtime"))
    monkeypatch.setattr(main_mod, "setup_api_client", lambda app_config=None: fake_api)
    monkeypatch.setattr(main_mod, "create_default_registry", lambda: fake_registry)
    monkeypatch.setattr(main_mod, "QueryEngine", _FakeQueryEngine)
    monkeypatch.setattr(main_mod, "SessionManager", _FakeSessionManager)
    monkeypatch.setattr(main_mod, "SQLiteSessionStore", lambda db_path=None: object())
    monkeypatch.setattr(main_mod, "HistoryManager", lambda storage_path=None: fake_history)
    monkeypatch.setattr(main_mod, "SQLiteEventJournal", lambda db_path=None: fake_event_journal)

    def _fake_task_manager_factory(config, event_journal):
        captured["runtime_backend"] = config.runtime_backend
        captured["event_journal"] = event_journal
        return fake_task_manager

    monkeypatch.setattr(main_mod, "create_task_manager_with_event_journal", _fake_task_manager_factory)
    monkeypatch.setattr(main_mod, "HooksManager", lambda config_path=None: fake_hooks)
    monkeypatch.setattr(main_mod, "get_memory", lambda: fake_memory)
    monkeypatch.setattr(main_mod, "_create_application", lambda app_config: fake_application)

    runtime = main_mod.create_runtime(model="claude-custom", working_dir="D:/runtime")

    assert runtime.event_journal is fake_event_journal
    assert runtime.query_engine.event_journal is fake_event_journal
    assert captured["runtime_backend"] == "sqlite"
    assert captured["event_journal"] is fake_event_journal
