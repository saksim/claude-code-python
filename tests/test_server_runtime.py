"""Runtime tests for daemon/API control-plane."""

from __future__ import annotations

import asyncio
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
import time

import pytest

from claude_code.engine.session import SessionManager
from claude_code.services.event_journal import EventJournal
from claude_code.server.control_plane import (
    ControlPlaneClient,
    ControlPlaneDaemon,
    DaemonResponseError,
    DaemonServerConfig,
    DaemonUnavailableError,
)
from claude_code.tasks.manager import TaskManager
from claude_code.tasks.queue import InMemoryTaskQueue
from claude_code.tools.base import Tool, ToolContext, ToolResult
from claude_code.tools.registry import ToolRegistry


class _EchoTool(Tool):
    @property
    def name(self) -> str:
        return "echo_tool"

    @property
    def description(self) -> str:
        return "Echo input text."

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
        return ToolResult(content=str(input_data.get("text", "")), is_error=False, tool_use_id="echo")

    def validate_input(self, input_data: dict) -> tuple[bool, str | None]:
        if "text" not in input_data:
            return False, "missing text"
        return True, None


class _FakeQueryEngine:
    def __init__(self, session_manager: SessionManager, *, delay_seconds: float = 0.0) -> None:
        self._session_manager = session_manager
        self._delay_seconds = delay_seconds
        self.received_queries: list[str] = []
        self._messages: list[object] = []
        self.config = SimpleNamespace(
            model="claude-test-model",
            permission_mode="default",
            always_allow=[],
            always_deny=[],
            session_id=None,
            working_directory=None,
        )

    async def query(self, user_input: str):
        self.received_queries.append(user_input)
        if self._delay_seconds > 0:
            await asyncio.sleep(self._delay_seconds)
        text = f"echo:{user_input}"
        yield {"type": "text", "content": text}
        assistant_message = SimpleNamespace(
            role="assistant",
            content=[{"type": "text", "text": text}],
        )
        self._messages.append(assistant_message)
        yield assistant_message
        yield {"type": "stop_reason", "reason": "end_turn"}

    async def resume_session(self, session_id: str | None = None) -> bool:
        if session_id:
            session = self._session_manager.load_session(session_id)
            if session is None:
                return False
            self.config.session_id = session.id
            return True
        sessions = self._session_manager.list_sessions()
        if not sessions:
            return False
        self.config.session_id = sessions[0].id
        return True

    def get_messages(self) -> list[object]:
        return list(self._messages)


def _build_runtime(tmp_path: Path, *, query_delay_seconds: float = 0.0) -> tuple[SimpleNamespace, str]:
    session_dir = tmp_path / "sessions"
    session_manager = SessionManager(storage_dir=session_dir)
    session = session_manager.create_session()
    session.add_user_message("bootstrap message")

    tool_registry = ToolRegistry(lazy=False)
    tool_registry.register(_EchoTool())

    query_engine = _FakeQueryEngine(session_manager, delay_seconds=query_delay_seconds)
    query_engine.config.session_id = session.id
    query_engine.config.working_directory = str(tmp_path)
    event_journal = EventJournal(tmp_path / ".claude" / "event_journal.jsonl")
    query_engine.event_journal = event_journal

    runtime = SimpleNamespace(
        working_directory=str(tmp_path),
        query_engine=query_engine,
        session_manager=session_manager,
        task_manager=TaskManager(task_queue=InMemoryTaskQueue()),
        tool_registry=tool_registry,
        event_journal=event_journal,
    )
    return runtime, session.id


@contextmanager
def _running_daemon(runtime: SimpleNamespace, *, request_timeout_seconds: float = 3.0):
    daemon = ControlPlaneDaemon(
        runtime,
        DaemonServerConfig(
            host="127.0.0.1",
            port=0,
            request_timeout_seconds=request_timeout_seconds,
        ),
    )
    daemon.start()
    client = ControlPlaneClient(daemon.base_url, timeout_seconds=0.2)
    last_error: Exception | None = None
    for _ in range(40):
        try:
            client.health()
            last_error = None
            break
        except Exception as exc:  # pragma: no cover - startup race mitigation only
            last_error = exc
            time.sleep(0.05)
    if last_error is not None:
        daemon.stop()
        raise last_error
    try:
        yield daemon
    finally:
        daemon.stop()


