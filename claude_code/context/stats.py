"""Stats tracking for Claude Code Python.

Tracks statistics for the session.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class SessionStats:
    """Statistics for the current session.

    Using frozen=True for immutability.

    Attributes:
        start_time: When the session started.
        total_queries: Number of queries made.
        total_tokens: Total tokens used.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        cache_read_tokens: Tokens read from cache.
        cache_creation_tokens: Tokens used for cache creation.
        total_cost: Total cost in USD.
        tool_calls: Number of tool calls made.
        tool_errors: Number of tool call errors.
        messages_sent: Number of user messages.
        messages_received: Number of assistant messages.
        compaction_count: Number of compactions performed.
        errors: Number of errors encountered.
    """

    start_time: datetime = field(default_factory=datetime.now)
    total_queries: int = 0
    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    total_cost: float = 0.0
    tool_calls: int = 0
    tool_errors: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    compaction_count: int = 0
    errors: int = 0

    @property
    def duration(self) -> float:
        """Get session duration in seconds.

        Returns:
            Duration in seconds.
        """
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def average_tokens_per_query(self) -> float:
        """Get average tokens per query.

        Returns:
            Average tokens per query, or 0 if no queries.
        """
        if self.total_queries == 0:
            return 0.0
        return self.total_tokens / self.total_queries

    @property
    def cost_per_hour(self) -> float:
        """Get estimated cost per hour.

        Returns:
            Cost per hour in USD, or 0 if no time elapsed.
        """
        hours = self.duration / 3600
        if hours == 0:
            return 0.0
        return self.total_cost / hours

    def to_dict(self) -> dict[str, Any]:
        """Convert stats to dictionary.

        Returns:
            Dictionary representation of stats.
        """
        return {
            "start_time": self.start_time.isoformat(),
            "duration_seconds": self.duration,
            "total_queries": self.total_queries,
            "total_tokens": self.total_tokens,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_read_tokens": self.cache_read_tokens,
            "cache_creation_tokens": self.cache_creation_tokens,
            "total_cost": self.total_cost,
            "tool_calls": self.tool_calls,
            "tool_errors": self.tool_errors,
            "messages_sent": self.messages_sent,
            "messages_received": self.messages_received,
            "compaction_count": self.compaction_count,
            "errors": self.errors,
        }


class StatsTracker:
    """Tracks statistics for the session.

    Collects metrics on queries, tokens, tool usage, etc.
    """

    def __init__(self) -> None:
        """Initialize StatsTracker."""
        self._stats = SessionStats()
        self._tool_usage: dict[str, int] = defaultdict(int)
        self._model_usage: dict[str, int] = defaultdict(int)

    @property
    def stats(self) -> SessionStats:
        """Get current stats."""
        return self._stats

    def record_query(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """Record a query.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
        """
        self._stats.total_queries += 1
        self._stats.input_tokens += input_tokens
        self._stats.output_tokens += output_tokens
        self._stats.total_tokens += input_tokens + output_tokens

    def record_cache_tokens(self, read: int = 0, creation: int = 0) -> None:
        """Record cache token usage.

        Args:
            read: Number of cache read tokens.
            creation: Number of cache creation tokens.
        """
        self._stats.cache_read_tokens += read
        self._stats.cache_creation_tokens += creation

    def record_cost(self, cost: float) -> None:
        """Record cost.

        Args:
            cost: Cost to record in USD.
        """
        self._stats.total_cost += cost

    def record_tool_call(self, tool_name: str, success: bool = True) -> None:
        """Record a tool call.

        Args:
            tool_name: Name of the tool.
            success: Whether the call succeeded.
        """
        self._stats.tool_calls += 1
        self._tool_usage[tool_name] += 1

        if not success:
            self._stats.tool_errors += 1

    def record_message(self, role: str) -> None:
        """Record a message.

        Args:
            role: Role of the message (user/assistant).
        """
        if role == "user":
            self._stats.messages_sent += 1
        else:
            self._stats.messages_received += 1

    def record_compaction(self) -> None:
        """Record a compaction."""
        self._stats.compaction_count += 1

    def record_error(self) -> None:
        """Record an error."""
        self._stats.errors += 1

    def record_model_usage(self, model: str, tokens: int) -> None:
        """Record model usage.

        Args:
            model: Model identifier.
            tokens: Number of tokens used.
        """
        self._model_usage[model] += tokens

    def get_tool_usage(self) -> dict[str, int]:
        """Get tool usage counts.

        Returns:
            Dictionary of tool name to call count.
        """
        return dict(self._tool_usage)

    def get_model_usage(self) -> dict[str, int]:
        """Get model usage counts.

        Returns:
            Dictionary of model to token count.
        """
        return dict(self._model_usage)

    def get_summary(self) -> dict[str, Any]:
        """Get a summary of stats.

        Returns:
            Dictionary with session, tool usage, and model usage.
        """
        return {
            "session": self._stats.to_dict(),
            "tool_usage": self.get_tool_usage(),
            "model_usage": self.get_model_usage(),
        }


_stats_tracker: StatsTracker | None = None


def get_stats_tracker() -> StatsTracker:
    """Get the global stats tracker.

    Returns:
        Global StatsTracker instance.
    """
    global _stats_tracker
    if _stats_tracker is None:
        _stats_tracker = StatsTracker()
    return _stats_tracker


def record_tool_call(tool_name: str, success: bool = True) -> None:
    """Record a tool call.

    Args:
        tool_name: Name of the tool.
        success: Whether the call succeeded.
    """
    get_stats_tracker().record_tool_call(tool_name, success)


def record_cost(cost: float) -> None:
    """Record cost.

    Args:
        cost: Cost to record in USD.
    """
    get_stats_tracker().record_cost(cost)