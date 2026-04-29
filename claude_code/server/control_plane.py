"""Daemon/API control plane for Claude Code runtime.

Provides:
- Local HTTP daemon entrypoint
- Runtime service dispatch (session/task/tool/query/artifact)
- Minimal stdlib client for CLI/IDE integration
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
import shlex
import socket
import threading
from dataclasses import dataclass
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Optional
from urllib import error as urllib_error
from urllib import parse as urllib_parse
from urllib import request as urllib_request

from pydantic import BaseModel, Field, ValidationError

from claude_code.permissions import create_permission_checker
from claude_code.tasks.types import BashTask, Task, TaskResult, TaskStatus, TaskType
from claude_code.tools.base import ToolContext


class ControlPlaneError(RuntimeError):
    """Control-plane exception carrying API error metadata."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "control_plane_error",
        status_code: int = 500,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details


class DaemonClientError(RuntimeError):
    """Base class for control-plane client errors."""


class DaemonUnavailableError(DaemonClientError):
    """Raised when daemon endpoint is unreachable."""


class DaemonTimeoutError(DaemonClientError):
    """Raised when daemon call times out."""


class DaemonResponseError(DaemonClientError):
    """Raised on non-2xx daemon responses."""

    def __init__(self, status_code: int, code: str, message: str, details: Any = None) -> None:
        super().__init__(f"{status_code} {code}: {message}")
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


@dataclass(frozen=True, slots=True)
class DaemonServerConfig:
    """Runtime daemon server configuration."""

    host: str = "127.0.0.1"
    port: int = 8787
    request_timeout_seconds: float = 30.0
    artifact_max_bytes: int = 512 * 1024


class QueryRequest(BaseModel):
    """POST /api/v1/query payload."""

    query: str = Field(min_length=1)
    session_id: str | None = None
    max_events: int = Field(default=256, ge=1, le=4096)


class ResumeSessionRequest(BaseModel):
    """POST /api/v1/sessions/resume payload."""

    session_id: str | None = None


class BashTaskCreateRequest(BaseModel):
    """POST /api/v1/tasks/bash payload."""

    command: str = Field(min_length=1)
    cwd: str | None = None
    env: dict[str, str] = Field(default_factory=dict)
    timeout: float | None = Field(default=None, gt=0)
    background: bool = True
    description: str | None = None
    idempotency_key: str | None = None
    max_retries: int = Field(default=0, ge=0, le=10)
    retry_delay: float = Field(default=0.0, ge=0.0, le=60.0)
    wait_timeout: float | None = Field(default=None, gt=0)


class ToolExecuteRequest(BaseModel):
    """POST /api/v1/tools/execute payload."""

    name: str = Field(min_length=1)
    input: dict[str, Any] = Field(default_factory=dict)
    permission_mode: str | None = None
    session_id: str | None = None


class ArtifactReadRequest(BaseModel):
    """GET /api/v1/artifacts/read query schema."""

    path: str = Field(min_length=1)
    encoding: str = Field(default="utf-8")
    max_bytes: int = Field(default=256 * 1024, ge=1, le=1024 * 1024)


class JournalListRequest(BaseModel):
    """GET /api/v1/events query schema."""

    session_id: str | None = None
    event_type: str | None = None
    limit: int = Field(default=200, ge=1, le=5000)
    since_sequence: int | None = Field(default=None, ge=1)
    until_sequence: int | None = Field(default=None, ge=1)


class JournalReplayRequest(BaseModel):
    """GET /api/v1/events/replay query schema."""

    session_id: str | None = None
    event_type: str | None = None
    limit: int = Field(default=200, ge=1, le=5000)
    since_sequence: int | None = Field(default=None, ge=1)
    until_sequence: int | None = Field(default=None, ge=1)


