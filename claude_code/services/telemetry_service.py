"""Telemetry Service for Claude Code Python.

Provides telemetry and observability for Claude Code operations.
"""

from __future__ import annotations

import json
import time
import uuid
from asyncio import Lock
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class EventType(Enum):
    """Types of telemetry events."""

    QUERY = "query"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    ERROR = "error"
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    COMMAND = "command"
    MODEL_CHANGE = "model_change"
    PERMISSION = "permission"
    COMPACTION = "compaction"
    COST_UPDATE = "cost_update"


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    """A single telemetry event.

    Attributes:
        event_type: Type of the event.
        timestamp: Unix timestamp of the event.
        session_id: ID of the session this event belongs to.
        data: Event-specific data.
        user_id: Optional user identifier.
        event_id: Unique identifier for this event.
    """

    event_type: EventType
    timestamp: float
    session_id: str
    data: dict[str, Any]
    user_id: str | None = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))


class TelemetryService:
    """Service for collecting and exporting telemetry data.

    Features:
    - Event collection with timestamps
    - Performance tracking
    - Error tracking
    - Export to various backends (console, file, OTLP)
    """

    def __init__(
        self,
        enabled: bool = True,
        export_to_console: bool = False,
        export_to_file: Path | str | None = None,
        session_id: str | None = None,
    ) -> None:
        """Initialize telemetry service.

        Args:
            enabled: Whether telemetry is enabled.
            export_to_console: Whether to print events to console.
            export_to_file: Path to export events to file.
            session_id: Optional session ID (generated if not provided).
        """
        self._enabled = enabled
        self._events: list[TelemetryEvent] = []
        self._export_console = export_to_console
        self._export_file = Path(export_to_file) if export_to_file else None
        self._session_id = session_id or str(uuid.uuid4())
        self._lock = Lock()
        self._start_time = time.time()

        if self._export_file:
            self._export_file.parent.mkdir(parents=True, exist_ok=True)

    @property
    def session_id(self) -> str:
        """Get current session ID."""
        return self._session_id

    async def track_event(
        self,
        event_type: EventType,
        data: dict[str, Any],
        user_id: str | None = None,
    ) -> None:
        """Track a telemetry event.

        Args:
            event_type: Type of the event.
            data: Event-specific data.
            user_id: Optional user identifier.
        """
        if not self._enabled:
            return

        event = TelemetryEvent(
            event_type=event_type,
            timestamp=time.time(),
            session_id=self._session_id,
            data=data,
            user_id=user_id,
        )

        async with self._lock:
            self._events.append(event)

        if self._export_console:
            self._print_event(event)

        if self._export_file:
            await self._write_event_to_file(event)

    async def track_query(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        duration_ms: float,
        success: bool = True,
    ) -> None:
        """Track a query event.

        Args:
            model: Model identifier.
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            duration_ms: Query duration in milliseconds.
            success: Whether the query succeeded.
        """
        await self.track_event(
            EventType.QUERY,
            {
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "duration_ms": duration_ms,
                "success": success,
            },
        )

    async def track_tool_call(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        success: bool = True,
        duration_ms: float | None = None,
    ) -> None:
        """Track a tool call event.

        Args:
            tool_name: Name of the tool.
            input_data: Input data to the tool.
            success: Whether the call succeeded.
            duration_ms: Optional call duration.
        """
        await self.track_event(
            EventType.TOOL_CALL,
            {
                "tool_name": tool_name,
                "input_size": len(json.dumps(input_data)),
                "success": success,
                "duration_ms": duration_ms,
            },
        )

    async def track_error(
        self,
        error_type: str,
        error_message: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Track an error event.

        Args:
            error_type: Type/category of the error.
            error_message: Error message.
            context: Additional error context.
        """
        await self.track_event(
            EventType.ERROR,
            {
                "error_type": error_type,
                "error_message": error_message,
                "context": context or {},
            },
        )

    async def track_session_start(
        self,
        model: str,
        working_directory: str,
    ) -> None:
        """Track session start.

        Args:
            model: Model being used.
            working_directory: Current working directory.
        """
        await self.track_event(
            EventType.SESSION_START,
            {
                "model": model,
                "working_directory": working_directory,
                "uptime": time.time() - self._start_time,
            },
        )

    async def track_session_end(self, reason: str = "normal") -> None:
        """Track session end.

        Args:
            reason: Reason for session ending.
        """
        await self.track_event(
            EventType.SESSION_END,
            {
                "reason": reason,
                "total_duration": time.time() - self._start_time,
                "event_count": len(self._events),
            },
        )

    async def track_permission(
        self,
        action: str,
        granted: bool,
        tool_name: str | None = None,
    ) -> None:
        """Track permission event.

        Args:
            action: Permission action.
            granted: Whether permission was granted.
            tool_name: Name of the tool requiring permission.
        """
        await self.track_event(
            EventType.PERMISSION,
            {
                "action": action,
                "granted": granted,
                "tool_name": tool_name,
            },
        )

    async def get_events(
        self,
        event_type: EventType | None = None,
        limit: int | None = None,
    ) -> list[TelemetryEvent]:
        """Get tracked events.

        Args:
            event_type: Filter by event type.
            limit: Maximum number of events to return.

        Returns:
            List of telemetry events.
        """
        async with self._lock:
            events = self._events

            if event_type:
                events = [e for e in events if e.event_type == event_type]

            if limit:
                events = events[-limit:]

            return events

    async def get_stats(self) -> dict[str, Any]:
        """Get telemetry statistics.

        Returns:
            Dictionary with telemetry statistics.
        """
        async with self._lock:
            by_type: dict[str, int] = {}
            for event in self._events:
                type_name = event.event_type.value
                by_type[type_name] = by_type.get(type_name, 0) + 1

            return {
                "total_events": len(self._events),
                "by_type": by_type,
                "session_id": self._session_id,
                "session_duration": time.time() - self._start_time,
                "export_console": self._export_console,
                "export_file": str(self._export_file) if self._export_file else None,
            }

    async def export_to_json(self, file_path: Path | str) -> None:
        """Export all events to JSON file.

        Args:
            file_path: Path to the output file.
        """
        events_data = []
        for event in self._events:
            events_data.append({
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp,
                "timestamp_iso": datetime.fromtimestamp(event.timestamp).isoformat(),
                "session_id": event.session_id,
                "user_id": event.user_id,
                "data": event.data,
            })

        file_path = Path(file_path)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "session_id": self._session_id,
                    "export_time": datetime.now().isoformat(),
                    "total_events": len(events_data),
                    "events": events_data,
                },
                f,
                indent=2,
            )

    def _print_event(self, event: TelemetryEvent) -> None:
        """Print event to console.

        Args:
            event: The event to print.
        """
        timestamp = datetime.fromtimestamp(event.timestamp).strftime("%H:%M:%S.%f")[
            :-3
        ]
        print(
            f"[TELEMETRY {timestamp}] {event.event_type.value}: {json.dumps(event.data)[:200]}"
        )

    async def _write_event_to_file(self, event: TelemetryEvent) -> None:
        """Write event to file.

        Args:
            event: The event to write.
        """
        if not self._export_file:
            return

        event_data = {
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "timestamp": event.timestamp,
            "session_id": event.session_id,
            "user_id": event.user_id,
            "data": event.data,
        }

        with open(self._export_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event_data) + "\n")

    async def clear(self) -> None:
        """Clear all events."""
        async with self._lock:
            self._events.clear()


_telemetry: TelemetryService | None = None


def get_telemetry() -> TelemetryService:
    """Get global telemetry instance.

    Returns:
        The global TelemetryService singleton.
    """
    global _telemetry
    if _telemetry is None:
        _telemetry = TelemetryService()
    return _telemetry