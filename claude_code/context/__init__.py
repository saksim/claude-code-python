"""
Claude Code Python - Context Module

Provides context building, notifications, and stats tracking.
"""

from claude_code.context.builder import (
    GitContext,
    WorkspaceContext,
    MemoryContext,
    SystemContext,
    ContextBuilder,
)

from claude_code.context.notifications import (
    NotificationType,
    Notification,
    NotificationManager,
    get_notification_manager,
    show_notification,
)

from claude_code.context.stats import (
    SessionStats,
    StatsTracker,
    get_stats_tracker,
    record_tool_call,
    record_cost,
)

__all__ = [
    # Context Builder
    "GitContext",
    "WorkspaceContext",
    "MemoryContext",
    "SystemContext",
    "ContextBuilder",
    
    # Notifications
    "NotificationType",
    "Notification",
    "NotificationManager",
    "get_notification_manager",
    "show_notification",
    
    # Stats
    "SessionStats",
    "StatsTracker",
    "get_stats_tracker",
    "record_tool_call",
    "record_cost",
]