def _iso_or_none(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat()


def _extract_assistant_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return str(content)
    parts: list[str] = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    return "".join(parts)


def _serialize_task(task: Task) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": task.id,
        "type": task.type.value if isinstance(task.type, TaskType) else str(task.type),
        "status": task.status.value if isinstance(task.status, TaskStatus) else str(task.status),
        "description": task.description,
        "created_at": _iso_or_none(task.created_at),
        "started_at": _iso_or_none(task.started_at),
        "completed_at": _iso_or_none(task.completed_at),
        "error": task.error,
        "is_backgrounded": task.is_backgrounded,
        "parent_id": task.parent_id,
        "tags": list(task.tags),
        "metadata": dict(task.metadata),
        "duration_seconds": task.duration,
    }
    if isinstance(task, BashTask):
        payload["command"] = task.command
        payload["cwd"] = task.cwd
        payload["timeout"] = task.timeout
    if task.result:
        payload["result"] = {
            "code": task.result.code,
            "stdout": task.result.stdout,
            "stderr": task.result.stderr,
            "error": task.result.error,
        }
    else:
        payload["result"] = None
    return payload


class ControlPlaneService:
    """Runtime-backed API service implementation."""

    def __init__(
        self,
        runtime: Any,
        *,
        artifact_max_bytes: int,
    ) -> None:
        self._runtime = runtime
        self._artifact_max_bytes = artifact_max_bytes
        self._query_lock = asyncio.Lock()

    @property
    def runtime(self) -> Any:
        return self._runtime

    async def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "service": "claude-code-python-daemon",
            "working_directory": self.runtime.working_directory,
        }

    async def query(self, request: QueryRequest) -> dict[str, Any]:
        if request.session_id:
            resumed = await self.runtime.query_engine.resume_session(request.session_id)
            if not resumed:
                raise ControlPlaneError(
                    f"Session not found: {request.session_id}",
                    code="session_not_found",
                    status_code=404,
                )

        text_parts: list[str] = []
        stop_reason: Optional[str] = None
        event_count = 0

        async with self._query_lock:
            async for event in self.runtime.query_engine.query(request.query):
                event_count += 1
                if event_count > request.max_events:
                    break

                if isinstance(event, dict):
                    event_type = str(event.get("type", ""))
                    if event_type == "text":
                        text_parts.append(str(event.get("content", "")))
                    elif event_type == "stop_reason":
                        stop_reason = str(event.get("reason", ""))
                    continue

                if getattr(event, "role", None) == "assistant":
                    text_parts.append(_extract_assistant_text(getattr(event, "content", "")))

        return {
            "output": "".join(text_parts),
            "stop_reason": stop_reason,
            "event_count": event_count,
            "session_id": self.runtime.query_engine.config.session_id,
            "message_count": len(self.runtime.query_engine.get_messages()),
        }

    async def list_sessions(self) -> dict[str, Any]:
        sessions = self.runtime.session_manager.list_sessions()
        return {
            "sessions": [
                {
                    "id": item.id,
                    "created_at": item.created_at,
                    "last_active": item.last_active,
                    "working_directory": item.working_directory,
                    "model": item.model,
                    "message_count": item.message_count,
                    "tool_call_count": item.tool_call_count,
                }
                for item in sessions
            ]
        }

    async def get_session(self, session_id: str) -> dict[str, Any]:
        session = self.runtime.session_manager.load_session(session_id)
        if session is None:
            raise ControlPlaneError(
                f"Session not found: {session_id}",
                code="session_not_found",
                status_code=404,
            )
        return {
            "session": {
                "id": session.id,
                "metadata": session.metadata.to_dict(),
                "messages": [message.to_dict() for message in session.messages],
            }
        }

    async def resume_session(self, request: ResumeSessionRequest) -> dict[str, Any]:
        resumed = await self.runtime.query_engine.resume_session(request.session_id)
        if not resumed:
            target_id = request.session_id or "(latest)"
            raise ControlPlaneError(
                f"Session not found: {target_id}",
                code="session_not_found",
                status_code=404,
            )
        return {
            "session_id": self.runtime.query_engine.config.session_id,
            "message_count": len(self.runtime.query_engine.get_messages()),
        }

    async def list_tasks(
        self,
        *,
        status: Optional[str] = None,
        task_type: Optional[str] = None,
    ) -> dict[str, Any]:
        status_filter: Optional[TaskStatus] = None
        type_filter: Optional[TaskType] = None
        if status:
            try:
                status_filter = TaskStatus(status)
            except ValueError as exc:
                raise ControlPlaneError(
                    f"Unknown task status: {status}",
                    code="validation_error",
                    status_code=400,
                ) from exc
        if task_type:
            try:
                type_filter = TaskType(task_type)
            except ValueError as exc:
                raise ControlPlaneError(
                    f"Unknown task type: {task_type}",
                    code="validation_error",
                    status_code=400,
                ) from exc

        tasks = self.runtime.task_manager.list_tasks(status=status_filter, task_type=type_filter)
        return {"tasks": [_serialize_task(task) for task in tasks]}

    async def get_task(self, task_id: str) -> dict[str, Any]:
        task = self.runtime.task_manager.get_task(task_id)
        if task is None:
            raise ControlPlaneError(
                f"Task not found: {task_id}",
                code="task_not_found",
                status_code=404,
            )
        return {"task": _serialize_task(task)}

    async def create_bash_task(self, request: BashTaskCreateRequest) -> dict[str, Any]:
        task = await self.runtime.task_manager.create_bash_task(
            command=request.command,
            cwd=request.cwd,
            env=request.env,
            timeout=request.timeout,
            background=request.background,
            description=request.description,
            idempotency_key=request.idempotency_key,
        )
        await self.runtime.task_manager.start_task(
            task.id,
            executor=self._execute_bash_task,
            max_retries=request.max_retries,
            retry_delay=request.retry_delay,
        )

        if not request.background:
            await self.runtime.task_manager.wait_for_task(
                task.id,
                timeout=request.wait_timeout or request.timeout,
            )

        latest = self.runtime.task_manager.get_task(task.id) or task
        return {"task": _serialize_task(latest)}

    async def execute_tool(self, request: ToolExecuteRequest) -> dict[str, Any]:
        tool = self.runtime.tool_registry.get(request.name)
        if tool is None:
            raise ControlPlaneError(
                f"Tool not found: {request.name}",
                code="tool_not_found",
                status_code=404,
            )

        config = self.runtime.query_engine.config
        permission_mode = request.permission_mode or config.permission_mode
        checker = create_permission_checker(
            mode=permission_mode,
            always_allow=list(config.always_allow),
            always_deny=list(config.always_deny),
        )
        if not checker.can_execute(request.name):
            raise ControlPlaneError(
                f"Permission denied for tool: {request.name}",
                code="permission_denied",
                status_code=403,
            )

        is_valid, validation_error = tool.validate_input(request.input)
        if not is_valid:
            raise ControlPlaneError(
                f"Invalid tool input: {validation_error}",
                code="validation_error",
                status_code=400,
            )

        context = ToolContext(
            working_directory=config.working_directory or self.runtime.working_directory,
            environment={},
            permission_mode=permission_mode,
            always_allow=list(config.always_allow),
            always_deny=list(config.always_deny),
            model=config.model,
            session_id=request.session_id or config.session_id,
        )
        result = await tool.execute(request.input, context)
        return {
            "tool_name": request.name,
            "content": result.content,
            "is_error": result.is_error,
            "tool_use_id": result.tool_use_id,
        }

    async def read_artifact(self, request: ArtifactReadRequest) -> dict[str, Any]:
        artifact_path = self._resolve_artifact_path(request.path)
        if not artifact_path.is_file():
            raise ControlPlaneError(
                f"Artifact not found: {request.path}",
                code="artifact_not_found",
                status_code=404,
            )

        raw = artifact_path.read_bytes()
        max_bytes = min(request.max_bytes, self._artifact_max_bytes)
        truncated = len(raw) > max_bytes
        payload = raw[:max_bytes]
        content = payload.decode(request.encoding, errors="replace")

        return {
            "path": str(artifact_path),
            "size_bytes": len(raw),
            "returned_bytes": len(payload),
            "truncated": truncated,
            "encoding": request.encoding,
            "content": content,
        }

    async def list_events(self, request: JournalListRequest) -> dict[str, Any]:
        journal = getattr(self.runtime, "event_journal", None)
        if journal is None:
            raise ControlPlaneError(
                "Event journal is not configured",
                code="event_journal_unavailable",
                status_code=503,
            )

        event_types = [request.event_type] if request.event_type else None
        entries = journal.query_events(
            session_id=request.session_id,
            event_types=event_types,
            limit=request.limit,
            since_sequence=request.since_sequence,
            until_sequence=request.until_sequence,
        )
        return {
            "events": [entry.to_dict() for entry in entries],
            "diagnostics": journal.get_diagnostics(),
        }

    async def replay_events(self, request: JournalReplayRequest) -> dict[str, Any]:
        journal = getattr(self.runtime, "event_journal", None)
        if journal is None:
            raise ControlPlaneError(
                "Event journal is not configured",
                code="event_journal_unavailable",
                status_code=503,
            )

        event_types = [request.event_type] if request.event_type else None
        entries = journal.replay_events(
            session_id=request.session_id,
            event_types=event_types,
            since_sequence=request.since_sequence,
            until_sequence=request.until_sequence,
            limit=request.limit,
        )
        return {
            "events": [entry.to_dict() for entry in entries],
            "diagnostics": journal.get_diagnostics(),
        }

    async def _execute_bash_task(self, task: Task) -> TaskResult:
        if not isinstance(task, BashTask):
            raise TypeError("executor expects BashTask")

        if os.name == "nt":
            cmd = ["cmd", "/c", task.command]
        else:
            cmd = shlex.split(task.command)

        env = {**os.environ, **(task.env or {})}
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=task.cwd,
            env=env,
        )
        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=task.timeout,
            )
        except asyncio.TimeoutError:
            try:
                process.kill()
            except Exception:
                pass
            try:
                await process.wait()
            except Exception:
                pass
            raise

        return TaskResult(
            code=process.returncode or 0,
            stdout=stdout_bytes.decode("utf-8", errors="replace"),
            stderr=stderr_bytes.decode("utf-8", errors="replace"),
            error=None,
        )

    def _resolve_artifact_path(self, raw_path: str) -> Path:
        root = Path(self.runtime.working_directory).resolve()
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = (root / path).resolve()
        else:
            path = path.resolve()

        try:
            path.relative_to(root)
        except ValueError as exc:
            raise ControlPlaneError(
                f"Artifact path escapes working directory: {raw_path}",
                code="validation_error",
                status_code=400,
            ) from exc
        return path


