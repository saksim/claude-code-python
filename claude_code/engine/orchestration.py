"""Tool Orchestration for Claude Code Python.

Complete tool orchestration system - modeled after TS version design.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable
from uuid import uuid4


class ToolExecutionPhase(Enum):
    """Tool execution phase."""

    PRE_EXECUTION = "pre_execution"
    EXECUTION = "execution"
    POST_EXECUTION = "post_execution"
    ON_PROGRESS = "on_progress"
    ON_COMPLETE = "on_complete"


@dataclass(frozen=True, slots=True)
class ToolCall:
    """Tool call request.

    Attributes:
        id: Unique identifier for the tool call.
        name: Name of the tool to execute.
        input_data: Input data for the tool.
        context: Execution context dictionary.
        started_at: When the execution started.
        completed_at: When the execution completed.
    """

    id: str
    name: str
    input_data: dict[str, Any]
    context: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Tool execution result.

    Attributes:
        call_id: ID of the tool call.
        tool_name: Name of the executed tool.
        content: Result content.
        is_error: Whether the execution resulted in an error.
        error_message: Error message if failed.
        execution_time_ms: Execution time in milliseconds.
        tokens_used: Number of tokens used.
        metadata: Additional metadata.
    """

    call_id: str
    tool_name: str
    content: Any
    is_error: bool = False
    error_message: str | None = None
    execution_time_ms: float = 0
    tokens_used: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


