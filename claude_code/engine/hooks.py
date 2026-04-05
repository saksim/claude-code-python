"""
Claude Code Python - Hook Execution Pipeline
Complete hook execution pipeline - inspired by TS version design.
Supports PreToolUse, PostToolUse, and other hook events.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns
- Async/await patterns
"""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum


class HookEvent(Enum):
    """Hook event types.
    
    Attributes:
        PRE_TOOL_USE: Before tool execution
        POST_TOOL_USE: After tool execution
        PRE_MESSAGE: Before message processing
        POST_MESSAGE: After message processing
        PRE_QUERY: Before query execution
        POST_QUERY: After query execution
        ON_ERROR: On error occurrence
        FILE_CHANGED: When files change
        SESSION_START: Session start
        SESSION_END: Session end
    """
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    PRE_MESSAGE = "PreMessage"
    POST_MESSAGE = "PostMessage"
    PRE_QUERY = "PreQuery"
    POST_QUERY = "PostQuery"
    ON_ERROR = "OnError"
    FILE_CHANGED = "FileChanged"
    SESSION_START = "SessionStart"
    SESSION_END = "SessionEnd"


class HookAction(Enum):
    """Hook execution action.
    
    Attributes:
        CONTINUE: Continue execution normally
        DENY: Deny the operation
        MODIFY: Modify the input/result
        STOP: Stop further processing
    """
    CONTINUE = "continue"
    DENY = "deny"
    MODIFY = "modify"
    STOP = "stop"


@dataclass(frozen=True, slots=True)
class HookContext:
    """Context passed to hook handlers.
    
    Contains all information about the event being hooked.
    
    Attributes:
        event: The hook event type
        tool_name: Name of the tool (for tool hooks)
        tool_input: Input data for the tool
        tool_result: Result from tool execution
        message: Message content (for message hooks)
        session_id: Current session identifier
        working_directory: Current working directory
        metadata: Additional metadata
    """
    event: HookEvent
    tool_name: Optional[str] = None
    tool_input: Optional[dict[str, Any]] = None
    tool_result: Optional[Any] = None
    message: Optional[str] = None
    session_id: Optional[str] = None
    working_directory: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HookResponse:
    """Response from hook execution.
    
    Contains the action to take and optional modifications.
    
    Attributes:
        action: Action to take (continue, deny, modify, stop)
        modified_input: Modified tool input (if any)
        modified_result: Modified tool result (if any)
        output: Optional output message
        error: Error message (if any)
    """
    action: HookAction
    modified_input: Optional[dict[str, Any]] = None
    modified_result: Optional[Any] = None
    output: Optional[str] = None
    error: Optional[str] = None


@dataclass(frozen=True, slots=True)
class HookConfig:
    """Configuration for an external hook script.
    
    Attributes:
        command: Command to execute
        event: Event to trigger on
        match_pattern: Optional regex pattern to match
        enabled: Whether hook is enabled
        timeout_ms: Timeout in milliseconds
    """
    command: str
    event: HookEvent
    match_pattern: Optional[str] = None
    enabled: bool = True
    timeout_ms: int = 30000


