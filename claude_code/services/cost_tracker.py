"""Cost Tracker Service for Claude Code Python.

Tracks API usage and costs for the session.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

DEFAULT_PRICING: dict[str, dict[str, float]] = {
    "claude-opus-4-20250514": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-3-opus-latest": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet-latest": {"input": 3.0, "output": 15.0},
    "claude-3-haiku-latest": {"input": 0.25, "output": 1.25},
    "claude-3-5-sonnet-latest": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-latest": {"input": 1.0, "output": 5.0},
}


@dataclass(frozen=True, slots=True)
class CostEntry:
    """A single cost entry.

    Attributes:
        timestamp: Unix timestamp of the entry.
        input_tokens: Number of input tokens.
        output_tokens: Number of output tokens.
        model: Model used.
        cost_usd: Cost in USD.
    """

    timestamp: float = field(default_factory=time.time)
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""
    cost_usd: float = 0.0


@dataclass(frozen=True, slots=True)
class CostStats:
    """Cost statistics.

    Attributes:
        total_input_tokens: Total input tokens used.
        total_output_tokens: Total output tokens used.
        total_cost_usd: Total cost in USD.
        request_count: Number of requests made.
        start_time: Unix timestamp when tracking started.
        last_request_time: Unix timestamp of last request.
    """

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    request_count: int = 0
    start_time: float = field(default_factory=time.time)
    last_request_time: float | None = None


class CostTracker:
    """Tracks API usage costs.

    Estimates costs based on token usage and model pricing.
    Uses approximate pricing for Claude models.
    """

    PRICING: dict[str, dict[str, float]] = DEFAULT_PRICING

    def __init__(self) -> None:
        """Initialize CostTracker."""
        self._entries: list[CostEntry] = []
        self._stats = CostStats()
        self._start_time = time.time()

    def record(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
        cost_usd: float | None = None,
    ) -> CostEntry:
        """Record API usage.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            model: Model used.
            cost_usd: Override cost (if None, calculates from pricing).

        Returns:
            The created cost entry.
        """
        if cost_usd is None:
            cost_usd = self._calculate_cost(input_tokens, output_tokens, model)

        entry = CostEntry(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=model,
            cost_usd=cost_usd,
        )

        self._entries.append(entry)
        self._update_stats(entry)

        return entry

    def _calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str,
    ) -> float:
        """Calculate cost based on token usage and model.

        Args:
            input_tokens: Number of input tokens.
            output_tokens: Number of output tokens.
            model: Model identifier.

        Returns:
            Cost in USD.
        """
        pricing = self.PRICING.get(model, {"input": 3.0, "output": 15.0})

        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]

        return input_cost + output_cost

    def _update_stats(self, entry: CostEntry) -> None:
        """Update cumulative statistics.

        Args:
            entry: Cost entry to add to stats.
        """
        self._stats.total_input_tokens += entry.input_tokens
        self._stats.total_output_tokens += entry.output_tokens
        self._stats.total_cost_usd += entry.cost_usd
        self._stats.request_count += 1
        self._stats.last_request_time = entry.timestamp

    def get_stats(self) -> CostStats:
        """Get current cost statistics.

        Returns:
            CostStats instance with current totals.
        """
        return self._stats

    def get_entries(self) -> list[CostEntry]:
        """Get all cost entries.

        Returns:
            List of cost entries.
        """
        return self._entries.copy()

    def reset(self) -> None:
        """Reset all tracking."""
        self._entries.clear()
        self._stats = CostStats()
        self._start_time = time.time()

    def format_summary(self) -> str:
        """Format a human-readable cost summary.

        Returns:
            Formatted summary string.
        """
        stats = self._stats

        lines = [
            "Cost Summary",
            "=" * 40,
            f"Requests:      {stats.request_count}",
            f"Input Tokens:  {stats.total_input_tokens:,}",
            f"Output Tokens: {stats.total_output_tokens:,}",
            f"Total Cost:    ${stats.total_cost_usd:.4f}",
            f"Session Time:  {self._format_duration(time.time() - self._start_time)}",
        ]

        return "\n".join(lines)

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form.

        Args:
            seconds: Duration in seconds.

        Returns:
            Formatted duration string.
        """
        if seconds < 60:
            return f"{seconds:.1f}s"
        if seconds < 3600:
            return f"{seconds / 60:.1f}m"
        return f"{seconds / 3600:.1f}h"

    def estimate_remaining_budget(
        self,
        budget_usd: float,
        avg_cost_per_request: float | None = None,
    ) -> float | None:
        """Estimate remaining budget.

        Args:
            budget_usd: Total budget in USD.
            avg_cost_per_request: Average cost per request (calculated from history if None).

        Returns:
            Estimated remaining budget, or None if unlimited.
        """
        if avg_cost_per_request is None:
            if self._stats.request_count > 0:
                avg_cost_per_request = self._stats.total_cost_usd / self._stats.request_count
            else:
                return None

        remaining = budget_usd - self._stats.total_cost_usd

        return remaining


_cost_tracker: CostTracker | None = None


def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance.

    Returns:
        Global CostTracker instance.
    """
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker