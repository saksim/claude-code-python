"""
AppState for Claude Code Python.

Central state management for the application.
Enhanced with selectors and derived state.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Optional, Callable, Dict, List
from enum import Enum
from copy import deepcopy
from datetime import datetime

# PermissionMode imported from canonical source
from claude_code.permissions import PermissionMode


class EffortLevel(Enum):
    """Effort level for task execution."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ConnectionStatus(Enum):
    """Remote connection status."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class PermissionContext:
    """Permission context for tool execution."""
    mode: PermissionMode = PermissionMode.DEFAULT
    rules: dict = field(default_factory=dict)
    is_bypass_available: bool = True


@dataclass(frozen=True, slots=True)
class ToolPermissionContext:
    """Tool permission context."""
    mode: PermissionMode = PermissionMode.DEFAULT
    rules: list = field(default_factory=list)
    is_bypass_mode_available: bool = True


@dataclass(frozen=True, slots=True)
class RemoteSessionState:
    """Remote session state."""
    url: Optional[str] = None
    status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    background_task_count: int = 0
    session_name: Optional[str] = None


@dataclass(frozen=True, slots=True)
class SessionMetadata:
    """Session metadata."""
    project_root: str = ""
    cwd: str = ""
    start_time: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    model: str = "claude-sonnet-4-20250514"
    effort: str = "medium"


@dataclass
class AppState:
    """
    Central application state.
    
    Contains all the mutable state for the Claude Code session.
    Enhanced with selectors and derived state support.
    """
    main_loop_model: str = "claude-sonnet-4-20250514"
    verbose: bool = False
    color: bool = True
    
    tool_permission_context: ToolPermissionContext = field(
        default_factory=ToolPermissionContext
    )
    
    session_id: str = ""
    conversation_id: str = ""
    
    expanded_view: str = "default"
    
    effort_value: str = "medium"
    
    tasks: dict = field(default_factory=dict)
    
    mcp_tools: list = field(default_factory=list)
    mcp_resources: list = field(default_factory=list)
    
    pre_tool_hooks: list = field(default_factory=list)
    post_tool_hooks: list = field(default_factory=list)
    
    read_files: dict = field(default_factory=dict)
    
    options: dict = field(default_factory=dict)
    
    metadata: dict = field(default_factory=dict)
    
    remote_session: RemoteSessionState = field(default_factory=RemoteSessionState)
    session_info: SessionMetadata = field(default_factory=SessionMetadata)


def get_default_app_state() -> AppState:
    """Get default application state."""
    return AppState()


@dataclass
class StateChange:
    """Represents a state change."""
    field: str
    old_value: Any
    new_value: Any
    timestamp: datetime = field(default_factory=datetime.now)


class StateObserver:
    """Observer for state changes."""
    
    def __init__(self, callback: Callable[[StateChange], None]):
        self.callback = callback
    
    def on_change(self, change: StateChange) -> None:
        self.callback(change)


class SelectorStore:
    """
    Enhanced store with selector support for AppState.
    Provides memoization and derived state computation.
    """
    
    def __init__(self, initial_state: Optional[AppState] = None):
        self._state = initial_state or get_default_app_state()
        self._observers: List[Callable[[StateChange], None]] = []
        self._version: int = 0
        self._selector_cache: Dict[str, tuple[Any, int]] = {}
        self._derived_states: Dict[str, Callable[[AppState], Any]] = {}
    
    @property
    def state(self) -> AppState:
        return self._state
    
    @property
    def version(self) -> int:
        return self._version
    
    def get_state(self) -> AppState:
        """Get current state."""
        return deepcopy(self._state)
    
    def set_state(self, updates: Dict[str, Any]) -> None:
        """Update state with notifications."""
        for key, new_value in updates.items():
            old_value = getattr(self._state, key, None)
            
            if old_value != new_value:
                setattr(self._state, key, new_value)
                self._version += 1
                
                change = StateChange(
                    field=key,
                    old_value=deepcopy(old_value),
                    new_value=deepcopy(new_value),
                )
                
                for observer in self._observers:
                    try:
                        observer(change)
                    except Exception:
                        pass
        
        self._selector_cache.clear()
    
    def subscribe(self, observer: Callable[[StateChange], None]) -> Callable[[], None]:
        """Subscribe to state changes."""
        self._observers.append(observer)
        
        def unsubscribe():
            if observer in self._observers:
                self._observers.remove(observer)
        
        return unsubscribe
    
    def select(self, selector: Callable[[AppState], Any], key: Optional[str] = None) -> Any:
        """Select a slice of state with memoization."""
        cache_key = key or str(hash(selector))
        
        if cache_key in self._selector_cache:
            cached_value, cached_version = self._selector_cache[cache_key]
            if cached_version == self._version:
                return cached_value
        
        value = selector(self._state)
        self._selector_cache[cache_key] = (value, self._version)
        
        return value
    
    def register_derived(self, name: str, compute: Callable[[AppState], Any]) -> None:
        """Register a derived state computation."""
        self._derived_states[name] = compute
    
    def get_derived(self, name: str) -> Any:
        """Get derived state value."""
        compute = self._derived_states.get(name)
        if compute:
            return self.select(compute, key=f"derived:{name}")
        return None
    
    def invalidate_cache(self) -> None:
        """Invalidate all selector caches."""
        self._selector_cache.clear()


_global_store: Optional[SelectorStore] = None


def get_selector_store() -> SelectorStore:
    """Get the global selector store."""
    global _global_store
    if _global_store is None:
        _global_store = SelectorStore()
    return _global_store


def set_selector_store(store: SelectorStore) -> None:
    """Set the global selector store."""
    global _global_store
    _global_store = store


def create_selector_store(initial_state: Optional[AppState] = None) -> SelectorStore:
    """Create a new selector store."""
    return SelectorStore(initial_state)


__all__ = [
    "PermissionMode",
    "EffortLevel",
    "ConnectionStatus",
    "PermissionContext",
    "ToolPermissionContext",
    "RemoteSessionState",
    "SessionMetadata",
    "AppState",
    "get_default_app_state",
    "StateChange",
    "StateObserver",
    "SelectorStore",
    "get_selector_store",
    "set_selector_store",
    "create_selector_store",
]