class HookExecutor:
    """Hook executor - runs external hook scripts.
    
    Inspired by TS version's toolHooks.ts design. Manages registration
    and execution of both Python and external script hooks.
    
    Attributes:
        _working_directory: Working directory for hook execution
        _hooks: Dictionary of external hook configurations
        _python_hooks: Dictionary of Python hook handlers
    
    Example:
        >>> executor = HookExecutor("/project")
        >>> executor.register_python_hook(
        ...     HookEvent.PRE_TOOL_USE,
        ...     my_handler
        ... )
        >>> response = await executor.execute_hooks(HookEvent.PRE_TOOL_USE, context)
    """
    
    def __init__(self, working_directory: Optional[str] = None) -> None:
        """Initialize hook executor.
        
        Args:
            working_directory: Working directory for hook scripts
        """
        self._working_directory = Path(working_directory or Path.cwd())
        self._hooks: dict[HookEvent, list[HookConfig]] = {
            event: [] for event in HookEvent
        }
        self._python_hooks: dict[HookEvent, list[Callable[[HookContext], Awaitable[HookResponse]]]] = {
            event: [] for event in HookEvent
        }
    
    def register_hook(self, config: HookConfig) -> None:
        """Register an external hook.
        
        Args:
            config: Hook configuration
        """
        self._hooks[config.event].append(config)
    
    def register_python_hook(
        self,
        event: HookEvent,
        handler: Callable[[HookContext], Awaitable[HookResponse]],
    ) -> None:
        """Register a Python hook handler.
        
        Args:
            event: Event to handle
            handler: Async function to handle the event
        """
        self._python_hooks[event].append(handler)
    
    async def execute_hooks(
        self,
        event: HookEvent,
        context: HookContext,
    ) -> HookResponse:
        """Execute all hooks for an event.
        
        Args:
            event: Hook event to process
            context: Hook context with event data
            
        Returns:
            Final HookResponse after all handlers
        """
        responses: list[HookResponse] = []
        
        # Execute Python hooks
        for handler in self._python_hooks.get(event, []):
            try:
                response = await handler(context)
                responses.append(response)
                
                if response.action == HookAction.DENY:
                    return response
                
                if response.action == HookAction.STOP:
                    break
                    
            except Exception as e:
                responses.append(HookResponse(
                    action=HookAction.CONTINUE,
                    error=str(e),
                ))
        
        # Execute external hooks
        for config in self._hooks.get(event, []):
            if not config.enabled:
                continue
            
            if config.match_pattern:
                if not self._matches_pattern(context, config.match_pattern):
                    continue
            
            try:
                response = await self._execute_hook_script(config, context)
                responses.append(response)
                
                if response.action == HookAction.DENY:
                    return response
                    
            except Exception as e:
                responses.append(HookResponse(
                    action=HookAction.CONTINUE,
                    error=str(e),
                ))
        
        # Apply modifications from last response
        if responses:
            last_response = responses[-1]
            if last_response.modified_input:
                context.tool_input = last_response.modified_input
            if last_response.modified_result:
                context.tool_result = last_response.modified_result
        
        return HookResponse(action=HookAction.CONTINUE)
    
    async def _execute_hook_script(
        self,
        config: HookConfig,
        context: HookContext,
    ) -> HookResponse:
        """Execute an external hook script.
        
        Args:
            config: Hook configuration
            context: Hook context
            
        Returns:
            HookResponse from the script
        """
        hook_input = self._build_hook_input(config.event, context)
        
        try:
            process = await asyncio.create_subprocess_exec(
                *config.command.split(),
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._working_directory),
            )
            
            result = await asyncio.wait_for(
                process.communicate(input=json.dumps(hook_input).encode()),
                timeout=config.timeout_ms / 1000,
            )
            
            stdout, stderr = result
            
            if process.returncode == 0:
                try:
                    output = json.loads(stdout)
                    return HookResponse(
                        action=HookAction(output.get("action", "continue")),
                        modified_input=output.get("modifiedInput"),
                        modified_result=output.get("modifiedResult"),
                        output=output.get("output"),
                    )
                except json.JSONDecodeError:
                    pass
            
            return HookResponse(
                action=HookAction.CONTINUE,
                error=stderr.decode() if stderr else "Hook failed",
            )
            
        except asyncio.TimeoutError:
            return HookResponse(
                action=HookAction.CONTINUE,
                error=f"Hook timeout after {config.timeout_ms}ms",
            )
    
    def _build_hook_input(self, event: HookEvent, context: HookContext) -> dict[str, Any]:
        """Build input for hook script.
        
        Args:
            event: Hook event
            context: Hook context
            
        Returns:
            Dictionary to pass to hook script
        """
        hook_input: dict[str, Any] = {
            "event": event.value,
            "session_id": context.session_id,
            "working_directory": context.working_directory,
            "timestamp": datetime.now().isoformat(),
        }
        
        if context.tool_name:
            hook_input["tool_name"] = context.tool_name
        
        if context.tool_input:
            hook_input["tool_input"] = context.tool_input
        
        if context.tool_result:
            hook_input["tool_result"] = context.tool_result
        
        if context.message:
            hook_input["message"] = context.message
        
        hook_input.update(context.metadata)
        
        return hook_input
    
    def _matches_pattern(self, context: HookContext, pattern: str) -> bool:
        """Check if context matches pattern.
        
        Args:
            context: Hook context
            pattern: Regex pattern
            
        Returns:
            True if context matches pattern
        """
        try:
            if context.tool_name:
                return bool(re.match(pattern, context.tool_name))
            return False
        except re.error:
            return False
    
    def get_registered_hooks(self) -> dict[str, list[dict[str, Any]]]:
        """Get all registered hooks.
        
        Returns:
            Dictionary of event to hook configurations
        """
        result: dict[str, list[dict[str, Any]]] = {}
        for event, hooks in self._hooks.items():
            if hooks:
                result[event.value] = [
                    {"command": h.command, "enabled": h.enabled}
                    for h in hooks
                ]
        return result


