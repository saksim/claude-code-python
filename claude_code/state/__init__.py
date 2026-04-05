"""
Claude Code Python - State Management

Central state management for the application.
"""

from claude_code.state.app_state import (
    AppState,
    PermissionMode,
    EffortLevel,
    PermissionContext,
    ToolPermissionContext,
    get_default_app_state,
    StateObserver,
    StateChange,
)

from claude_code.state.store import (
    Store,
    SelectorStore,
    StateChange,
    create_store,
    get_store,
    set_store,
)

from claude_code.state.session_state import (
    SessionMetadata,
    Session,
    SessionStore,
    SessionManager,
    get_session_manager,
    set_session_manager,
)

__all__ = [
    # App State
    "AppState",
    "PermissionMode",
    "EffortLevel",
    "PermissionContext",
    "ToolPermissionContext",
    "get_default_app_state",
    "StateObserver",
    
    # Store
    "Store",
    "SelectorStore",
    "create_store",
    "get_store",
    "set_store",
    
    # Session
    "SessionMetadata",
    "Session",
    "SessionStore",
    "SessionManager",
    "get_session_manager",
    "set_session_manager",
]
