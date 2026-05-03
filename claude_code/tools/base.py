"""
Claude Code Python - Tool Base Classes
Core interfaces for the tool system.
"""

from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from claude_code.tools.registry import ToolRegistry


class ToolInput(BaseModel):
    """Input to a tool call."""

    data: dict[str, Any]
    tool_use_id: str


class ToolResult(BaseModel):
    """Result from a tool execution."""

    content: str | list[dict[str, Any]] = ""
    is_error: bool = False
    tool_use_id: str = ""

    def to_api_format(self) -> dict[str, Any]:
        """Convert this result to API tool_result format."""
        return {
            "type": "tool_result",
            "tool_use_id": self.tool_use_id,
            "content": self.content,
            "is_error": self.is_error,
        }


class ToolProgress(BaseModel):
    """Progress update from a tool."""

    tool_use_id: str
    data: dict[str, Any] = Field(default_factory=dict)


ToolCallback = Callable[[ToolProgress], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Definition of a tool for API exposure."""

    name: str
    description: str
    input_schema: dict[str, Any]

    aliases: list[str] = field(default_factory=list)
    max_result_size_chars: int = 100000

    is_read_only: bool = False
    is_concurrency_safe: bool = False
    is_destructive: bool = False
    requires_user_interaction: bool = False


_PLAN_ALLOWED_TOOLS: frozenset[str] = frozenset(
    {"read", "glob", "grep", "web_search", "web_fetch"}
)


@dataclass
class ToolContext:
    """Context available during tool execution."""

    working_directory: str
    environment: dict[str, str] = field(default_factory=dict)
    read_file_cache: dict[str, str] = field(default_factory=dict)
    abort_signal: Optional[asyncio.Event] = None

    permission_mode: str = "default"
    always_allow: list[str] = field(default_factory=list)
    always_deny: list[str] = field(default_factory=list)
    model: Optional[str] = None
    session_id: Optional[str] = None
    memory_scope: Optional[str] = None
    conversation_id: Optional[str] = None
    api_provider: Optional[str] = None
    task_manager: Any = None
    tool_registry: Optional["ToolRegistry"] = None

    _allow_set: Optional[frozenset[str]] = field(default=None, repr=False)
    _deny_set: Optional[frozenset[str]] = field(default=None, repr=False)

    def get_env(self, key: str, default: str = "") -> str:
        """Get environment variable from context, fallback to process env."""
        return self.environment.get(key, os.environ.get(key, default))

    def should_abort(self) -> bool:
        """Check whether execution should abort."""
        return self.abort_signal is not None and self.abort_signal.is_set()

    def _ensure_permission_cache(self) -> None:
        """Build permission caches once for O(1) checks."""
        if self._allow_set is None:
            self._allow_set = frozenset(self.always_allow)
        if self._deny_set is None:
            self._deny_set = frozenset(self.always_deny)

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check whether a tool is allowed under the current permission context."""
        self._ensure_permission_cache()

        if tool_name in self._deny_set:
            return False
        if tool_name in self._allow_set:
            return True

        if self.permission_mode == "yolo":
            return True
        if self.permission_mode == "plan":
            return tool_name in _PLAN_ALLOWED_TOOLS
        return True


class Tool(ABC):
    """Base class for all tools."""

    def __init__(self) -> None:
        self._definition: Optional[ToolDefinition] = None

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool name."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Tool description for model exposure."""

    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON schema describing tool input."""

    def get_definition(self) -> ToolDefinition:
        """Get cached tool definition."""
        if self._definition is None:
            self._definition = ToolDefinition(
                name=self.name,
                description=self.description,
                input_schema=self.input_schema,
                is_read_only=self.is_read_only(),
                is_concurrency_safe=self.is_concurrency_safe(),
                is_destructive=self.is_destructive(),
                requires_user_interaction=self.requires_user_interaction(),
                max_result_size_chars=self.max_result_size_chars,
            )
        return self._definition

    def is_read_only(self) -> bool:
        return False

    def is_concurrency_safe(self) -> bool:
        return False

    def is_destructive(self) -> bool:
        return False

    def requires_user_interaction(self) -> bool:
        return False

    @property
    def max_result_size_chars(self) -> int:
        return 100000

    @abstractmethod
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute tool logic."""

    def validate_input(self, input_data: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate tool input before execution."""
        return True, None

    def prepare_permission_check(
        self, input_data: dict[str, Any]
    ) -> Optional[Callable[[dict[str, Any]], bool]]:
        """Optional matcher used by permission policy evaluation."""
        return None


__all__ = [
    "ToolInput",
    "ToolResult",
    "ToolProgress",
    "ToolCallback",
    "ToolDefinition",
    "ToolContext",
    "Tool",
]
