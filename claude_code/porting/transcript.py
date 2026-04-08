"""
Claude Code Python - Transcript Store

Provides simple conversation transcript storage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TranscriptStore:
    """Simple transcript store for conversation recording.
    
    Attributes:
        entries: List of transcript entries
        flushed: Whether the transcript has been flushed to disk
    """
    entries: list[str] = field(default_factory=list)
    flushed: bool = False

    def append(self, entry: str) -> None:
        """Append an entry to the transcript.
        
        Args:
            entry: Entry to append
        """
        self.entries.append(entry)
        self.flushed = False

    def compact(self, keep_last: int = 10) -> None:
        """Compact the transcript, keeping only the last N entries.
        
        Args:
            keep_last: Number of entries to keep
        """
        if len(self.entries) > keep_last:
            self.entries[:] = self.entries[-keep_last:]

    def replay(self) -> tuple[str, ...]:
        """Get all entries as a tuple.
        
        Returns:
            Tuple of all entries
        """
        return tuple(self.entries)

    def flush(self) -> None:
        """Mark the transcript as flushed."""
        self.flushed = True

    def clear(self) -> None:
        """Clear all entries."""
        self.entries.clear()
        self.flushed = False

    def get_entry_count(self) -> int:
        """Get the number of entries.
        
        Returns:
            Number of entries
        """
        return len(self.entries)

    def get_latest(self, count: int = 1) -> list[str]:
        """Get the latest N entries.
        
        Args:
            count: Number of entries to get
            
        Returns:
            List of latest entries
        """
        return self.entries[-count:] if self.entries else []

    def as_text(self) -> str:
        """Get all entries as a single text.
        
        Returns:
            All entries joined by newlines
        """
        return "\n".join(self.entries)

    def as_markdown(self) -> str:
        """Convert to markdown format.
        
        Returns:
            Markdown formatted string
        """
        lines = ["# Transcript", ""]
        lines.extend(f"- {entry}" for entry in self.entries)
        return "\n".join(lines)


__all__ = [
    "TranscriptStore",
]