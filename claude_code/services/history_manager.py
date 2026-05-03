"""
Claude Code Python - History Manager
Manages conversation history and session persistence.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- pathlib.Path for file operations
- Proper error handling
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4


# Default constants
DEFAULT_MAX_ENTRIES: int = 1000
AUTO_SAVE_INTERVAL_SECONDS: int = 30


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    """A single conversation entry.
    
    Using frozen=True, slots=True for immutability and memory efficiency.
    
    Attributes:
        id: Unique identifier for this entry
        role: Message role (user/assistant/system)
        content: Message content (string or list of content blocks)
        timestamp: Unix timestamp when the entry was created
        tokens_used: Number of tokens consumed by this message
        cost_usd: Cost in USD for this message
        metadata: Additional metadata about the entry
    """
    id: str
    role: str
    content: str | list[dict[str, Any]]
    timestamp: float = field(default_factory=time.time)
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert the entry to a dictionary.
        
        Returns:
            Dictionary representation of the entry.
        """
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "tokens_used": self.tokens_used,
            "cost_usd": self.cost_usd,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> HistoryEntry:
        """Create a HistoryEntry from a dictionary.
        
        Args:
            data: Dictionary containing entry data.
            
        Returns:
            A new HistoryEntry instance.
        """
        return cls(
            id=data["id"],
            role=data["role"],
            content=data["content"],
            timestamp=data.get("timestamp", time.time()),
            tokens_used=data.get("tokens_used"),
            cost_usd=data.get("cost_usd"),
            metadata=data.get("metadata", {}),
        )


