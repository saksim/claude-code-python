"""Runtime tests for /resume command and session recovery flow."""

from __future__ import annotations

import io
from types import SimpleNamespace

import pytest
from rich.console import Console

from claude_code.commands.base import CommandContext
from claude_code.commands.compact import ResumeCommand
from claude_code.engine.query import QueryConfig, QueryEngine
from claude_code.engine.session import SessionManager
from claude_code.repl import REPL, REPLConfig


class _NoopAPIClient:
    async def create_message_streaming(self, messages, options):
        if False:
            yield None

    async def create_message(self, messages, options):
        class _Response:
            content = [{"type": "text", "text": "noop"}]

        return _Response()


def _context(tmp_path, engine) -> CommandContext:
    return CommandContext(
        working_directory=str(tmp_path),
        console=Console(file=io.StringIO(), force_terminal=False, width=120),
        engine=engine,
        session={"id": "ctx-session"},
    )


@pytest.mark.asyncio
async def test_resume_command_lists_recent_sessions(tmp_path):
    manager = SessionManager(storage_dir=tmp_path)
    session = manager.create_session()
    session.add_user_message("hello")
    session.add_assistant_message("world")

    engine = SimpleNamespace(session_manager=manager)
    result = await ResumeCommand().execute("", _context(tmp_path, engine))

    assert result.success
    assert session.id in str(result.content)
    assert "Use /resume <session-id>" in str(result.content)


@pytest.mark.asyncio
async def test_resume_command_restores_target_session(tmp_path):
    manager = SessionManager(storage_dir=tmp_path)
    session = manager.create_session()
    session.metadata.working_directory = str(tmp_path)
    session.add_user_message("u1")
    session.add_assistant_message("a1")
    session.save()

    engine = QueryEngine(api_client=_NoopAPIClient(), config=QueryConfig())
    engine.session_manager = manager

    result = await ResumeCommand().execute(session.id, _context(tmp_path, engine))

    assert result.success
    assert engine.config.session_id == session.id
    assert engine.config.working_directory == str(tmp_path)
    assert len(engine.messages) == 2
    assert "Session ID" in str(result.content)


@pytest.mark.asyncio
async def test_resume_command_reports_missing_or_unreadable_session(tmp_path):
    # Corrupted session file should be treated as unreadable and fail gracefully.
    (tmp_path / "broken.json").write_text("{not-valid-json", encoding="utf-8")
    manager = SessionManager(storage_dir=tmp_path)

    engine = QueryEngine(api_client=_NoopAPIClient(), config=QueryConfig())
    engine.session_manager = manager

    result = await ResumeCommand().execute("broken", _context(tmp_path, engine))

    assert result.success is False
    assert "not found or unreadable" in str(result.error)


@pytest.mark.asyncio
async def test_query_engine_resume_session_without_candidates_returns_false(tmp_path):
    manager = SessionManager(storage_dir=tmp_path)
    engine = QueryEngine(api_client=_NoopAPIClient(), config=QueryConfig())
    engine.session_manager = manager

    resumed = await engine.resume_session()
    assert resumed is False


@pytest.mark.asyncio
async def test_repl_resume_command_calls_engine_resume_session(tmp_path):
    class _StubEngine:
        def __init__(self) -> None:
            self.called = None
            self.messages = []
            self.tool_results = []
            self.config = SimpleNamespace(
                session_id="active-session",
                working_directory=str(tmp_path),
            )

        async def resume_session(self, session_id: str) -> bool:
            self.called = session_id
            self.config.session_id = session_id
            self.messages = [object(), object()]
            return True

    engine = _StubEngine()
    repl = REPL(
        engine=engine,
        config=REPLConfig(working_directory=str(tmp_path), welcome_message=False),
    )
    repl._commands = {"resume": ResumeCommand()}
    repl._console = Console(file=io.StringIO(), force_terminal=False, width=120)

    handled = await repl.run_command("/resume my-session")

    assert handled is True
    assert engine.called == "my-session"