class ToolOrchestrator:
    """Tool orchestrator - manages tool execution flow.

    Modeled after the TypeScript version design with hooks,
    parallel/sequential execution, and progress tracking.
    """

    def __init__(
        self,
        tool_registry: Any | None = None,
        permission_checker: Any | None = None,
    ) -> None:
        """Initialize ToolOrchestrator.

        Args:
            tool_registry: Registry for looking up tools.
            permission_checker: Permission checker for tool access.
        """
        self._registry = tool_registry
        self._permission_checker = permission_checker
        self._hooks: dict[ToolExecutionPhase, list[Callable[..., Awaitable[None]]]] = {
            phase: [] for phase in ToolExecutionPhase
        }
        self._active_calls: dict[str, ToolCall] = {}
        self._callbacks: dict[str, list[Callable[[dict[str, Any]], None]]] = {}

    def register_tool(self, tool: Any) -> None:
        """Register a tool.

        Args:
            tool: Tool instance to register.
        """
        if self._registry:
            self._registry.register(tool)

    def register_hook(
        self,
        phase: ToolExecutionPhase,
        handler: Callable[[ToolCall], Awaitable[None]],
    ) -> None:
        """Register a hook for a specific execution phase.

        Args:
            phase: The execution phase to hook into.
            handler: Async handler function to call.
        """
        self._hooks[phase].append(handler)

    async def execute_tool(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> ToolResult:
        """Execute a tool.

        Args:
            tool_name: Name of the tool to execute.
            input_data: Input data for the tool.
            context: Execution context.

        Returns:
            ToolResult with execution outcome.
        """
        call = ToolCall(
            id=str(uuid4())[:8],
            name=tool_name,
            input_data=input_data,
            context=context or {},
            started_at=datetime.now(),
        )

        self._active_calls[call.id] = call

        try:
            await self._run_hooks(ToolExecutionPhase.PRE_EXECUTION, call)

            if self._permission_checker:
                self._permission_checker.check_or_raise(tool_name)

            tool = self._get_tool(tool_name)
            if not tool:
                return ToolResult(
                    call_id=call.id,
                    tool_name=tool_name,
                    content=None,
                    is_error=True,
                    error_message=f"Tool not found: {tool_name}",
                )

            result = await tool.execute(input_data, context)

            call.completed_at = datetime.now()
            execution_time = 0.0
            if call.started_at and call.completed_at:
                execution_time = (
                    call.completed_at - call.started_at
                ).total_seconds() * 1000

            tool_result = ToolResult(
                call_id=call.id,
                tool_name=tool_name,
                content=result.content if hasattr(result, "content") else result,
                is_error=result.is_error if hasattr(result, "is_error") else False,
                execution_time_ms=execution_time,
                metadata={"tool_name": tool_name},
            )

            await self._run_hooks(ToolExecutionPhase.POST_EXECUTION, call)

            return tool_result

        except Exception as e:
            return ToolResult(
                call_id=call.id,
                tool_name=tool_name,
                content=None,
                is_error=True,
                error_message=str(e),
            )
        finally:
            self._active_calls.pop(call.id, None)

    async def execute_parallel(
        self,
        calls: list[tuple[str, dict[str, Any]]],
        context: dict[str, Any] | None = None,
    ) -> list[ToolResult]:
        """Execute multiple tools in parallel.

        Args:
            calls: List of (tool_name, input_data) tuples.
            context: Execution context.

        Returns:
            List of ToolResults in the same order as calls.
        """
        tasks = [
            self.execute_tool(name, data, context)
            for name, data in calls
        ]
        return await asyncio.gather(*tasks)

    async def execute_sequential(
        self,
        calls: list[tuple[str, dict[str, Any]]],
        context: dict[str, Any] | None = None,
    ) -> list[ToolResult]:
        """Execute multiple tools sequentially.

        Stops on first error.

        Args:
            calls: List of (tool_name, input_data) tuples.
            context: Execution context.

        Returns:
            List of ToolResults.
        """
        results: list[ToolResult] = []
        for name, data in calls:
            result = await self.execute_tool(name, data, context)
            results.append(result)
            if result.is_error:
                break
        return results

    def _get_tool(self, name: str) -> Any:
        """Get a tool by name.

        Args:
            name: Tool name to look up.

        Returns:
            Tool instance or None if not found.
        """
        if self._registry:
            return self._registry.get(name)
        return None

    async def _run_hooks(self, phase: ToolExecutionPhase, call: ToolCall) -> None:
        """Run all hooks for a phase.

        Args:
            phase: The execution phase.
            call: The tool call being executed.
        """
        for handler in self._hooks.get(phase, []):
            try:
                await handler(call)
            except Exception:
                pass

    def get_active_calls(self) -> dict[str, ToolCall]:
        """Get all active tool calls.

        Returns:
            Dictionary of active calls by ID.
        """
        return self._active_calls.copy()

    def on_progress(
        self,
        call_id: str,
        callback: Callable[[dict[str, Any]], None],
    ) -> None:
        """Register a progress callback.

        Args:
            call_id: ID of the tool call.
            callback: Callback function for progress updates.
        """
        if call_id not in self._callbacks:
            self._callbacks[call_id] = []
        self._callbacks[call_id].append(callback)

    async def emit_progress(self, call_id: str, data: dict[str, Any]) -> None:
        """Emit a progress event.

        Args:
            call_id: ID of the tool call.
            data: Progress data to emit.
        """
        for callback in self._callbacks.get(call_id, []):
            try:
                callback(data)
            except Exception:
                pass


class StreamingToolExecutor:
    """Streaming tool executor - supports real-time progress output."""

    def __init__(self, orchestrator: ToolOrchestrator) -> None:
        """Initialize StreamingToolExecutor.

        Args:
            orchestrator: The tool orchestrator to use.
        """
        self._orchestrator = orchestrator

    async def execute_streaming(
        self,
        tool_name: str,
        input_data: dict[str, Any],
        context: dict[str, Any] | None = None,
        on_progress: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    ) -> ToolResult:
        """Execute a tool with streaming progress.

        Args:
            tool_name: Name of the tool to execute.
            input_data: Input data for the tool.
            context: Execution context.
            on_progress: Async callback for progress updates.

        Returns:
            ToolResult with execution outcome.
        """
        call_id = str(uuid4())[:8]

        if on_progress:
            self._orchestrator.on_progress(call_id, on_progress)

        await self._orchestrator.emit_progress(
            call_id,
            {
                "type": "start",
                "tool": tool_name,
            },
        )

        result = await self._orchestrator.execute_tool(
            tool_name, input_data, context
        )

        await self._orchestrator.emit_progress(
            call_id,
            {
                "type": "complete",
                "result": result.content if not result.is_error else None,
                "error": result.error_message if result.is_error else None,
            },
        )

        return result


__all__ = [
    "ToolExecutionPhase",
    "ToolCall",
    "ToolResult",
    "ToolOrchestrator",
    "StreamingToolExecutor",
]