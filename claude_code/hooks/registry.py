"""
Hook registry for Claude Code Python.

Manages registration and execution of hooks.
"""

import asyncio
import uuid
import os
import shlex
from typing import Callable, Optional, Any, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from claude_code.hooks.events import (
    HookEventEmitter,
    HookOutcome,
    get_hook_emitter,
    emit_hook_started,
    emit_hook_progress,
    emit_hook_response,
)


class HookEvent(Enum):
    """Hook event types."""
    # Lifecycle hooks
    SESSION_START = "SessionStart"
    SESSION_END = "SessionEnd"
    SETUP = "Setup"
    TEARDOWN = "Teardown"
    
    # Tool hooks
    PRE_TOOL_CALL = "PreToolCall"
    POST_TOOL_CALL = "PostToolCall"
    
    # Message hooks
    PRE_MESSAGE = "PreMessage"
    POST_MESSAGE = "PostMessage"
    
    # Query hooks
    PRE_QUERY = "PreQuery"
    POST_QUERY = "PostQuery"
    
    # Error hooks
    ON_ERROR = "OnError"
    
    # File hooks
    FILE_CHANGED = "FileChanged"
    
    # Custom hooks
    CUSTOM = "Custom"


@dataclass(frozen=True, slots=True)
class HookConfig:
    """Configuration for a hook."""
    name: str
    command: str
    event: str
    timeout_ms: int = 15000
    async_timeout_ms: int = 15000
    enabled: bool = True
    cwd: Optional[str] = None
    env: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HookResult:
    """Result from hook execution."""
    hook_id: str
    hook_name: str
    hook_event: str
    success: bool
    output: str = ""
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    error: Optional[str] = None
    duration_ms: float = 0


@dataclass(frozen=True, slots=True)
class PendingAsyncHook:
    """A pending async hook."""
    process_id: str
    hook_id: str
    hook_name: str
    hook_event: str
    tool_name: Optional[str] = None
    plugin_id: Optional[str] = None
    start_time: float = field(default_factory=datetime.now().timestamp)
    timeout_ms: int = 15000
    command: str = ""
    response_sent: bool = False
    process: Optional[asyncio.subprocess.Process] = None
    progress_task: Optional[asyncio.Task] = None