class PreToolUseHandler:
    """PreToolUse hook handler.
    
    Executes before a tool is called, allowing modification
    or denial of the tool execution.
    """
    
    def __init__(self, executor: HookExecutor) -> None:
        """Initialize handler.
        
        Args:
            executor: Hook executor to use
        """
        self._executor = executor
    
    async def handle(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        context: HookContext,
    ) -> tuple[bool, dict[str, Any]]:
        """Handle PreToolUse event.
        
        Args:
            tool_name: Name of the tool
            tool_input: Input to the tool
            context: Hook context
            
        Returns:
            Tuple of (allowed, modified_input)
        """
        context.tool_name = tool_name
        context.tool_input = tool_input
        
        response = await self._executor.execute_hooks(
            HookEvent.PRE_TOOL_USE,
            context,
        )
        
        if response.action == HookAction.DENY:
            return False, tool_input
        
        if response.modified_input:
            return True, response.modified_input
        
        return True, tool_input


class PostToolUseHandler:
    """PostToolUse hook handler.
    
    Executes after a tool completes, allowing modification
    of the result.
    """
    
    def __init__(self, executor: HookExecutor) -> None:
        """Initialize handler.
        
        Args:
            executor: Hook executor to use
        """
        self._executor = executor
    
    async def handle(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: Any,
        context: HookContext,
    ) -> Any:
        """Handle PostToolUse event.
        
        Args:
            tool_name: Name of the tool
            tool_input: Input to the tool
            tool_result: Result from tool execution
            context: Hook context
            
        Returns:
            Modified result (or original if no modification)
        """
        context.tool_name = tool_name
        context.tool_input = tool_input
        context.tool_result = tool_result
        
        response = await self._executor.execute_hooks(
            HookEvent.POST_TOOL_USE,
            context,
        )
        
        return response.modified_result if response.modified_result else tool_result


_default_executor: Optional[HookExecutor] = None


def get_hook_executor(working_directory: Optional[str] = None) -> HookExecutor:
    """Get the default hook executor.
    
    Args:
        working_directory: Optional working directory
        
    Returns:
        Global HookExecutor instance
    """
    global _default_executor
    if _default_executor is None:
        _default_executor = HookExecutor(working_directory)
    return _default_executor


__all__ = [
    "HookEvent",
    "HookAction",
    "HookContext",
    "HookResponse",
    "HookConfig",
    "HookExecutor",
    "PreToolUseHandler",
    "PostToolUseHandler",
    "get_hook_executor",
]
