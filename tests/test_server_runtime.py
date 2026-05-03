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


def test_control_plane_github_ci_workflow_endpoint(tmp_path: Path, monkeypatch):
    runtime, _ = _build_runtime(tmp_path)

    captured: dict[str, object] = {}

    class _FakeWorkflowService:
        def run_workflow(self, **kwargs):
            captured.update(kwargs)
            return {
                "workflow_id": "wf-1",
                "status": "completed",
                "steps": [],
                "working_directory": kwargs["working_directory"],
                "headless_ci": kwargs["headless_ci"],
            }

    import claude_code.server.control_plane as control_plane_mod

    monkeypatch.setattr(control_plane_mod, "GitHubCIWorkflowService", _FakeWorkflowService)

    with _running_daemon(runtime) as daemon:
        client = ControlPlaneClient(daemon.base_url, timeout_seconds=3.0)
        payload = client.run_github_ci_workflow(
            issue_reference="#124",
            plan_summary="link issue to PR",
            branch_name="codex/p2-04-124",
            base_branch="main",
            ci_commands=["python -m pytest -q"],
            headless_ci=True,
            allow_dirty_repo=False,
            push_remote=False,
            create_pull_request=False,
        )

    assert payload["workflow"]["status"] == "completed"
    assert captured["working_directory"] == str(tmp_path)
    assert captured["issue_reference"] == "#124"
    assert captured["create_pull_request"] is False


def test_control_plane_github_ci_workflow_failure_maps_error(tmp_path: Path, monkeypatch):
    runtime, _ = _build_runtime(tmp_path)

    from claude_code.services.github_ci_workflow import GitHubCIWorkflowError
    import claude_code.server.control_plane as control_plane_mod

    class _FailingWorkflowService:
        def run_workflow(self, **kwargs):
            raise GitHubCIWorkflowError(
                "network down",
                code="network_failure",
                status_code=503,
                details={"reason": "dns"},
                step="pr",
            )

    monkeypatch.setattr(control_plane_mod, "GitHubCIWorkflowService", _FailingWorkflowService)

    with _running_daemon(runtime) as daemon:
        client = ControlPlaneClient(daemon.base_url, timeout_seconds=3.0)
        with pytest.raises(DaemonResponseError) as exc_info:
            client.run_github_ci_workflow(
                issue_reference="#125",
                push_remote=True,
                create_pull_request=True,
            )

    assert exc_info.value.status_code == 503
    assert exc_info.value.code == "network_failure"


def test_control_plane_org_policy_audit_endpoint(tmp_path: Path):
    runtime, _ = _build_runtime(tmp_path)

    with _running_daemon(runtime) as daemon:
        client = ControlPlaneClient(daemon.base_url, timeout_seconds=3.0)
        evaluate = client.evaluate_org_policy(
            tool_name="write",
            operation="repo:edit",
            payload={"content": "hello", "token": "sk-secret"},
            actor="dev-bot",
            policies=[
                {
                    "id": "approve-write",
                    "effect": "require_approval",
                    "tool_pattern": "write",
                    "operation_pattern": "*",
                    "priority": 10,
                }
            ],
            create_approval=True,
        )
        decision = evaluate["policy_decision"]
        assert decision["allowed"] is False
        assert decision["decision"] == "approval_pending"
        approval_id = decision["approval"]["approval_id"]
        assert decision["payload_redacted"]["token"] == "***REDACTED***"

        listed = client.list_org_approvals(status="pending", limit=10)
        assert listed["approvals"]
        assert listed["approvals"][0]["approval_id"] == approval_id

        decided = client.decide_org_approval(
            approval_id=approval_id,
            decision="approve",
            decided_by="sec-admin",
            reason="approved for release",
        )
        assert decided["approval"]["status"] == "approved"

        allowed = client.evaluate_org_policy(
            tool_name="write",
            operation="repo:edit",
            payload={"content": "hello", "token": "sk-secret"},
            actor="dev-bot",
            create_approval=True,
        )
        assert allowed["policy_decision"]["allowed"] is True
        assert allowed["policy_decision"]["decision"] == "allowed_by_approval"

        audit_events = client.list_org_audit_events(
            event_type="org_policy.evaluated",
            limit=20,
        )
        assert audit_events["events"]

        report = client.get_org_policy_report(limit=50)
        summary = report["report"]["summary"]
        assert summary["rule_count"] >= 1
        assert summary["approval_total"] >= 1


def test_control_plane_org_policy_audit_failure_maps_error(tmp_path: Path):
    runtime, _ = _build_runtime(tmp_path)

    with _running_daemon(runtime) as daemon:
        client = ControlPlaneClient(daemon.base_url, timeout_seconds=3.0)

        with pytest.raises(DaemonResponseError) as missing_exc:
            client.decide_org_approval(
                approval_id="apr-missing",
                decision="approve",
                decided_by="sec-admin",
            )
        assert missing_exc.value.status_code == 404
        assert missing_exc.value.code == "approval_not_found"

        with pytest.raises(DaemonResponseError) as validation_exc:
            client.evaluate_org_policy(
                tool_name="write",
                operation="repo:edit",
                payload={"a": 1},
                policies=[
                    {
                        "id": "bad-rule",
                        "effect": "unsupported",
                        "tool_pattern": "write",
                    }
                ],
            )
        assert validation_exc.value.status_code == 400
        assert validation_exc.value.code == "validation_error"
