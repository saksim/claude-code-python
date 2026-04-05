"""Hook events for Claude Code Python.

Provides a generic event system for broadcasting hook execution events.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable


class HookOutcome(Enum):
    """Outcome of a hook execution."""

    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class HookStartedEvent:
    """Hook started event.

    Attributes:
        type: Event type identifier.
        hook_id: Unique hook identifier.
        hook_name: Name of the hook.
        hook_event: Event that triggered the hook.
        timestamp: ISO format timestamp.
    """

    type: str = "started"
    hook_id: str = ""
    hook_name: str = ""
    hook_event: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True, slots=True)
class HookProgressEvent:
    """Hook progress event.

    Attributes:
        type: Event type identifier.
        hook_id: Unique hook identifier.
        hook_name: Name of the hook.
        hook_event: Event that triggered the hook.
        stdout: Standard output from hook.
        stderr: Standard error from hook.
        output: Combined output.
        timestamp: ISO format timestamp.
    """

    type: str = "progress"
    hook_id: str = ""
    hook_name: str = ""
    hook_event: str = ""
    stdout: str = ""
    stderr: str = ""
    output: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True, slots=True)
class HookResponseEvent:
    """Hook response event.

    Attributes:
        type: Event type identifier.
        hook_id: Unique hook identifier.
        hook_name: Name of the hook.
        hook_event: Event that triggered the hook.
        output: Combined output.
        stdout: Standard output from hook.
        stderr: Standard error from hook.
        exit_code: Exit code from the hook.
        outcome: Outcome of the hook execution.
        timestamp: ISO format timestamp.
    """

    type: str = "response"
    hook_id: str = ""
    hook_name: str = ""
    hook_event: str = ""
    output: str = ""
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    outcome: HookOutcome = HookOutcome.SUCCESS
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


HookExecutionEvent = HookStartedEvent | HookProgressEvent | HookResponseEvent

HookEventHandler = Callable[[HookExecutionEvent], None]


class HookEventEmitter:
    """Hook event emitter for broadcasting hook execution events."""

    def __init__(self) -> None:
        """Initialize HookEventEmitter."""
        self._handler: HookEventHandler | None = None
        self._pending_events: list[HookExecutionEvent] = []
        self._all_events_enabled: bool = False
        self._always_emitted_events: frozenset[str] = frozenset(
            {"SessionStart", "Setup"}
        )

    def register_handler(self, handler: HookEventHandler | None) -> None:
        """Register an event handler.

        Args:
            handler: Callback function for events.
        """
        self._handler = handler

        if handler and self._pending_events:
            for event in self._pending_events:
                handler(event)
            self._pending_events.clear()

    def set_all_events_enabled(self, enabled: bool) -> None:
        """Enable or disable all hook events.

        Args:
            enabled: Whether to enable all events.
        """
        self._all_events_enabled = enabled

    def _should_emit(self, hook_event: str) -> bool:
        """Check if an event should be emitted.

        Args:
            hook_event: The hook event name.

        Returns:
            True if the event should be emitted.
        """
        if hook_event in self._always_emitted_events:
            return True
        return self._all_events_enabled

    def _emit(self, event: HookExecutionEvent) -> None:
        """Emit an event.

        Args:
            event: The event to emit.
        """
        if self._handler:
            self._handler(event)
        else:
            self._pending_events.append(event)
            if len(self._pending_events) > 100:
                self._pending_events.pop(0)

    def emit_started(
        self,
        hook_id: str,
        hook_name: str,
        hook_event: str,
    ) -> None:
        """Emit a hook started event.

        Args:
            hook_id: Unique hook identifier.
            hook_name: Name of the hook.
            hook_event: Event that triggered the hook.
        """
        if not self._should_emit(hook_event):
            return

        self._emit(
            HookStartedEvent(
                type="started",
                hook_id=hook_id,
                hook_name=hook_name,
                hook_event=hook_event,
            )
        )

    def emit_progress(
        self,
        hook_id: str,
        hook_name: str,
        hook_event: str,
        stdout: str = "",
        stderr: str = "",
        output: str = "",
    ) -> None:
        """Emit a hook progress event.

        Args:
            hook_id: Unique hook identifier.
            hook_name: Name of the hook.
            hook_event: Event that triggered the hook.
            stdout: Standard output from hook.
            stderr: Standard error from hook.
            output: Combined output.
        """
        if not self._should_emit(hook_event):
            return

        self._emit(
            HookProgressEvent(
                type="progress",
                hook_id=hook_id,
                hook_name=hook_name,
                hook_event=hook_event,
                stdout=stdout,
                stderr=stderr,
                output=output,
            )
        )

    def emit_response(
        self,
        hook_id: str,
        hook_name: str,
        hook_event: str,
        output: str = "",
        stdout: str = "",
        stderr: str = "",
        exit_code: int | None = None,
        outcome: HookOutcome = HookOutcome.SUCCESS,
    ) -> None:
        """Emit a hook response event.

        Args:
            hook_id: Unique hook identifier.
            hook_name: Name of the hook.
            hook_event: Event that triggered the hook.
            output: Combined output.
            stdout: Standard output from hook.
            stderr: Standard error from hook.
            exit_code: Exit code from the hook.
            outcome: Outcome of the hook execution.
        """
        self._emit(
            HookResponseEvent(
                type="response",
                hook_id=hook_id,
                hook_name=hook_name,
                hook_event=hook_event,
                output=output,
                stdout=stdout,
                stderr=stderr,
                exit_code=exit_code,
                outcome=outcome,
            )
        )

    def clear(self) -> None:
        """Clear all pending events and reset state."""
        self._handler = None
        self._pending_events.clear()
        self._all_events_enabled = False


_emitter: HookEventEmitter | None = None


def get_hook_emitter() -> HookEventEmitter:
    """Get the global hook event emitter.

    Returns:
        Global HookEventEmitter instance.
    """
    global _emitter
    if _emitter is None:
        _emitter = HookEventEmitter()
    return _emitter


def emit_hook_started(
    hook_id: str,
    hook_name: str,
    hook_event: str,
) -> None:
    """Emit a hook started event.

    Args:
        hook_id: Unique hook identifier.
        hook_name: Name of the hook.
        hook_event: Event that triggered the hook.
    """
    get_hook_emitter().emit_started(hook_id, hook_name, hook_event)


def emit_hook_progress(
    hook_id: str,
    hook_name: str,
    hook_event: str,
    stdout: str = "",
    stderr: str = "",
    output: str = "",
) -> None:
    """Emit a hook progress event.

    Args:
        hook_id: Unique hook identifier.
        hook_name: Name of the hook.
        hook_event: Event that triggered the hook.
        stdout: Standard output from hook.
        stderr: Standard error from hook.
        output: Combined output.
    """
    get_hook_emitter().emit_progress(
        hook_id, hook_name, hook_event, stdout, stderr, output
    )


def emit_hook_response(
    hook_id: str,
    hook_name: str,
    hook_event: str,
    output: str = "",
    stdout: str = "",
    stderr: str = "",
    exit_code: int | None = None,
    outcome: HookOutcome = HookOutcome.SUCCESS,
) -> None:
    """Emit a hook response event.

    Args:
        hook_id: Unique hook identifier.
        hook_name: Name of the hook.
        hook_event: Event that triggered the hook.
        output: Combined output.
        stdout: Standard output from hook.
        stderr: Standard error from hook.
        exit_code: Exit code from the hook.
        outcome: Outcome of the hook execution.
    """
    get_hook_emitter().emit_response(
        hook_id, hook_name, hook_event, output, stdout, stderr, exit_code, outcome
    )