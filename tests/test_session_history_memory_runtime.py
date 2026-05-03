"""Runtime tests for session/history/memory boundary contracts."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from claude_code.engine.query import QueryConfig, QueryEngine
from claude_code.engine.session import SessionManager
from claude_code.services.history_manager import HistoryManager
from claude_code.services.memory_service import SessionMemory


class _SingleTurnApiClient:
    """Deterministic API client that emits one assistant text response."""

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
async def test_query_engine_persists_live_messages_only_to_session(tmp_path):
    session_manager = SessionManager(storage_dir=tmp_path / "sessions")
    history_manager = HistoryManager(storage_path=tmp_path / "history.json")
    memory = SessionMemory(storage_dir=tmp_path / "memory")

    engine = QueryEngine(api_client=_SingleTurnApiClient(), config=QueryConfig())
    engine.session_manager = session_manager
    engine.history_manager = history_manager
    engine.memory = memory

    current_session = session_manager.ensure_current_session()
    engine.config.session_id = current_session.id
    engine.config.working_directory = str(tmp_path)

    async for _ in engine.query("hello"):
        pass

    reloaded_session = session_manager.load_session(current_session.id)
    assert reloaded_session is not None
    assert len(reloaded_session.messages) >= 2
    assert reloaded_session.messages[0].role == "user"
    assert reloaded_session.messages[1].role == "assistant"

    assert history_manager.get_entries() == []
    assert await memory.export() == {}


@pytest.mark.asyncio
async def test_resume_archives_previous_session_into_history(tmp_path):
    session_manager = SessionManager(storage_dir=tmp_path / "sessions")
    history_manager = HistoryManager(storage_path=tmp_path / "history.json")

    session_one = session_manager.create_session()
    session_one.metadata.working_directory = str(tmp_path / "project-a")
    session_one.add_user_message("u1")
    session_one.add_assistant_message("a1")
    session_one.save()

    session_two = session_manager.create_session()
    session_two.metadata.working_directory = str(tmp_path / "project-b")
    session_two.add_user_message("u2")
    session_two.add_assistant_message("a2")
    session_two.save()

    session_manager.switch_session(session_one.id)

    engine = QueryEngine(api_client=_SingleTurnApiClient(), config=QueryConfig())
    engine.session_manager = session_manager
    engine.history_manager = history_manager
    engine.config.session_id = session_one.id
    engine.messages = []

    resumed = await engine.resume_session(session_two.id)

    assert resumed is True
    assert engine.config.session_id == session_two.id
    assert len(engine.messages) == len(session_two.messages)

    archived = history_manager.get_session_entries(session_one.id)
    assert len(archived) == len(session_one.messages)
    assert all(entry.metadata.get("session_id") == session_one.id for entry in archived)


def test_history_archive_is_idempotent_for_same_session_messages(tmp_path):
    history_manager = HistoryManager(storage_path=tmp_path / "history.json")
    messages = [
        {
            "id": "m1",
            "role": "user",
            "content": "hello",
            "timestamp": 1.0,
            "metadata": {},
        },
        {
            "id": "m2",
            "role": "assistant",
            "content": "world",
            "timestamp": 2.0,
            "metadata": {},
        },
    ]

    first = history_manager.archive_session_messages("s-1", messages)
    second = history_manager.archive_session_messages("s-1", messages)

    assert first == 2
    assert second == 0
    assert len(history_manager.get_session_entries("s-1")) == 2


@pytest.mark.asyncio
async def test_memory_knowledge_api_is_separate_from_session_history(tmp_path):
    memory = SessionMemory(storage_dir=tmp_path / "memory")

    await memory.set_knowledge(
        "project:architecture",
        {"decision": "use sqlite"},
    )
    keys = await memory.list_knowledge_keys()

    assert keys == ["project:architecture"]
    assert await memory.get("project:architecture") == {"decision": "use sqlite"}
