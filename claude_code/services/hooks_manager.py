"""
Claude Code Python - Hooks System
Manages pre/post execution hooks for tools and commands.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- pathlib.Path for file operations
- Proper error handling
"""

from __future__ import annotations

import asyncio
import json
import shlex
import subprocess
import time
from pathlib import Path
from typing import Callable, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


# Default constants
DEFAULT_HOOKS_CONFIG_PATH: Path = Path.home() / ".claude" / "hooks.json"
DEFAULT_HOOK_TIMEOUT_SECONDS: int = 30


class HookEvent(Enum):
    """Events that can trigger hooks.
    
    Attributes:
        BEFORE_TOOL: Fired before a tool is executed
        AFTER_TOOL: Fired after a tool completes
        BEFORE_COMMAND: Fired before a command is executed
        AFTER_COMMAND: Fired after a command completes
        ON_ERROR: Fired when an error occurs
        ON_EXIT: Fired when the session exits
    """
    BEFORE_TOOL = "before_tool"
    AFTER_TOOL = "after_tool"
    BEFORE_COMMAND = "before_command"
    AFTER_COMMAND = "after_command"
    ON_ERROR = "on_error"
    ON_EXIT = "on_exit"


@dataclass(frozen=True, slots=True)
class Hook:
    """A hook definition.
    
    Using frozen=True, slots=True for immutability and memory efficiency.
    
    Attributes:
        name: Unique name identifying the hook
        event: The event type that triggers this hook
        command: The command to execute when triggered
        working_directory: Optional working directory for the hook
        enabled: Whether the hook is currently enabled
        timeout_seconds: Maximum execution time for the hook
    """
    name: str
    event: HookEvent
    command: str
    working_directory: Optional[str] = None
    enabled: bool = True
    timeout_seconds: int = DEFAULT_HOOK_TIMEOUT_SECONDS


@dataclass(frozen=True, slots=True)
class HookResult:
    """Result of a hook execution.
    
    Attributes:
        hook_name: Name of the hook that was executed
        success: Whether the hook completed successfully
        output: Standard output from the hook
        error: Error message if the hook failed
        duration_ms: Execution time in milliseconds
    """
    hook_name: str
    success: bool
    output: str = ""
    error: Optional[str] = None
    duration_ms: float = 0.0