class HistoryManager:
    """Manages conversation history.
    
    Stores history in memory and optionally persists to disk. Uses pathlib.Path
    for file operations and provides thread-safe access to history entries.
    
    Attributes:
        storage_path: Path to the persistent storage file
        max_entries: Maximum number of entries to retain in memory
    
    Example:
        >>> manager = HistoryManager(storage_path="./history.json")
        >>> manager.add_user("Hello, world!")
        >>> messages = manager.get_messages(limit=10)
        >>> manager.save()
    """
    
    def __init__(
        self,
        storage_path: Optional[str | Path] = None,
        max_entries: int = DEFAULT_MAX_ENTRIES,
    ):
        self._storage_path = Path(storage_path) if storage_path else None
        self._max_entries = max_entries
        self._entries: list[HistoryEntry] = []
        self._session_id = self._generate_session_id()
        self._last_save = time.time()
        
        if self._storage_path and self._storage_path.exists():
            self._load()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID.
        
        Returns:
            An 8-character hex string for session identification.
        """
        return uuid4().hex[:8]
    
    def add(
        self,
        role: str,
        content: str | list[dict[str, Any]],
        **metadata: Any,
    ) -> HistoryEntry:
        """Add a new history entry.
        
        Args:
            role: Message role (user/assistant/system)
            content: Message content (string or list of content blocks)
            **metadata: Additional metadata to attach to the entry
            
        Returns:
            The created HistoryEntry instance.
        """
        entry_id = f"{role}_{len(self._entries)}"
        
        entry = HistoryEntry(
            id=entry_id,
            role=role,
            content=content,
            metadata=metadata,
        )
        
        self._entries.append(entry)
        
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        
        if time.time() - self._last_save > AUTO_SAVE_INTERVAL_SECONDS:
            self.save()
        
        return entry
    
    def add_user(self, content: str, **metadata: Any) -> HistoryEntry:
        """Add a user message to the history.
        
        Args:
            content: The user's message content
            **metadata: Additional metadata
            
        Returns:
            The created HistoryEntry.
        """
        return self.add("user", content, **metadata)
    
    def add_assistant(
        self,
        content: str | list[dict[str, Any]],
        **metadata: Any,
    ) -> HistoryEntry:
        """Add an assistant message to the history.
        
        Args:
            content: The assistant's message content
            **metadata: Additional metadata
            
        Returns:
            The created HistoryEntry.
        """
        return self.add("assistant", content, **metadata)
    
    def add_system(self, content: str, **metadata: Any) -> HistoryEntry:
        """Add a system message to the history.
        
        Args:
            content: The system message content
            **metadata: Additional metadata
            
        Returns:
            The created HistoryEntry.
        """
        return self.add("system", content, **metadata)
    
    def get_messages(self, limit: Optional[int] = None) -> list[dict[str, Any]]:
        """Get messages in API format.
        
        Args:
            limit: Maximum number of messages to return (most recent)
            
        Returns:
            List of messages suitable for API calls.
        """
        entries = self._entries[-limit:] if limit else self._entries
        
        return [
            {"role": e.role, "content": e.content}
            for e in entries
        ]
    
    def get_entries(self, limit: Optional[int] = None) -> list[HistoryEntry]:
        """Get history entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of HistoryEntry objects.
        """
        if limit:
            return self._entries[-limit:]
        return self._entries.copy()
    
    def search(self, query: str, limit: int = 10) -> list[HistoryEntry]:
        """Search history for entries containing query.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching HistoryEntry objects, most recent first.
        """
        results: list[HistoryEntry] = []
        query_lower = query.lower()
        
        for entry in reversed(self._entries):
            content = entry.content
            if isinstance(content, list):
                content = " ".join(
                    c.get("text", "") for c in content if c.get("type") == "text"
                )
            
            if query_lower in content.lower():
                results.append(entry)
                
                if len(results) >= limit:
                    break
        
        return results

    def archive_session_messages(
        self,
        session_id: str,
        messages: list[dict[str, Any]],
        *,
        working_directory: str | None = None,
        model: str | None = None,
        replace_existing: bool = False,
    ) -> int:
        """Archive persisted session messages into history storage.

        Session is the source-of-truth for active conversations. This method
        materializes a stable, searchable archive in history.

        Args:
            session_id: Session identifier.
            messages: Serialized session message list.
            working_directory: Optional working directory metadata.
            model: Optional model metadata.
            replace_existing: If True, drop existing archive entries for session first.

        Returns:
            Number of newly archived entries.
        """
        if replace_existing:
            self._entries = [
                entry
                for entry in self._entries
                if entry.metadata.get("session_id") != session_id
            ]

        existing_message_ids = {
            str(entry.metadata.get("message_id"))
            for entry in self._entries
            if entry.metadata.get("session_id") == session_id
            and entry.metadata.get("message_id") is not None
        }

        archived_count = 0
        now = time.time()
        for index, message in enumerate(messages):
            message_id = str(message.get("id") or f"message-{index}")
            if message_id in existing_message_ids:
                continue

            role = str(message.get("role", "assistant"))
            content = message.get("content", "")
            timestamp = float(message.get("timestamp") or now)

            metadata = dict(message.get("metadata") or {})
            metadata.update(
                {
                    "session_id": session_id,
                    "message_id": message_id,
                    "archived_from": "session",
                }
            )
            if working_directory:
                metadata["working_directory"] = working_directory
            if model:
                metadata["model"] = model
            if message.get("tool_call_id"):
                metadata["tool_call_id"] = message.get("tool_call_id")
            if message.get("tool_name"):
                metadata["tool_name"] = message.get("tool_name")

            self._entries.append(
                HistoryEntry(
                    id=f"{session_id}:{message_id}",
                    role=role,
                    content=content,
                    timestamp=timestamp,
                    metadata=metadata,
                )
            )
            existing_message_ids.add(message_id)
            archived_count += 1

        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries :]

        if archived_count > 0:
            self.save()

        return archived_count

    def get_session_entries(
        self,
        session_id: str,
        limit: Optional[int] = None,
    ) -> list[HistoryEntry]:
        """Get archived history entries for a specific session."""
        entries = [
            entry
            for entry in self._entries
            if entry.metadata.get("session_id") == session_id
        ]
        entries.sort(key=lambda item: item.timestamp)
        if limit:
            return entries[-limit:]
        return entries
    
    def clear(self) -> None:
        """Clear all history and generate a new session ID."""
        self._entries.clear()
        self._session_id = self._generate_session_id()
    
    def save(self) -> bool:
        """Save history to disk.
        
        Returns:
            True if saved successfully, False otherwise.
        """
        if not self._storage_path:
            return False
        
        try:
            data: dict[str, Any] = {
                "session_id": self._session_id,
                "entries": [e.to_dict() for e in self._entries],
            }
            
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            self._last_save = time.time()
            return True
            
        except Exception:
            return False
    
    def _load(self) -> None:
        """Load history from disk."""
        if not self._storage_path or not self._storage_path.exists():
            return
        
        try:
            with open(self._storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            self._session_id = data.get("session_id", self._generate_session_id())
            self._entries = [
                HistoryEntry.from_dict(e) for e in data.get("entries", [])
            ]
            
        except Exception:
            pass
    
    @property
    def session_id(self) -> str:
        """Get current session ID.
        
        Returns:
            The unique session identifier.
        """
        return self._session_id
    
    def __len__(self) -> int:
        """Get number of entries.
        
        Returns:
            The count of history entries.
        """
        return len(self._entries)


# Global history manager
_history_manager: Optional[HistoryManager] = None


def get_history_manager() -> HistoryManager:
    """Get the global history manager instance."""
    global _history_manager
    if _history_manager is None:
        _history_manager = HistoryManager()
    return _history_manager