def test_control_plane_validation_rejects_empty_query(tmp_path: Path):
    runtime, _ = _build_runtime(tmp_path)
    with _running_daemon(runtime) as daemon:
        client = ControlPlaneClient(daemon.base_url, timeout_seconds=2.0)
        with pytest.raises(DaemonResponseError) as exc_info:
            client.query("")
        assert exc_info.value.status_code == 400
        assert exc_info.value.code == "validation_error"


def test_control_plane_service_endpoints_cover_session_task_tool_artifact(tmp_path: Path):
    runtime, session_id = _build_runtime(tmp_path)
    note_path = tmp_path / "note.txt"
    note_path.write_text("daemon artifact", encoding="utf-8")

    with _running_daemon(runtime) as daemon:
        client = ControlPlaneClient(daemon.base_url, timeout_seconds=3.0)

        health = client.health()
        assert health["status"] == "ok"

        sessions = client.list_sessions()["sessions"]
        assert sessions
        session_payload = client.get_session(session_id)["session"]
        assert session_payload["id"] == session_id

        task_payload = client.create_bash_task(
            "echo daemon-control-plane",
            background=False,
            wait_timeout=2.0,
        )["task"]
        assert task_payload["id"]
        task_detail = client.get_task(task_payload["id"])["task"]
        assert task_detail["id"] == task_payload["id"]
        assert task_detail["status"] in {"completed", "failed", "timeout"}

        tool_payload = client.execute_tool("echo_tool", {"text": "tool-ok"})
        assert tool_payload["is_error"] is False
        assert tool_payload["content"] == "tool-ok"

        artifact = client.read_artifact("note.txt")
        assert artifact["truncated"] is False
        assert "daemon artifact" in artifact["content"]


def test_control_plane_client_server_runtime_query_chain(tmp_path: Path):
    runtime, _ = _build_runtime(tmp_path)
    with _running_daemon(runtime) as daemon:
        client = ControlPlaneClient(daemon.base_url, timeout_seconds=3.0)
        result = client.query("hello daemon")
        assert "echo:hello daemon" in result["output"]
        assert runtime.query_engine.received_queries[-1] == "hello daemon"


def test_control_plane_failure_modes_daemon_down_timeout_and_session_not_found(tmp_path: Path):
    down_client = ControlPlaneClient("http://127.0.0.1:9", timeout_seconds=0.2)
    with pytest.raises(DaemonUnavailableError):
        down_client.health()

    slow_runtime, _ = _build_runtime(tmp_path / "slow", query_delay_seconds=0.3)
    with _running_daemon(slow_runtime, request_timeout_seconds=0.05) as daemon:
        slow_client = ControlPlaneClient(daemon.base_url, timeout_seconds=2.0)
        with pytest.raises(DaemonResponseError) as timeout_exc:
            slow_client.query("slow")
        assert timeout_exc.value.status_code == 504
        assert timeout_exc.value.code == "timeout"

        with pytest.raises(DaemonResponseError) as session_exc:
            slow_client.get_session("session-missing")
        assert session_exc.value.status_code == 404
        assert session_exc.value.code == "session_not_found"


def test_control_plane_events_endpoints(tmp_path: Path):
    runtime, session_id = _build_runtime(tmp_path)
    runtime.event_journal.append_event(
        event_type="query.started",
        payload={"input": "hello"},
        session_id=session_id,
        conversation_id="conv-1",
        source="query_engine",
    )
    runtime.event_journal.append_event(
        event_type="tool.completed",
        payload={"tool_name": "echo_tool"},
        session_id=session_id,
        conversation_id="conv-1",
        source="query_engine",
    )

    with _running_daemon(runtime) as daemon:
        client = ControlPlaneClient(daemon.base_url, timeout_seconds=3.0)
        listed = client.list_events(session_id=session_id, limit=10)
        assert listed["events"]
        assert listed["events"][0]["session_id"] == session_id

        replayed = client.replay_events(session_id=session_id, event_type="tool.completed", limit=10)
        assert replayed["events"]
        assert all(item["event_type"] == "tool.completed" for item in replayed["events"])
