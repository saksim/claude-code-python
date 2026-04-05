"""
Analytics service for Claude Code Python.

Provides telemetry and analytics tracking for usage patterns.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- Proper error handling
"""

from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional
from enum import Enum


# Default constants
_DEFAULT_USER_ID: str = "anonymous"


class EventType(Enum):
    """Analytics event types.
    
    Attributes:
        SESSION_START: Session lifecycle start event
        SESSION_END: Session lifecycle end event
        QUERY_START: Query execution start event
        QUERY_END: Query execution end event
        QUERY_ERROR: Query execution error event
        TOOL_USE: Tool usage event
        TOOL_ERROR: Tool execution error event
        TOKEN_USAGE: Token consumption tracking event
        FEATURE_USED: Feature usage event
        ERROR: Generic error event
    """
    SESSION_START = "session_start"
    SESSION_END = "session_end"
    QUERY_START = "query_start"
    QUERY_END = "query_end"
    QUERY_ERROR = "query_error"
    TOOL_USE = "tool_use"
    TOOL_ERROR = "tool_error"
    TOKEN_USAGE = "token_usage"
    FEATURE_USED = "feature_used"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class AnalyticsEvent:
    """An analytics event.
    
    Using frozen=True, slots=True for immutability and memory efficiency.
    
    Attributes:
        event_type: Type of the event
        timestamp: Unix timestamp when the event occurred
        session_id: Unique session identifier
        request_id: Unique request identifier
        properties: Additional event properties
        user_id: User identifier for analytics
    """
    event_type: str
    timestamp: float = field(default_factory=time.time)
    session_id: str = ""
    request_id: str = ""
    properties: dict[str, Any] = field(default_factory=dict)
    user_id: str = ""


@dataclass(frozen=True, slots=True)
class SessionStats:
    """Session statistics.
    
    Using frozen=True, slots=True for immutability and memory efficiency.
    
    Attributes:
        session_id: Unique session identifier
        start_time: Unix timestamp when session started
        end_time: Unix timestamp when session ended (None if active)
        total_queries: Number of queries in the session
        total_tokens: Total tokens consumed
        total_cost: Total cost in USD
        tool_calls: Number of tool calls made
        errors: Number of errors encountered
    """
    session_id: str = ""
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_queries: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    tool_calls: int = 0
    errors: int = 0


