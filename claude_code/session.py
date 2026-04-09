import warnings
warnings.warn(f"{__name__} is deprecated and will be removed in a future version.", DeprecationWarning, stacklevel=2)
"""
Claude Code Python - Session Persistence
Session management for conversation state and history.

Following TOP Python Dev standards:
- Frozen dataclasses for immutability
- Clear type hints
- Comprehensive docstrings
- Tuple usage for immutable sequences

Inspired by Claw version design with enhancements.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class StoredSession:
    """Immutable session data for persistence.
    
    Frozen dataclass ensures session data cannot be accidentally modified
    after creation, providing a stable record of conversation history.
    
    Attributes:
        session_id: Unique identifier for the session
        created_at: ISO timestamp when session was created
        messages: Tuple of message contents (immutable sequence)
        input_tokens: Total input tokens used in session
        output_tokens: Total output tokens used in session
        model: Model identifier used for this session
        workspace: Working directory for the session
    
    Example:
        >>> session = StoredSession(
        ...     session_id="abc123",
        ...     created_at="2024-01-15T10:30:00",
        ...     messages=("Hello", "Hi there!"),
        ... )
        >>> session.total_tokens
        0
    """
    session_id: str
    created_at: str
    messages: tuple[str, ...]
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = "claude-sonnet-4-20250514"
    workspace: str = ""
    
    @property
    def total_tokens(self) -> int:
        """Total tokens used in session (input + output)."""
        return self.input_tokens + self.output_tokens
    
    @property
    def message_count(self) -> int:
        """Number of messages in session."""
        return len(self.messages)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary suitable for JSON serialization.
        """
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StoredSession":
        """Create session from dictionary.
        
        Args:
            data: Dictionary with session properties.
            
        Returns:
            StoredSession instance.
        """
        return cls(
            session_id=data["session_id"],
            created_at=data["created_at"],
            messages=tuple(data.get("messages", [])),
            input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0),
            model=data.get("model", "claude-sonnet-4-20250514"),
            workspace=data.get("workspace", ""),
        )
    
    def as_markdown(self) -> str:
        """Generate markdown representation of session.
        
        Returns:
            Markdown formatted session summary.
        """
        lines = [
            f"# Session: {self.session_id}",
            "",
            f"**Created:** {self.created_at}",
            f"**Messages:** {self.message_count}",
            f"**Input Tokens:** {self.input_tokens:,}",
            f"**Output Tokens:** {self.output_tokens:,}",
            f"**Total Tokens:** {self.total_tokens:,}",
            f"**Model:** {self.model}",
            "",
            "## Messages",
        ]
        
        for i, msg in enumerate(self.messages, 1):
            preview = f"{msg[:100]}..." if len(msg) > 100 else msg
            lines.append(f"{i}. {preview}")
        
        return "\n".join(lines)


class SessionStore:
    """Session storage manager.
    
    Provides persistent storage for sessions, including save, load,
    list, and delete operations. Sessions are stored as JSON files
    in a configurable directory.
    
    Uses __slots__ for memory optimization.
    
    Attributes:
        _storage_dir: Directory for session storage files
    
    Example:
        >>> store = SessionStore("/path/to/sessions")
        >>> sessions = store.list_sessions(limit=5)
    """
    
    __slots__ = ('_storage_dir',)
    
    def __init__(self, storage_dir: str | Path | None = None) -> None:
        """Initialize session store.
        
        Args:
            storage_dir: Directory for session storage. Defaults to ~/.claude-code-python/sessions
        """
        if storage_dir is None:
            storage_dir = os.path.expanduser("~/.claude-code-python/sessions")
        
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)
    
    def _session_path(self, session_id: str) -> Path:
        """Get file path for session.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            Path to session file.
        """
        return self._storage_dir / f"{session_id}.json"
    
    def save_session(self, session: StoredSession) -> str:
        """Save session to storage.
        
        Args:
            session: Session to save.
            
        Returns:
            Path where session was saved.
        """
        path = self._session_path(session.session_id)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2)
        
        return str(path)
    
    def load_session(self, session_id: str) -> Optional[StoredSession]:
        """Load session from storage.
        
        Args:
            session_id: Identifier of session to load.
            
        Returns:
            StoredSession if found, None otherwise.
        """
        path = self._session_path(session_id)
        
        if not path.exists():
            return None
        
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return StoredSession.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None
    
    def list_sessions(self, limit: int = 10) -> list[StoredSession]:
        """List recent sessions.
        
        Args:
            limit: Maximum number of sessions to return.
            
        Returns:
            List of stored sessions, most recent first.
        """
        sessions: list[StoredSession] = []
        
        for path in sorted(
            self._storage_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        ):
            session = self.load_session(path.stem)
            if session:
                sessions.append(session)
            
            if len(sessions) >= limit:
                break
        
        return sessions
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session from storage.
        
        Args:
            session_id: Identifier of session to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        path = self._session_path(session_id)
        
        if path.exists():
            path.unlink()
            return True
        
        return False
    
    def get_session_count(self) -> int:
        """Get total number of stored sessions.
        
        Returns:
            Count of session files in storage.
        """
        return len(list(self._storage_dir.glob("*.json")))


