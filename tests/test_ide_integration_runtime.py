"""Runtime tests for P2-03 IDE integration path (VS Code first)."""

from __future__ import annotations

import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from claude_code.server.control_plane import ControlPlaneClient
from claude_code.server.ide_adapter import VSCodeClientAdapter
from claude_code.engine.session import SessionManager
from claude_code.services.event_journal import EventJournal
from claude_code.server.control_plane import ControlPlaneDaemon, DaemonServerConfig
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
    def __init__(self, session_manager: SessionManager) -> None:
        self._session_manager = session_manager
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


def _build_runtime(tmp_path: Path) -> tuple[SimpleNamespace, str]:
    session_dir = tmp_path / "sessions"
    session_manager = SessionManager(storage_dir=session_dir)
    session = session_manager.create_session()
    session.add_user_message("bootstrap message")

    tool_registry = ToolRegistry(lazy=False)
    tool_registry.register(_EchoTool())

    query_engine = _FakeQueryEngine(session_manager)
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
def _running_daemon(runtime: SimpleNamespace):
    daemon = ControlPlaneDaemon(
        runtime,
        DaemonServerConfig(
            host="127.0.0.1",
            port=0,
            request_timeout_seconds=3.0,
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


def _prepare_git_repo(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "config", "user.email", "ide-test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "ide-test"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )


def test_vscode_client_protocol_adapter_normalizes_workspace_snapshot(tmp_path: Path):
    class _FakeDaemonClient:
        def get_ide_workspace(self, **kwargs):
            assert kwargs["include_diff"] is True
            return {
                "workspace": {
                    "working_directory": str(tmp_path),
                    "diff": {"content": "diff --git a/a.py b/a.py", "truncated": False, "line_count": 1},
                    "changed_files": [{"path": "a.py", "status": " M"}],
                    "sessions": [{"id": "session-1"}],
                    "tasks": [{"id": "task-1"}],
                    "findings": [{"file_path": "a.py", "line": 1, "severity": "low", "issue": "x"}],
                }
            }

    adapter = VSCodeClientAdapter(_FakeDaemonClient())  # type: ignore[arg-type]
    snapshot = adapter.fetch_workspace_snapshot()

    assert snapshot.working_directory == str(tmp_path)
    assert snapshot.diff["content"].startswith("diff --git")
    assert snapshot.changed_files[0]["path"] == "a.py"
    assert snapshot.sessions[0]["id"] == "session-1"
    assert snapshot.tasks[0]["id"] == "task-1"
    assert snapshot.findings[0]["file_path"] == "a.py"


def test_ide_to_daemon_core_chain_returns_diff_task_session_and_findings(tmp_path: Path):
    _prepare_git_repo(tmp_path)
    baseline = tmp_path / "module.py"
    baseline.write_text("def run():\n    return 0\n", encoding="utf-8")

    import subprocess

    subprocess.run(["git", "add", "module.py"], cwd=tmp_path, check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "commit", "-m", "baseline"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )

    baseline.write_text("def run():\n    print('debug')\n    return 0\n", encoding="utf-8")

    runtime, _ = _build_runtime(tmp_path)
    with _running_daemon(runtime) as daemon:
        client = ControlPlaneClient(daemon.base_url, timeout_seconds=3.0)
        payload = client.get_ide_workspace(diff_max_lines=200, findings_limit=50)
        workspace = payload["workspace"]

        assert workspace["working_directory"] == str(tmp_path)
        assert isinstance(workspace["sessions"], list)
        assert isinstance(workspace["tasks"], list)
        assert isinstance(workspace["changed_files"], list)
        assert isinstance(workspace["findings"], list)
        assert "module.py" in workspace["diff"]["content"]
        assert any(item["path"] == "module.py" for item in workspace["changed_files"])