class ControlPlaneDaemon:
    """Threaded HTTP daemon exposing runtime control-plane APIs."""

    def __init__(self, runtime: Any, config: Optional[DaemonServerConfig] = None) -> None:
        self.config = config or DaemonServerConfig()
        self._service = ControlPlaneService(
            runtime,
            artifact_max_bytes=self.config.artifact_max_bytes,
        )
        self._loop = asyncio.new_event_loop()
        self._loop_thread: Optional[threading.Thread] = None
        self._httpd: Optional[ThreadingHTTPServer] = None
        self._http_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._running = False
        self._port = self.config.port

    @property
    def port(self) -> int:
        return self._port

    @property
    def base_url(self) -> str:
        return f"http://{self.config.host}:{self.port}"

    def start(self) -> None:
        with self._lock:
            if self._running:
                return

            self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self._loop_thread.start()

            handler = self._build_handler()
            self._httpd = ThreadingHTTPServer((self.config.host, self.config.port), handler)
            self._port = int(self._httpd.server_address[1])
            self._http_thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
            self._http_thread.start()
            self._running = True

    def stop(self) -> None:
        with self._lock:
            if not self._running:
                return
            if self._httpd is not None:
                self._httpd.shutdown()
                self._httpd.server_close()
            self._running = False

        if self._http_thread is not None:
            self._http_thread.join(timeout=5.0)
        self._http_thread = None

        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._loop_thread is not None:
            self._loop_thread.join(timeout=5.0)
        self._loop_thread = None

        try:
            self._loop.close()
        except Exception:
            pass

    def serve_forever(self) -> None:
        self.start()
        if self._http_thread is None:
            return
        try:
            self._http_thread.join()
        except KeyboardInterrupt:
            self.stop()

    def _run_event_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def _build_handler(self):
        daemon = self

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802
                daemon._handle_http(self, "GET")

            def do_POST(self) -> None:  # noqa: N802
                daemon._handle_http(self, "POST")

            def log_message(self, format: str, *args: Any) -> None:
                return

        return _Handler

    def _handle_http(self, handler: BaseHTTPRequestHandler, method: str) -> None:
        try:
            parsed = urllib_parse.urlparse(handler.path)
            path = parsed.path
            query_params = urllib_parse.parse_qs(parsed.query, keep_blank_values=True)
            payload = self._read_json_payload(handler) if method == "POST" else {}
            data = self._dispatch(method=method, path=path, payload=payload, query_params=query_params)
            self._write_response(handler, status_code=200, payload={"ok": True, "data": data})
        except ControlPlaneError as exc:
            self._write_response(
                handler,
                status_code=exc.status_code,
                payload={
                    "ok": False,
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "details": exc.details,
                    },
                },
            )
        except Exception as exc:
            self._write_response(
                handler,
                status_code=500,
                payload={
                    "ok": False,
                    "error": {
                        "code": "internal_error",
                        "message": str(exc),
                    },
                },
            )

    def _read_json_payload(self, handler: BaseHTTPRequestHandler) -> dict[str, Any]:
        raw_length = handler.headers.get("Content-Length", "0")
        try:
            length = int(raw_length)
        except ValueError as exc:
            raise ControlPlaneError(
                "Invalid Content-Length",
                code="validation_error",
                status_code=400,
            ) from exc

        if length <= 0:
            return {}

        raw = handler.rfile.read(length)
        if not raw:
            return {}
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ControlPlaneError(
                "Invalid JSON payload",
                code="invalid_json",
                status_code=400,
            ) from exc
        if not isinstance(parsed, dict):
            raise ControlPlaneError(
                "JSON payload must be an object",
                code="validation_error",
                status_code=400,
            )
        return parsed

    def _dispatch(
        self,
        *,
        method: str,
        path: str,
        payload: dict[str, Any],
        query_params: dict[str, list[str]],
    ) -> dict[str, Any]:
        if method == "GET" and path == "/health":
            return self._await_service_call(self._service.health())

        if method == "POST" and path == "/api/v1/query":
            request = self._validate_payload(QueryRequest, payload)
            return self._await_service_call(self._service.query(request))

        if method == "GET" and path == "/api/v1/sessions":
            return self._await_service_call(self._service.list_sessions())

        if method == "GET" and path.startswith("/api/v1/sessions/"):
            session_id = path.removeprefix("/api/v1/sessions/").strip()
            if not session_id:
                raise ControlPlaneError("Missing session id", code="validation_error", status_code=400)
            return self._await_service_call(self._service.get_session(session_id))

        if method == "POST" and path == "/api/v1/sessions/resume":
            request = self._validate_payload(ResumeSessionRequest, payload)
            return self._await_service_call(self._service.resume_session(request))

        if method == "GET" and path == "/api/v1/tasks":
            status = self._first_query_value(query_params, "status")
            task_type = self._first_query_value(query_params, "type")
            return self._await_service_call(self._service.list_tasks(status=status, task_type=task_type))

        if method == "GET" and path.startswith("/api/v1/tasks/"):
            task_id = path.removeprefix("/api/v1/tasks/").strip()
            if not task_id:
                raise ControlPlaneError("Missing task id", code="validation_error", status_code=400)
            return self._await_service_call(self._service.get_task(task_id))

        if method == "POST" and path == "/api/v1/tasks/bash":
            request = self._validate_payload(BashTaskCreateRequest, payload)
            return self._await_service_call(self._service.create_bash_task(request))

        if method == "POST" and path == "/api/v1/tools/execute":
            request = self._validate_payload(ToolExecuteRequest, payload)
            return self._await_service_call(self._service.execute_tool(request))

        if method == "GET" and path == "/api/v1/artifacts/read":
            max_bytes_raw = self._first_query_value(query_params, "max_bytes", default=str(256 * 1024))
            try:
                max_bytes = int(max_bytes_raw) if max_bytes_raw is not None else 256 * 1024
            except ValueError as exc:
                raise ControlPlaneError(
                    f"Invalid max_bytes value: {max_bytes_raw}",
                    code="validation_error",
                    status_code=400,
                ) from exc
            request = self._validate_payload(
                ArtifactReadRequest,
                {
                    "path": self._first_query_value(query_params, "path"),
                    "encoding": self._first_query_value(query_params, "encoding", default="utf-8"),
                    "max_bytes": max_bytes,
                },
            )
            return self._await_service_call(self._service.read_artifact(request))

        if method == "GET" and path == "/api/v1/events":
            request = self._validate_payload(
                JournalListRequest,
                {
                    "session_id": self._first_query_value(query_params, "session_id"),
                    "event_type": self._first_query_value(query_params, "event_type"),
                    "limit": self._parse_optional_int(
                        self._first_query_value(query_params, "limit"),
                        default=200,
                        field_name="limit",
                    ),
                    "since_sequence": self._parse_optional_int(
                        self._first_query_value(query_params, "since_sequence"),
                        field_name="since_sequence",
                    ),
                    "until_sequence": self._parse_optional_int(
                        self._first_query_value(query_params, "until_sequence"),
                        field_name="until_sequence",
                    ),
                },
            )
            return self._await_service_call(self._service.list_events(request))

        if method == "GET" and path == "/api/v1/events/replay":
            request = self._validate_payload(
                JournalReplayRequest,
                {
                    "session_id": self._first_query_value(query_params, "session_id"),
                    "event_type": self._first_query_value(query_params, "event_type"),
                    "limit": self._parse_optional_int(
                        self._first_query_value(query_params, "limit"),
                        default=200,
                        field_name="limit",
                    ),
                    "since_sequence": self._parse_optional_int(
                        self._first_query_value(query_params, "since_sequence"),
                        field_name="since_sequence",
                    ),
                    "until_sequence": self._parse_optional_int(
                        self._first_query_value(query_params, "until_sequence"),
                        field_name="until_sequence",
                    ),
                },
            )
            return self._await_service_call(self._service.replay_events(request))

        raise ControlPlaneError(
            f"Route not found: {method} {path}",
            code="route_not_found",
            status_code=404,
        )

    def _await_service_call(self, coroutine: Any) -> dict[str, Any]:
        future = asyncio.run_coroutine_threadsafe(coroutine, self._loop)
        try:
            result = future.result(timeout=self.config.request_timeout_seconds)
        except concurrent.futures.TimeoutError as exc:
            future.cancel()
            raise ControlPlaneError(
                "Daemon request timed out",
                code="timeout",
                status_code=504,
            ) from exc
        except ControlPlaneError:
            raise
        except Exception as exc:
            raise ControlPlaneError(str(exc), code="internal_error", status_code=500) from exc
        if not isinstance(result, dict):
            return {"result": result}
        return result

    @staticmethod
    def _write_response(
        handler: BaseHTTPRequestHandler,
        *,
        status_code: int,
        payload: dict[str, Any],
    ) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        handler.send_response(status_code)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    @staticmethod
    def _first_query_value(
        query_params: dict[str, list[str]],
        name: str,
        *,
        default: Optional[str] = None,
    ) -> Optional[str]:
        values = query_params.get(name)
        if not values:
            return default
        value = values[0]
        if value is None or value == "":
            return default
        return value

    @staticmethod
    def _parse_optional_int(
        value: Optional[str],
        *,
        default: Optional[int] = None,
        field_name: str,
    ) -> Optional[int]:
        if value is None or value == "":
            return default
        try:
            return int(value)
        except ValueError as exc:
            raise ControlPlaneError(
                f"Invalid {field_name} value: {value}",
                code="validation_error",
                status_code=400,
            ) from exc

    @staticmethod
    def _validate_payload(model: type[BaseModel], payload: dict[str, Any]) -> Any:
        try:
            return model.model_validate(payload)
        except ValidationError as exc:
            raise ControlPlaneError(
                "Request validation failed",
                code="validation_error",
                status_code=400,
                details=exc.errors(),
            ) from exc


