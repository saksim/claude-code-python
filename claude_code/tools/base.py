"""
Claude Code Python - Tool Base Classes
Core interfaces for the tool system.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Protocol pattern for type safety
- Dataclass for immutable data structures
"""

from __future__ import annotations

import os
import asyncio
import json
from typing import Any, Optional, Callable, Awaitable, TYPE_CHECKING
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from claude_code.tools.registry import ToolRegistry


class ToolInput(BaseModel):
    """Input to a tool call.
    
    Following Pydantic best practices for validation.
    """
    data: dict[str, Any]
    tool_use_id: str


class ToolResult(BaseModel):
    """Result from a tool execution.
    
    Following Pydantic best practices:
    - Type validation
    - Default values
    - Serialization support
    """
    content: str | list[dict[str, Any]] = ""
    is_error: bool = False
    tool_use_id: str = ""
    
    def to_api_format(self) -> dict[str, Any]:
        """Convert to API tool_result format.
        
        Returns:
            Dictionary in API format.
        """
        if isinstance(self.content, str):
            return {
                "type": "tool_result",
                "tool_use_id": self.tool_use_id,
                "content": self.content,
                "is_error": self.is_error,
            }
        return {
            "type": "tool_result",
            "tool_use_id": self.tool_use_id,
            "content": self.content,
            "is_error": self.is_error,
        }


class ToolProgress(BaseModel):
    """Progress update from a tool.
    
    Used for long-running operations.
    """
    tool_use_id: str
    data: dict[str, Any] = Field(default_factory=dict)


# Type alias for progress callback
ToolCallback = Callable[[ToolProgress], Awaitable[None]]


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Definition of a tool for the API.
    
    Using frozen dataclass with slots for immutability and memory efficiency.
    """
    name: str
    description: str
    input_schema: dict[str, Any]
    
    # Optional features
    aliases: list[str] = field(default_factory=list)
    max_result_size_chars: int = 100000
    
    # Tool characteristics
    is_read_only: bool = False
    is_concurrency_safe: bool = False
    is_destructive: bool = False
    requires_user_interaction: bool = False


@dataclass
class ToolContext:
    """Context available during tool execution.
    
    Following Python best practices:
    - Type hints
    - Docstrings
    - Sensible defaults
    - Config propagation from main conversation to tools
    """
    working_directory: str
    environment: dict[str, str] = field(default_factory=dict)
    read_file_cache: dict[str, str] = field(default_factory=dict)
    abort_signal: Optional[asyncio.Event] = None
    # Config propagation fields
    permission_mode: str = "default"
    always_allow: list[str] = field(default_factory=list)
    always_deny: list[str] = field(default_factory=list)
    model: Optional[str] = None
    session_id: Optional[str] = None
    
    def get_env(self, key: str, default: str = "") -> str:
        """Get environment variable.
        
        Args:
            key: Environment variable name.
            default: Default value if not found.
            
        Returns:
            Environment variable value or default.
        """
        return self.environment.get(key, os.environ.get(key, default))
    
    def should_abort(self) -> bool:
        """Check if execution should be aborted.
        
        Returns:
            True if abort signal is set.
        """
        return self.abort_signal is not None and self.abort_signal.is_set()
    
    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if a tool is allowed based on permission context.
        
        Args:
            tool_name: Name of the tool to check.
            
        Returns:
            True if the tool is allowed.
        """
        if tool_name in self.always_deny:
            return False
        if tool_name in self.always_allow:
            return True
        if self.permission_mode == "yolo":
            return True
        if self.permission_mode == "plan":
            return tool_name in ("read", "glob", "grep", "web_search", "web_fetch")
        return True


class Tool(ABC):
    """
    Base class for all tools.
    
    Tools are the primary way Claude interacts with the outside world.
    Each tool implements a specific capability like reading files,
    running commands, searching the web, etc.
    
    Following TOP Python Dev standards:
    - Abstract base class with ABC
    - Clear docstrings
    - Type hints throughout
    - Property-based interface
    """
    
    def __init__(self) -> None:
        """Initialize tool with cached definition."""
        self._definition: Optional[ToolDefinition] = None
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Tool name, must be unique.
        
        Returns:
            Unique tool name.
        """
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the tool.
        
        Returns:
            Tool description for API.
        """
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> dict[str, Any]:
        """JSON Schema for tool input.
        
        Returns:
            JSON schema dictionary.
        """
        pass
    
    def get_definition(self) -> ToolDefinition:
        """Get the tool definition for API.
        
        Returns:
            Cached ToolDefinition.
        """
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
        """Whether this tool only reads data, never modifies.
        
        Returns:
            True if tool is read-only.
        """
        return False
    
    def is_concurrency_safe(self) -> bool:
        """Whether multiple instances can run concurrently.
        
        Returns:
            True if tool is thread/concurrency safe.
        """
        return False
    
    def is_destructive(self) -> bool:
        """Whether this tool performs irreversible operations.
        
        Returns:
            True if tool is destructive.
        """
        return False
    
    def requires_user_interaction(self) -> bool:
        """Whether this tool requires user interaction.
        
        Returns:
            True if tool requires user interaction.
        """
        return False
    
    @property
    def max_result_size_chars(self) -> int:
        """Maximum size for tool results in characters.
        
        Returns:
            Maximum result size.
        """
        return 100000
    
    @abstractmethod
    async def execute(
        self,
        input_data: dict[str, Any],
        context: ToolContext,
        on_progress: Optional[ToolCallback] = None,
    ) -> ToolResult:
        """Execute the tool with given input.
        
        Args:
            input_data: Parsed input matching input_schema.
            context: Execution context.
            on_progress: Optional callback for progress updates.
            
        Returns:
            Tool result.
        """
        pass
    
    def validate_input(self, input_data: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate input before execution.
        
        Args:
            input_data: Input data to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        return True, None
    
    def prepare_permission_check(self, input_data: dict[str, Any]) -> Optional[Callable[[dict[str, Any]], bool]]:
        """Return a matcher for permission rules.
        
        Args:
            input_data: Input data for permission check.
            
        Returns:
            Permission matcher function or None.
        """
        return None