class RuntimeSession:
    """Runtime session - manages active session state.
    
    Active session that tracks messages and usage during a conversation.
    Can be persisted to storage via to_stored_session().
    
    Uses __slots__ for memory optimization.
    
    Attributes:
        session_id: Unique session identifier
        workspace: Working directory for this session
        model: Model identifier
        messages: List of message contents
        input_tokens: Total input tokens used
        output_tokens: Total output tokens used
        created_at: Session creation timestamp
        last_activity: Last activity timestamp
    
    Example:
        >>> session = RuntimeSession(workspace="/project")
        >>> session.add_message("Hello")
        >>> session.save()
    """
    
    __slots__ = ('session_id', 'workspace', 'model', 'messages', 'input_tokens', 'output_tokens', 'created_at', 'last_activity', '_store')
    
    def __init__(
        self,
        session_id: str | None = None,
        workspace: str | Path | None = None,
        model: str = "claude-sonnet-4-20250514",
    ) -> None:
        """Initialize runtime session.
        
        Args:
            session_id: Optional session ID (generated if not provided)
            workspace: Working directory (defaults to current directory)
            model: Model identifier to use
        """
        self.session_id = session_id or str(uuid4())[:8]
        self.workspace = str(workspace or os.getcwd())
        self.model = model
        
        self.messages: list[str] = []
        self.input_tokens: int = 0
        self.output_tokens: int = 0
        self.created_at: str = datetime.now().isoformat()
        self.last_activity: str = datetime.now().isoformat()
        
        self._store = SessionStore()
    
    def add_message(self, message: str) -> None:
        """Add a message to the session.
        
        Args:
            message: Message content to add.
        """
        self.messages.append(message)
        self.last_activity = datetime.now().isoformat()
    
    def add_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Add usage statistics.
        
        Args:
            input_tokens: Input tokens to add.
            output_tokens: Output tokens to add.
        """
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
    
    def to_stored_session(self) -> StoredSession:
        """Convert to storable session format.
        
        Returns:
            Frozen StoredSession for persistence.
        """
        return StoredSession(
            session_id=self.session_id,
            created_at=self.created_at,
            messages=tuple(self.messages),
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            model=self.model,
            workspace=self.workspace,
        )
    
    def save(self) -> str:
        """Save session to persistent storage.
        
        Returns:
            Path where session was saved.
        """
        return self._store.save_session(self.to_stored_session())
    
    @classmethod
    def load(cls, session_id: str) -> Optional["RuntimeSession"]:
        """Load session from storage.
        
        Args:
            session_id: Identifier of session to load.
            
        Returns:
            RuntimeSession if found, None otherwise.
        """
        stored = SessionStore().load_session(session_id)
        
        if not stored:
            return None
        
        session = cls(
            session_id=stored.session_id,
            workspace=stored.workspace,
            model=stored.model,
        )
        session.messages = list(stored.messages)
        session.input_tokens = stored.input_tokens
        session.output_tokens = stored.output_tokens
        session.created_at = stored.created_at
        
        return session
    
    def as_markdown(self) -> str:
        """Generate markdown representation.
        
        Returns:
            Markdown formatted session summary.
        """
        return self.to_stored_session().as_markdown()


_default_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    """Get the default session store.
    
    Returns:
        Global SessionStore instance.
    """
    global _default_store
    if _default_store is None:
        _default_store = SessionStore()
    return _default_store


__all__ = [
    "StoredSession",
    "SessionStore",
    "RuntimeSession",
    "get_session_store",
]