class ControlPlaneClient:
    """Minimal stdlib HTTP client for local daemon integration."""

    def __init__(self, base_url: str, *, timeout_seconds: float = 10.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health")

    def query(self, query: str, *, session_id: Optional[str] = None) -> dict[str, Any]:
        payload: dict[str, Any] = {"query": query}
        if session_id:
            payload["session_id"] = session_id
        return self._request("POST", "/api/v1/query", payload=payload)

    def list_sessions(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/sessions")

    def get_session(self, session_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/sessions/{session_id}")

    def resume_session(self, session_id: Optional[str] = None) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if session_id:
            payload["session_id"] = session_id
        return self._request("POST", "/api/v1/sessions/resume", payload=payload)

    def list_tasks(self) -> dict[str, Any]:
        return self._request("GET", "/api/v1/tasks")

    def get_task(self, task_id: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/tasks/{task_id}")

    def create_bash_task(self, command: str, **kwargs: Any) -> dict[str, Any]:
        payload = {"command": command, **kwargs}
        return self._request("POST", "/api/v1/tasks/bash", payload=payload)

    def execute_tool(self, name: str, input_data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        payload = {"name": name, "input": input_data or {}}
        return self._request("POST", "/api/v1/tools/execute", payload=payload)

    def read_artifact(self, path: str, *, encoding: str = "utf-8", max_bytes: int = 262144) -> dict[str, Any]:
        query = urllib_parse.urlencode(
            {"path": path, "encoding": encoding, "max_bytes": str(max_bytes)}
        )
        return self._request("GET", f"/api/v1/artifacts/read?{query}")

    def list_events(
        self,
        *,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 200,
        since_sequence: Optional[int] = None,
        until_sequence: Optional[int] = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {"limit": str(limit)}
        if session_id:
            params["session_id"] = session_id
        if event_type:
            params["event_type"] = event_type
        if since_sequence is not None:
            params["since_sequence"] = str(since_sequence)
        if until_sequence is not None:
            params["until_sequence"] = str(until_sequence)
        query = urllib_parse.urlencode(params)
        return self._request("GET", f"/api/v1/events?{query}")

    def replay_events(
        self,
        *,
        session_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 200,
        since_sequence: Optional[int] = None,
        until_sequence: Optional[int] = None,
    ) -> dict[str, Any]:
        params: dict[str, str] = {"limit": str(limit)}
        if session_id:
            params["session_id"] = session_id
        if event_type:
            params["event_type"] = event_type
        if since_sequence is not None:
            params["since_sequence"] = str(since_sequence)
        if until_sequence is not None:
            params["until_sequence"] = str(until_sequence)
        query = urllib_parse.urlencode(params)
        return self._request("GET", f"/api/v1/events/replay?{query}")

    def _request(
        self,
        method: str,
        path: str,
        *,
        payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        data_bytes: Optional[bytes] = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json; charset=utf-8"

        request = urllib_request.Request(url=url, method=method, data=data_bytes, headers=headers)
        try:
            with urllib_request.urlopen(request, timeout=self._timeout) as response:
                raw = response.read()
                parsed = json.loads(raw.decode("utf-8")) if raw else {}
                return self._unwrap_response(parsed)
        except urllib_error.HTTPError as exc:
            raw = exc.read()
            parsed: dict[str, Any]
            try:
                parsed = json.loads(raw.decode("utf-8")) if raw else {}
            except Exception:
                parsed = {}
            error_obj = parsed.get("error", {}) if isinstance(parsed, dict) else {}
            raise DaemonResponseError(
                exc.code,
                str(error_obj.get("code", "http_error")),
                str(error_obj.get("message", exc.reason)),
                error_obj.get("details"),
            ) from exc
        except urllib_error.URLError as exc:
            reason = exc.reason
            if isinstance(reason, socket.timeout):
                raise DaemonTimeoutError("Daemon request timed out") from exc
            raise DaemonUnavailableError(f"Daemon unavailable: {reason}") from exc
        except TimeoutError as exc:
            raise DaemonTimeoutError("Daemon request timed out") from exc

    @staticmethod
    def _unwrap_response(payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict):
            return {"result": payload}

        ok = payload.get("ok")
        if ok is False:
            error_obj = payload.get("error", {})
            raise DaemonResponseError(
                500,
                str(error_obj.get("code", "daemon_error")),
                str(error_obj.get("message", "daemon request failed")),
                error_obj.get("details"),
            )

        data = payload.get("data")
        if isinstance(data, dict):
            return data
        return payload


def run_control_plane_daemon(
    runtime: Any,
    *,
    host: str = "127.0.0.1",
    port: int = 8787,
    request_timeout_seconds: float = 30.0,
) -> None:
    """Blocking daemon runner used by CLI entrypoint."""
    daemon = ControlPlaneDaemon(
        runtime,
        DaemonServerConfig(
            host=host,
            port=port,
            request_timeout_seconds=request_timeout_seconds,
        ),
    )
    daemon.serve_forever()


__all__ = [
    "ControlPlaneError",
    "DaemonClientError",
    "DaemonUnavailableError",
    "DaemonTimeoutError",
    "DaemonResponseError",
    "DaemonServerConfig",
    "ControlPlaneDaemon",
    "ControlPlaneClient",
    "run_control_plane_daemon",
]