class HookRegistry:
    """
    Registry for managing hooks.
    
    Handles hook registration, configuration, and execution.
    """
    
    def __init__(self, emitter: Optional[HookEventEmitter] = None):
        self._hooks: dict[str, HookConfig] = {}
        self._emitter = emitter or get_hook_emitter()
        self._pending_async_hooks: dict[str, PendingAsyncHook] = {}
        self._lock = asyncio.Lock()
    
    def register(self, config: HookConfig) -> None:
        """Register a hook."""
        self._hooks[config.name] = config
    
    def unregister(self, name: str) -> bool:
        """Unregister a hook."""
        if name in self._hooks:
            del self._hooks[name]
            return True
        return False
    
    def get(self, name: str) -> Optional[HookConfig]:
        """Get a hook by name."""
        return self._hooks.get(name)
    
    def list_by_event(self, event: str) -> list[HookConfig]:
        """List all hooks for a specific event."""
        return [h for h in self._hooks.values() if h.event == event and h.enabled]
    
    def list_all(self) -> list[HookConfig]:
        """List all registered hooks."""
        return list(self._hooks.values())
    
    async def execute(
        self,
        hook_name: str,
        context: Optional[dict] = None,
    ) -> HookResult:
        """Execute a synchronous hook."""
        hook = self._hooks.get(hook_name)
        if not hook:
            return HookResult(
                hook_id="",
                hook_name=hook_name,
                hook_event="",
                success=False,
                error=f"Hook not found: {hook_name}",
            )
        
        return await self._execute_hook(hook, context or {})
    
    async def execute_for_event(
        self,
        event: str,
        context: Optional[dict] = None,
    ) -> list[HookResult]:
        """Execute all hooks for a specific event."""
        hooks = self.list_by_event(event)
        results = []
        
        for hook in hooks:
            result = await self._execute_hook(hook, context or {})
            results.append(result)
        
        return results
    
    async def _execute_hook(
        self,
        hook: HookConfig,
        context: dict,
    ) -> HookResult:
        """Execute a single hook."""
        import time
        start = time.time()
        
        hook_id = str(uuid.uuid4())
        
        emit_hook_started(hook_id, hook.name, hook.event)
        
        try:
            # Expand command with context variables
            command = self._expand_command(hook.command, context)
            
            # Execute the command
            process = await asyncio.create_subprocess_exec(
                *shlex.split(command) if os.name != 'nt' else command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=hook.cwd or os.getcwd(),
                env={**os.environ, **hook.env},
            )
            
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                process.communicate(),
                timeout=hook.timeout_ms / 1000,
            )
            
            stdout = stdout_bytes.decode('utf-8', errors='replace')
            stderr = stderr_bytes.decode('utf-8', errors='replace')
            output = stdout + stderr
            
            success = process.returncode == 0
            duration_ms = (time.time() - start) * 1000
            
            emit_hook_response(
                hook_id,
                hook.name,
                hook.event,
                output=output,
                stdout=stdout,
                stderr=stderr,
                exit_code=process.returncode,
                outcome=HookOutcome.SUCCESS if success else HookOutcome.ERROR,
            )
            
            return HookResult(
                hook_id=hook_id,
                hook_name=hook.name,
                hook_event=hook.event,
                success=success,
                output=output,
                stdout=stdout,
                stderr=stderr,
                exit_code=process.returncode,
                duration_ms=duration_ms,
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start) * 1000
            error = f"Hook timed out after {hook.timeout_ms}ms"
            
            emit_hook_response(
                hook_id,
                hook.name,
                hook.event,
                output="",
                stderr=error,
                outcome=HookOutcome.ERROR,
            )
            
            return HookResult(
                hook_id=hook_id,
                hook_name=hook.name,
                hook_event=hook.event,
                success=False,
                error=error,
                duration_ms=duration_ms,
            )
            
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            
            emit_hook_response(
                hook_id,
                hook.name,
                hook.event,
                stderr=str(e),
                outcome=HookOutcome.ERROR,
            )
            
            return HookResult(
                hook_id=hook_id,
                hook_name=hook.name,
                hook_event=hook.event,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )
    
    def _expand_command(self, command: str, context: dict) -> str:
        """Expand command with context variables."""
        result = command
        for key, value in context.items():
            result = result.replace(f"${{{key}}}", str(value))
            result = result.replace(f"${key}", str(value))
        return result
    
    async def check_pending_hooks(self) -> list[dict]:
        """Check for completed async hooks."""
        completed = []
        
        async with self._lock:
            for process_id, hook in list(self._pending_async_hooks.items()):
                if hook.process and hook.process.returncode is not None:
                    stdout_bytes = await hook.process.stdout.read() if hook.process.stdout else b''
                    stderr_bytes = await hook.process.stderr.read() if hook.process.stderr else b''
                    
                    stdout = stdout_bytes.decode('utf-8', errors='replace')
                    stderr = stderr_bytes.decode('utf-8', errors='replace')
                    
                    completed.append({
                        "process_id": process_id,
                        "hook_id": hook.hook_id,
                        "hook_name": hook.hook_name,
                        "hook_event": hook.hook_event,
                        "stdout": stdout,
                        "stderr": stderr,
                        "exit_code": hook.process.returncode,
                    })
                    
                    del self._pending_async_hooks[process_id]
        
        return completed
    
    def clear(self) -> None:
        """Clear all hooks."""
        self._hooks.clear()
        self._pending_async_hooks.clear()


# Global registry
_registry: Optional[HookRegistry] = None


def get_hook_registry() -> HookRegistry:
    """Get the global hook registry."""
    global _registry
    if _registry is None:
        _registry = HookRegistry()
    return _registry


def set_hook_registry(registry: HookRegistry) -> None:
    """Set the global hook registry."""
    global _registry
    _registry = registry
