"""
Claude Code Python - Bootstrap System

Provides bootstrap graph and startup flow management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import sys
import platform


@dataclass(frozen=True, slots=True)
class BootstrapGraph:
    """Bootstrap graph showing the startup flow.
    
    Attributes:
        stages: Tuple of bootstrap stages
    """
    stages: tuple[str, ...] = field(default_factory=lambda: (
        "top-level prefetch side effects",
        "warning handler and environment guards",
        "CLI parser and pre-action trust gate",
        "setup() + commands/agents parallel load",
        "deferred init after trust",
        "mode routing: local / remote / ssh / teleport / direct-connect / deep-link",
        "query engine submit loop",
    ))

    def as_markdown(self) -> str:
        """Convert to markdown format."""
        lines = ["# Bootstrap Graph", ""]
        lines.extend(f"- {stage}" for stage in self.stages)
        return "\n".join(lines)

    def get_stage_count(self) -> int:
        """Get the number of bootstrap stages."""
        return len(self.stages)

    def get_stage(self, index: int) -> str | None:
        """Get a specific stage by index.
        
        Args:
            index: Stage index (0-based)
            
        Returns:
            Stage name or None if index out of range
        """
        if 0 <= index < len(self.stages):
            return self.stages[index]
        return None


def get_bootstrap_graph() -> BootstrapGraph:
    """Get the default bootstrap graph.
    
    Returns:
        BootstrapGraph instance
    """
    return BootstrapGraph()


__all__ = [
    "BootstrapGraph",
    "get_bootstrap_graph",
]