class AnalyticsService:
    """Analytics service for tracking usage and errors.
    
    This is a simplified version that logs events locally.
    In production, this would send to a telemetry endpoint.
    
    Attributes:
        enabled: Whether analytics tracking is enabled
        session_stats: Current session statistics if active
    
    Example:
        >>> analytics = AnalyticsService(enabled=True)
        >>> session_id = analytics.start_session()
        >>> analytics.track_tool_use("Read", success=True, duration_ms=150)
        >>> stats = analytics.end_session()
    """
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self._events: list[AnalyticsEvent] = []
        self._session_stats: Optional[SessionStats] = None
        self._current_request_id: Optional[str] = None
    
    def start_session(self, session_id: Optional[str] = None) -> str:
        """Start a new analytics session.
        
        Args:
            session_id: Optional existing session ID, or None to generate new
            
        Returns:
            The session ID (either provided or generated).
        """
        if not self.enabled:
            return ""
        
        session_id = session_id or uuid.uuid4().hex
        
        self._session_stats = SessionStats(session_id=session_id)
        
        self.track(
            EventType.SESSION_START.value,
            properties={"session_id": session_id}
        )
        
        return session_id
    
    def end_session(self) -> Optional[SessionStats]:
        """End the current session and return stats.
        
        Returns:
            SessionStats if session was active, None otherwise.
        """
        if not self.enabled or self._session_stats is None:
            return None
        
        self._session_stats = SessionStats(
            session_id=self._session_stats.session_id,
            start_time=self._session_stats.start_time,
            end_time=time.time(),
            total_queries=self._session_stats.total_queries,
            total_tokens=self._session_stats.total_tokens,
            total_cost=self._session_stats.total_cost,
            tool_calls=self._session_stats.tool_calls,
            errors=self._session_stats.errors,
        )
        
        self.track(
            EventType.SESSION_END.value,
            properties={
                "session_id": self._session_stats.session_id,
                "total_queries": self._session_stats.total_queries,
                "total_tokens": self._session_stats.total_tokens,
                "total_cost": self._session_stats.total_cost,
                "tool_calls": self._session_stats.tool_calls,
                "errors": self._session_stats.errors,
            }
        )
        
        stats = self._session_stats
        self._session_stats = None
        return stats
    
    def track(
        self,
        event_type: str,
        properties: Optional[dict[str, Any]] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Track an analytics event.
        
        Args:
            event_type: Type of event to track
            properties: Optional event properties
            request_id: Optional request identifier
        """
        if not self.enabled:
            return
        
        event = AnalyticsEvent(
            event_type=event_type,
            session_id=self._session_stats.session_id if self._session_stats else "",
            request_id=request_id or self._current_request_id or "",
            properties=properties or {},
            user_id=self._get_user_id(),
        )
        
        self._events.append(event)
        self._log_event(event)
    
    def track_query_start(self, request_id: str) -> None:
        """Track the start of a query.
        
        Args:
            request_id: Unique request identifier
        """
        self._current_request_id = request_id
        self.track(
            EventType.QUERY_START.value,
            request_id=request_id
        )
        if self._session_stats:
            self._session_stats = SessionStats(
                session_id=self._session_stats.session_id,
                start_time=self._session_stats.start_time,
                end_time=self._session_stats.end_time,
                total_queries=self._session_stats.total_queries + 1,
                total_tokens=self._session_stats.total_tokens,
                total_cost=self._session_stats.total_cost,
                tool_calls=self._session_stats.tool_calls,
                errors=self._session_stats.errors,
            )
    
    def track_query_end(
        self,
        request_id: str,
        tokens: int = 0,
        cost: float = 0.0,
        duration_ms: float = 0,
    ) -> None:
        """Track the end of a query.
        
        Args:
            request_id: Unique request identifier
            tokens: Number of tokens used
            cost: Cost in USD
            duration_ms: Query duration in milliseconds
        """
        self.track(
            EventType.QUERY_END.value,
            request_id=request_id,
            properties={
                "tokens": tokens,
                "cost": cost,
                "duration_ms": duration_ms,
            }
        )
        self._current_request_id = None
        
        if self._session_stats:
            self._session_stats = SessionStats(
                session_id=self._session_stats.session_id,
                start_time=self._session_stats.start_time,
                end_time=self._session_stats.end_time,
                total_queries=self._session_stats.total_queries,
                total_tokens=self._session_stats.total_tokens + tokens,
                total_cost=self._session_stats.total_cost + cost,
                tool_calls=self._session_stats.tool_calls,
                errors=self._session_stats.errors,
            )
    
    def track_tool_use(
        self,
        tool_name: str,
        success: bool = True,
        duration_ms: float = 0,
    ) -> None:
        """Track a tool usage event.
        
        Args:
            tool_name: Name of the tool that was used
            success: Whether the tool executed successfully
            duration_ms: Execution time in milliseconds
        """
        self.track(
            EventType.TOOL_USE.value,
            properties={
                "tool_name": tool_name,
                "success": success,
                "duration_ms": duration_ms,
            }
        )
        
        if self._session_stats and success:
            self._session_stats = SessionStats(
                session_id=self._session_stats.session_id,
                start_time=self._session_stats.start_time,
                end_time=self._session_stats.end_time,
                total_queries=self._session_stats.total_queries,
                total_tokens=self._session_stats.total_tokens,
                total_cost=self._session_stats.total_cost,
                tool_calls=self._session_stats.tool_calls + 1,
                errors=self._session_stats.errors,
            )
    
    def track_error(
        self,
        error_type: str,
        message: str,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Track an error event.
        
        Args:
            error_type: Type/category of the error
            message: Error message
            context: Optional error context
        """
        self.track(
            EventType.ERROR.value,
            properties={
                "error_type": error_type,
                "message": message,
                "context": context or {},
            }
        )
        
        if self._session_stats:
            self._session_stats = SessionStats(
                session_id=self._session_stats.session_id,
                start_time=self._session_stats.start_time,
                end_time=self._session_stats.end_time,
                total_queries=self._session_stats.total_queries,
                total_tokens=self._session_stats.total_tokens,
                total_cost=self._session_stats.total_cost,
                tool_calls=self._session_stats.tool_calls,
                errors=self._session_stats.errors + 1,
            )
    
    def track_token_usage(
        self,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
    ) -> None:
        """Track token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cache_read_tokens: Tokens from cache reads
            cache_creation_tokens: Tokens from cache creation
        """
        self.track(
            EventType.TOKEN_USAGE.value,
            properties={
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_read_tokens": cache_read_tokens,
                "cache_creation_tokens": cache_creation_tokens,
                "total_tokens": input_tokens + output_tokens,
            }
        )
    
    def track_feature(self, feature_name: str, value: Any = True) -> None:
        """Track feature usage.
        
        Args:
            feature_name: Name of the feature used
            value: Optional value associated with the feature
        """
        self.track(
            EventType.FEATURE_USED.value,
            properties={
                "feature_name": feature_name,
                "value": value,
            }
        )
    
    def get_session_stats(self) -> Optional[SessionStats]:
        """Get current session statistics.
        
        Returns:
            SessionStats if a session is active, None otherwise.
        """
        return self._session_stats
    
    def get_events(self) -> list[AnalyticsEvent]:
        """Get all tracked events.
        
        Returns:
            Copy of the events list.
        """
        return self._events.copy()
    
    def _get_user_id(self) -> str:
        """Get the user ID from environment or generate one.
        
        Returns:
            User ID string.
        """
        return os.getenv("CLAUDE_USER_ID", _DEFAULT_USER_ID)
    
    def _log_event(self, event: AnalyticsEvent) -> None:
        """Log an event (debug logging in development).
        
        In production, this would send to a telemetry endpoint.
        For now, just store in memory.
        
        Args:
            event: The analytics event to log
        """
        pass
    
    def flush(self) -> None:
        """Flush events to the telemetry endpoint."""
        if not self.enabled or not self._events:
            return
        
        # In production, this would batch-send events
        # For now, just clear the events
        self._events.clear()
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable analytics.
        
        Args:
            enabled: Whether to enable analytics
        """
        self.enabled = enabled


# Global analytics instance
_analytics: Optional[AnalyticsService] = None


def get_analytics() -> AnalyticsService:
    """Get the global analytics instance.
    
    Returns:
        The global AnalyticsService singleton.
    """
    global _analytics
    if _analytics is None:
        _analytics = AnalyticsService()
    return _analytics


def set_analytics(service: AnalyticsService) -> None:
    """Set the global analytics instance.
    
    Args:
        service: AnalyticsService instance to use globally.
    """
    global _analytics
    _analytics = service


def track_event(event_type: str, properties: Optional[dict[str, Any]] = None) -> None:
    """Track an analytics event.
    
    Args:
        event_type: Type of event to track
        properties: Optional event properties
    """
    get_analytics().track(event_type, properties)


def log_event(event_type: str, **kwargs: Any) -> None:
    """Log an event with keyword arguments.
    
    Args:
        event_type: Type of event to track
        **kwargs: Event properties as keyword arguments
    """
    get_analytics().track(event_type, properties=kwargs)
