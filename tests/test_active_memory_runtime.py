"""Runtime tests for P1-04 active memory integration."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import claude_code.main as main_mod
from claude_code.engine.query import QueryConfig, QueryEngine
from claude_code.services.event_journal import EventJournal
from claude_code.services.memory_service import MemoryEntry, SessionMemory


class _SingleTurnApiClient:
    """Deterministic API client for query-engine runtime tests."""

    async def create_message_streaming(self, messages, options):
        yield SimpleNamespace(
            type="message",
            content={"content": [{"type": "text", "text": "ack"}]},
            usage=None,
            error=None,
        )

    async def create_message(self, messages, options):
        return SimpleNamespace(content=[{"type": "text", "text": "ack"}])


@pytest.mark.asyncio
async def test_query_engine_records_memory_hit_event(tmp_path):
    memory = SessionMemory(storage_dir=tmp_path / "memory")
    await memory.set_scoped(
        "project",
        "architecture",
        "sqlite runtime backend",
        working_directory=tmp_path,
    )
    journal = EventJournal(tmp_path / "events.jsonl")
    engine = QueryEngine(api_client=_SingleTurnApiClient(), config=QueryConfig())
    engine.memory = memory
    engine.event_journal = journal
    engine.config.working_directory = str(tmp_path)
    engine.config.memory_scope = "project"

    async for _ in engine.query("please explain sqlite architecture"):
        pass

    events = journal.query_events(event_types=["memory.hit"], limit=20)
    assert events
    payload = events[0].payload
    assert payload.get("scope") == "project"
    assert "architecture" in payload.get("matched_keys", [])


def test_build_system_prompt_includes_scoped_memory_snapshot(monkeypatch, tmp_path):
    memory = SessionMemory(storage_dir=tmp_path / "memory")
    memory._memory.clear()  # type: ignore[attr-defined]  # isolate test from previous state
    key = SessionMemory._scoped_key("project", "roadmap", working_directory=tmp_path)
    memory._memory[key] = MemoryEntry(key=key, value="P1-04 active memory")  # type: ignore[attr-defined]

    monkeypatch.setattr(main_mod, "get_memory", lambda: memory)
    monkeypatch.setenv("CLAUDE_MEMORY_SCOPE", "project")

    prompt = main_mod.build_system_prompt(str(tmp_path))

    assert "Active memory snapshot:" in prompt
    assert "scope: project" in prompt
    assert "roadmap: P1-04 active memory" in prompt


def test_create_runtime_propagates_memory_scope_from_env(monkeypatch, tmp_path):
    captured = {}

    class _FakeSession:
        def __init__(self):
            self.id = "session-xyz"
            self.metadata = type(
                "_Metadata",
                (),
                {"working_directory": "D:/initial", "model": "claude-initial"},
            )()

    class _FakeSessionManager:
        @classmethod
        def from_store(cls, store):
            return cls()

        def ensure_current_session(self):
            return _FakeSession()

    class _FakeQueryEngine:
        def __init__(self, api_client, config, tool_registry):
            captured["config"] = config
            self.api_client = api_client
            self.config = config
            self.tool_registry = tool_registry

    monkeypatch.setenv("CLAUDE_MEMORY_SCOPE", "user")
    monkeypatch.setattr(main_mod, "get_config", lambda: main_mod.Config(model="claude-test-model"))
    monkeypatch.setattr(main_mod, "setup_api_client", lambda app_config=None: object())
    monkeypatch.setattr(main_mod, "create_default_registry", lambda: object())
    monkeypatch.setattr(main_mod, "QueryEngine", _FakeQueryEngine)
    monkeypatch.setattr(main_mod, "SessionManager", _FakeSessionManager)
    monkeypatch.setattr(main_mod, "SQLiteSessionStore", lambda db_path=None: object())
    monkeypatch.setattr(main_mod, "HistoryManager", lambda storage_path=None: object())
    monkeypatch.setattr(main_mod, "SQLiteEventJournal", lambda db_path=None: object())
    monkeypatch.setattr(
        main_mod,
        "create_task_manager_with_event_journal",
        lambda config, event_journal: object(),
    )
    monkeypatch.setattr(main_mod, "HooksManager", lambda config_path=None: object())
    monkeypatch.setattr(main_mod, "get_memory", lambda: SessionMemory(storage_dir=tmp_path / "memory"))
    monkeypatch.setattr(main_mod, "_create_application", lambda app_config: object())

    main_mod.create_runtime(model="claude-custom-model", working_dir="D:/runtime")

    assert captured["config"].memory_scope == "user"
