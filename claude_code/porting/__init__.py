"""
Claude Code Python - Porting Module

Provides tools and commands snapshots from the TypeScript parity workspace.
Includes parity auditing, session persistence, and coverage tracking.
"""

from claude_code.porting.snapshots import (
    PortingModule,
    PortingBacklog,
    PORTED_TOOLS,
    PORTED_COMMANDS,
    build_tool_backlog,
    build_command_backlog,
    get_tool_snapshot,
    get_command_snapshot,
    find_tools,
    find_commands,
    get_all_tool_names,
    get_all_command_names,
)

from claude_code.porting.audit import (
    ParityAuditResult,
    run_parity_audit,
)

from claude_code.porting.session_store import (
    StoredSession,
    DEFAULT_SESSION_DIR,
    save_session,
    load_session,
    list_sessions,
    delete_session,
    get_session_path,
)

from claude_code.porting.execution import (
    MirroredCommand,
    MirroredTool,
    ExecutionRegistry,
    build_execution_registry,
    get_execution_registry,
)

from claude_code.porting.transcript import (
    TranscriptStore,
)

__all__ = [
    # Snapshots
    "PortingModule",
    "PortingBacklog",
    "PORTED_TOOLS",
    "PORTED_COMMANDS",
    "build_tool_backlog",
    "build_command_backlog",
    "get_tool_snapshot",
    "get_command_snapshot",
    "find_tools",
    "find_commands",
    "get_all_tool_names",
    "get_all_command_names",
    # Audit
    "ParityAuditResult",
    "run_parity_audit",
    # Session Store
    "StoredSession",
    "DEFAULT_SESSION_DIR",
    "save_session",
    "load_session",
    "list_sessions",
    "delete_session",
    "get_session_path",
    # Execution
    "MirroredCommand",
    "MirroredTool",
    "ExecutionRegistry",
    "build_execution_registry",
    "get_execution_registry",
    # Transcript
    "TranscriptStore",
]