class HooksManager:
    """Manages execution hooks.
    
    Hooks can run before/after tool execution, commands, and other events.
    Hooks are loaded from and saved to a JSON configuration file.
    
    Attributes:
        config_path: Path to the hooks configuration file
    
    Example:
        >>> manager = HooksManager()
        >>> manager.add_hook("log-tools", HookEvent.AFTER_TOOL, "echo 'Tool: ${tool_name}'")
        >>> results = await manager.trigger(HookEvent.AFTER_TOOL, {"tool_name": "read"})
    """
    
    def __init__(self, config_path: Optional[str | Path] = None):
        self._hooks: list[Hook] = []
        self._config_path = Path(config_path) if config_path else DEFAULT_HOOKS_CONFIG_PATH
        self._load_hooks()
    
    def _get_default_config_path(self) -> Path:
        """Get default hooks config path.
        
        Returns:
            Path to the default hooks configuration file.
        """
        return DEFAULT_HOOKS_CONFIG_PATH
    
    def _load_hooks(self) -> None:
        """Load hooks from configuration file."""
        if not self._config_path.exists():
            return
        
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            for hook_data in data.get("hooks", []):
                try:
                    hook = Hook(
                        name=hook_data["name"],
                        event=HookEvent(hook_data["event"]),
                        command=hook_data["command"],
                        working_directory=hook_data.get("working_directory"),
                        enabled=hook_data.get("enabled", True),
                        timeout_seconds=hook_data.get("timeout_seconds", DEFAULT_HOOK_TIMEOUT_SECONDS),
                    )
                    self._hooks.append(hook)
                except (KeyError, ValueError):
                    pass
                    
        except Exception:
            pass
    
    def save_hooks(self) -> bool:
        """Save hooks to the configuration file.
        
        Returns:
            True if saved successfully, False otherwise.
        """
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)
            
            data: dict[str, Any] = {
                "hooks": [
                    {
                        "name": h.name,
                        "event": h.event.value,
                        "command": h.command,
                        "working_directory": h.working_directory,
                        "enabled": h.enabled,
                        "timeout_seconds": h.timeout_seconds,
                    }
                    for h in self._hooks
                ]
            }
            
            with open(self._config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception:
            return False
    
    def add_hook(
        self,
        name: str,
        event: HookEvent,
        command: str,
        **kwargs: Any,
    ) -> Hook:
        """Add a new hook.
        
        Args:
            name: Unique hook name
            event: When to trigger the hook
            command: Command to execute
            **kwargs: Additional hook options (working_directory, enabled, timeout_seconds)
            
        Returns:
            The created Hook instance.
        """
        hook = Hook(
            name=name,
            event=event,
            command=command,
            **kwargs
        )
        
        self._hooks.append(hook)
        self.save_hooks()
        
        return hook
    
    def remove_hook(self, name: str) -> bool:
        """Remove a hook by name.
        
        Args:
            name: Name of the hook to remove
            
        Returns:
            True if removed, False if not found.
        """
        for i, hook in enumerate(self._hooks):
            if hook.name == name:
                self._hooks.pop(i)
                self.save_hooks()
                return True
        return False
    
    def get_hooks(self, event: Optional[HookEvent] = None) -> list[Hook]:
        """Get hooks, optionally filtered by event.
        
        Args:
            event: Optional event type to filter by
            
        Returns:
            List of enabled Hook objects.
        """
        if event:
            return [h for h in self._hooks if h.event == event and h.enabled]
        return [h for h in self._hooks if h.enabled]
    
    async def trigger(
        self,
        event: HookEvent,
        context: dict[str, Any],
    ) -> list[HookResult]:
        """Trigger all hooks for an event.
        
        Args:
            event: The event type that occurred
            context: Context data (tool_name, input, output, etc.)
            
        Returns:
            List of HookResult objects, one per triggered hook.
        """
        results: list[HookResult] = []
        hooks = self.get_hooks(event)
        
        for hook in hooks:
            start_time = time.time()
            
            try:
                command = self._format_command(hook.command, context)
                
                process = await asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=hook.working_directory,
                )
                
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=hook.timeout_seconds
                )
                
                output = stdout.decode() if stdout else ""
                error = stderr.decode() if stderr else None
                
                result = HookResult(
                    hook_name=hook.name,
                    success=process.returncode == 0,
                    output=output,
                    error=error,
                    duration_ms=(time.time() - start_time) * 1000,
                )
                
            except asyncio.TimeoutError:
                result = HookResult(
                    hook_name=hook.name,
                    success=False,
                    error=f"Timeout after {hook.timeout_seconds}s",
                    duration_ms=(time.time() - start_time) * 1000,
                )
            except Exception as e:
                result = HookResult(
                    hook_name=hook.name,
                    success=False,
                    error=str(e),
                    duration_ms=(time.time() - start_time) * 1000,
                )
            
            results.append(result)
        
        return results
    
    def _format_command(self, command: str, context: dict[str, Any]) -> str:
        """Format command with context variables.
        
        Replaces ${key} placeholders with context values.
        
        Args:
            command: Command template string
            context: Context dictionary with variable values
            
        Returns:
            Formatted command string.
        """
        for key, value in context.items():
            placeholder = f"${{{key}}}"
            if placeholder in command:
                str_value = str(value) if not isinstance(value, str) else value
                command = command.replace(placeholder, shlex.quote(str_value))
        
        return command


# Global hooks manager
_hooks_manager: Optional[HooksManager] = None


def get_hooks_manager() -> HooksManager:
    """Get the global hooks manager instance.
    
    Returns:
        The global HooksManager singleton.
    """
    global _hooks_manager
    if _hooks_manager is None:
        _hooks_manager = HooksManager()
    return _hooks_manager
