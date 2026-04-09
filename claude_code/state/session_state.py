"""
Session state management for Claude Code Python.

Handles session persistence and state management.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- pathlib.Path for file operations
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field, asdict


# Default constants
DEFAULT_MODEL: str = "claude-sonnet-4-20250514"
DEFAULT_SESSION_DIR: Path = Path.home() / ".claude" / "sessions"


@dataclass(slots=True)
class SessionMetadata:
    """Metadata for a session.
    
    Using slots=True for memory efficiency.
    
    Attributes:
        session_id: Unique session identifier
        conversation_id: Unique conversation identifier
        created_at: ISO timestamp when session was created
        updated_at: ISO timestamp when session was last updated
        model: Model identifier used for this session
        messages_count: Number of messages in the session
        total_tokens: Total tokens consumed in the session
        total_cost: Total cost in USD for the session
    """
    session_id: str
    conversation_id: str
    created_at: str
    updated_at: str
    model: str
    messages_count: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


@dataclass
class Session:
    """A conversation session.
    
    Contains all state for a Claude Code session including
    metadata, messages, context, and settings.
    
    Attributes:
        metadata: Session metadata
        messages: List of message dictionaries
        context: Session context data
        settings: Session-specific settings
    """
    metadata: SessionMetadata
    messages: list[dict[str, Any]] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    settings: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary.
        
        Returns:
            Dictionary representation of the session
        """
        return {
            "metadata": asdict(self.metadata),
            "messages": self.messages,
            "context": self.context,
            "settings": self.settings,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """Create session from dictionary.
        
        Args:
            data: Dictionary with session data
            
        Returns:
            New Session instance
        """
        return cls(
            metadata=SessionMetadata(**data.get("metadata", {})),
            messages=data.get("messages", []),
            context=data.get("context", {}),
            settings=data.get("settings", {}),
        )


class SessionStore:
    """Persistent session storage.
    
    Handles saving and loading sessions from disk using pathlib.Path.
    
    Attributes:
        storage_dir: Directory for session file storage
    
    Example:
        >>> store = SessionStore()
        >>> sessions = store.list_sessions()
        >>> session = store.load(sessions[0].session_id)
    """
    
    def __init__(self, storage_dir: Optional[str | Path] = None) -> None:
        """Initialize session store.
        
        Args:
            storage_dir: Optional custom storage directory
        """
        if storage_dir:
            self._storage_dir = Path(storage_dir)
        else:
            self._storage_dir = DEFAULT_SESSION_DIR
        
        self._storage_dir.mkdir(parents=True, exist_ok=True)
    
    @property
    def storage_dir(self) -> Path:
        """Get the storage directory path."""
        return self._storage_dir
    
    def _get_session_path(self, session_id: str) -> Path:
        """Get the file path for a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Path to the session file
        """
        return self._storage_dir / f"{session_id}.json"
    
    def save(self, session: Session) -> None:
        """Save a session to disk.
        
        Args:
            session: Session to save
        """
        path = self._get_session_path(session.metadata.session_id)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
    
    def load(self, session_id: str) -> Optional[Session]:
        """Load a session from disk.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Session if found, None otherwise
        """
        path = self._get_session_path(session_id)
        
        if not path.exists():
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return Session.from_dict(data)
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
    
    def list_sessions(self) -> list[SessionMetadata]:
        """List all saved sessions.
        
        Returns:
            List of session metadata, sorted by most recent
        """
        sessions: list[SessionMetadata] = []
        
        for path in self._storage_dir.glob("*.json"):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                sessions.append(SessionMetadata(**data.get("metadata", {})))
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
        
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        return sessions
    
    def delete(self, session_id: str) -> bool:
        """Delete a session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            True if deleted, False if not found
        """
        path = self._get_session_path(session_id)
        
        if path.exists():
            path.unlink()
            return True
        return False
    
    def get_recent(self, count: int = 10) -> list[SessionMetadata]:
        """Get the most recent sessions.
        
        Args:
            count: Maximum number of sessions to return
            
        Returns:
            List of recent session metadata
        """
        return self.list_sessions()[:count]


class SessionManager:
    """Manages the current session.
    
    Handles session creation, saving, loading, and state updates.
    
    Attributes:
        store: Session store for persistence
        current_session: Currently active session
    
    Example:
        >>> manager = SessionManager()
        >>> session = manager.create_session()
        >>> manager.add_message("user", "Hello")
        >>> manager.save_current()
    """
    
    def __init__(self, store: Optional[SessionStore] = None) -> None:
        """Initialize session manager.
        
        Args:
            store: Optional session store
        """
        self._store = store or SessionStore()
        self._current_session: Optional[Session] = None
    
    @property
    def current_session(self) -> Optional[Session]:
        """Get the current session."""
        return self._current_session
    
    def create_session(
        self,
        model: str = DEFAULT_MODEL,
    ) -> Session:
        """Create a new session.
        
        Args:
            model: Model identifier for the session
            
        Returns:
            Newly created session
        """
        session_id = uuid.uuid4().hex
        conversation_id = uuid.uuid4().hex
        now = datetime.now(timezone.utc).isoformat()
        
        self._current_session = Session(
            metadata=SessionMetadata(
                session_id=session_id,
                conversation_id=conversation_id,
                created_at=now,
                updated_at=now,
                model=model,
            ),
            messages=[],
            context={},
            settings={},
        )
        
        self._store.save(self._current_session)
        return self._current_session
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """Load an existing session.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Loaded session or None if not found
        """
        session = self._store.load(session_id)
        if session:
            self._current_session = session
        return session
    
    def save_current(self) -> None:
        """Save the current session."""
        if self._current_session:
            self._current_session = Session(
                metadata=SessionMetadata(
                    session_id=self._current_session.metadata.session_id,
                    conversation_id=self._current_session.metadata.conversation_id,
                    created_at=self._current_session.metadata.created_at,
                    updated_at=datetime.now(timezone.utc).isoformat(),
                    model=self._current_session.metadata.model,
                    messages_count=self._current_session.metadata.messages_count,
                    total_tokens=self._current_session.metadata.total_tokens,
                    total_cost=self._current_session.metadata.total_cost,
                ),
                messages=self._current_session.messages,
                context=self._current_session.context,
                settings=self._current_session.settings,
            )
            self._store.save(self._current_session)
    
    def add_message(self, role: str, content: Any) -> None:
        """Add a message to the current session.
        
        Args:
            role: Message role (user/assistant/system)
            content: Message content
        """
        if self._current_session:
            self._current_session.messages.append({
                "role": role,
                "content": content,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            self._current_session = Session(
                metadata=SessionMetadata(
                    session_id=self._current_session.metadata.session_id,
                    conversation_id=self._current_session.metadata.conversation_id,
                    created_at=self._current_session.metadata.created_at,
                    updated_at=datetime.now(timezone.utc).isoformat(),
                    model=self._current_session.metadata.model,
                    messages_count=self._current_session.metadata.messages_count + 1,
                    total_tokens=self._current_session.metadata.total_tokens,
                    total_cost=self._current_session.metadata.total_cost,
                ),
                messages=self._current_session.messages,
                context=self._current_session.context,
                settings=self._current_session.settings,
            )
    
    def update_stats(
        self,
        tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        """Update session statistics.
        
        Args:
            tokens: Tokens to add to total
            cost: Cost to add to total
        """
        if self._current_session:
            self._current_session = Session(
                metadata=SessionMetadata(
                    session_id=self._current_session.metadata.session_id,
                    conversation_id=self._current_session.metadata.conversation_id,
                    created_at=self._current_session.metadata.created_at,
                    updated_at=self._current_session.metadata.updated_at,
                    model=self._current_session.metadata.model,
                    messages_count=self._current_session.metadata.messages_count,
                    total_tokens=self._current_session.metadata.total_tokens + tokens,
                    total_cost=self._current_session.metadata.total_cost + cost,
                ),
                messages=self._current_session.messages,
                context=self._current_session.context,
                settings=self._current_session.settings,
            )
    
    def close(self) -> None:
        """Close and save the current session."""
        self.save_current()
        self._current_session = None


# Global session manager
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get the global session manager.
    
    Returns:
        Global SessionManager singleton
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def set_session_manager(manager: SessionManager) -> None:
    """Set the global session manager.
    
    Args:
        manager: SessionManager to use globally
    """
    global _session_manager
    _session_manager = manager
