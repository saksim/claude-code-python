"""
Claude Code Python - Hooks System

Provides hooks for extending Claude Code functionality with custom scripts.

Hooks allow you to:
- Run scripts before/after tool execution
- React to file changes
- Modify messages
- Perform cleanup tasks
"""

from claude_code.hooks.events import (
    HookEventEmitter,
    HookOutcome,
    HookStartedEvent,
    HookProgressEvent,
    HookResponseEvent,
    get_hook_emitter,
    emit_hook_started,
    emit_hook_progress,
    emit_hook_response,
)

from claude_code.hooks.registry import (
    HookRegistry,
    HookConfig,
    HookResult,
    HookEvent,
    PendingAsyncHook,
    get_hook_registry,
    set_hook_registry,
)

from claude_code.hooks.config import (
    HooksConfig,
    HooksConfigManager,
    load_hooks_from_file,
    create_hook_from_config,
)

__all__ = [
    # Events
    "HookEventEmitter",
    "HookOutcome",
    "HookStartedEvent",
    "HookProgressEvent",
    "HookResponseEvent",
    "get_hook_emitter",
    "emit_hook_started",
    "emit_hook_progress",
    "emit_hook_response",
    
    # Registry
    "HookRegistry",
    "HookConfig",
    "HookResult",
    "HookEvent",
    "PendingAsyncHook",
    "get_hook_registry",
    "set_hook_registry",
    
    # Config
    "HooksConfig",
    "HooksConfigManager",
    "load_hooks_from_file",
    "create_hook_from_config",
]


# Example hook events that can be triggered:
# 
# SessionStart - When a new session starts
# SessionEnd - When a session ends
# Setup - During initial setup
# Teardown - During cleanup
#
# PreToolCall - Before a tool is called
# PostToolCall - After a tool completes
#
# PreMessage - Before sending a message
# PostMessage - After receiving a message
#
# PreQuery - Before sending a query
# PostQuery - After receiving a query response
#
# OnError - When an error occurs
# FileChanged - When a file is modified
