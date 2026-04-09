"""Session Management for Claude Code Python.

Handles conversation persistence and history.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from uuid import uuid4

logger = logging.getLogger(__name__)


DEFAULT_STORAGE_DIR = Path.home() / ".claude-code-python" / "sessions"
DEFAULT_MODEL = "claude-sonnet-4-20250514"


@dataclass(frozen=True, slots=True)
class SessionMetadata:
    """Metadata for a session.

    Attributes:
        id: Unique session identifier.
        created_at: Unix timestamp when session was created.
        last_active: Unix timestamp of last activity.
        working_directory: Working directory for the session.
        model: Model being used.
        message_count: Number of messages in the session.
        tool_call_count: Number of tool calls in the session.
    """

    id: str
    created_at: float
    last_active: float
    working_directory: str
    model: str
    message_count: int = 0
    tool_call_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "id": self.id,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "working_directory": self.working_directory,
            "model": self.model,
            "message_count": self.message_count,
            "tool_call_count": self.tool_call_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SessionMetadata:
        """Create from dictionary.

        Args:
            data: Dictionary with session data.

        Returns:
            SessionMetadata instance.
        """
        return cls(
            id=data["id"],
            created_at=data["created_at"],
            last_active=data["last_active"],
            working_directory=data["working_directory"],
            model=data["model"],
            message_count=data.get("message_count", 0),
            tool_call_count=data.get("tool_call_count", 0),
        )


@dataclass(frozen=True, slots=True)
class MessageRecord:
    """A recorded message in the session.

    Attributes:
        id: Unique message identifier.
        role: Message role (user, assistant, system).
        content: Message content (string or list of content blocks).
        timestamp: Unix timestamp of the message.
        tool_call_id: ID of associated tool call.
        tool_name: Name of associated tool.
        metadata: Additional message metadata.
    """

    id: str
    role: str
    content: str | list[dict[str, Any]]
    timestamp: float
    tool_call_id: str | None = None
    tool_name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation.
        """
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "tool_call_id": self.tool_call_id,
            "tool_name": self.tool_name,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MessageRecord:
        """Create from dictionary.

        Args:
            data: Dictionary with message data.

        Returns:
            MessageRecord instance.
        """
        return cls(
            id=data["id"],
            role=data["role"],
            content=data["content"],
            timestamp=data["timestamp"],
            tool_call_id=data.get("tool_call_id"),
            tool_name=data.get("tool_name"),
            metadata=data.get("metadata", {}),
        )


class SessionStore:
    """Storage for session data."""

    def __init__(self, storage_dir: Path | str | None = None) -> None:
        """Initialize SessionStore.

        Args:
            storage_dir: Directory for session storage (default: ~/.claude-code-python/sessions).
        """
        self._storage_dir = Path(storage_dir) if storage_dir else DEFAULT_STORAGE_DIR
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    @property
    def storage_dir(self) -> Path:
        """Get the storage directory."""
        return self._storage_dir

    def _get_session_path(self, session_id: str) -> Path:
        """Get path for session file.

        Args:
            session_id: Session identifier.

        Returns:
            Path to the session file.
        """
        return self._storage_dir / f"{session_id}.json"

    def save_session(self, session: "Session") -> None:
        """Save a session to disk.

        Args:
            session: The session to save.
        """
        path = self._get_session_path(session.id)
        data = {
            "metadata": session.metadata.to_dict(),
            "messages": [msg.to_dict() for msg in session.messages],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_session(self, session_id: str) -> Session | None:
        """Load a session from disk.

        Args:
            session_id: Session identifier.

        Returns:
            Session instance or None if not found.
        """
        path = self._get_session_path(session_id)

        if not path.is_file():
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            metadata = SessionMetadata.from_dict(data["metadata"])
            messages = [MessageRecord.from_dict(m) for m in data["messages"]]

            session = Session(
                metadata=metadata,
                messages=messages,
            )
            return session

        except Exception as e:
            logger.error(f"Error loading session: {e}")
            return None

    def list_sessions(self) -> list[SessionMetadata]:
        """List all saved sessions.

        Returns:
            List of session metadata, sorted by last active.
        """
        sessions: list[SessionMetadata] = []

        for path in self._storage_dir.glob("*.json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sessions.append(SessionMetadata.from_dict(data["metadata"]))
            except Exception:
                continue

        sessions.sort(key=lambda s: s.last_active, reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session identifier.

        Returns:
            True if deleted, False if not found.
        """
        path = self._get_session_path(session_id)
        if path.is_file():
            path.unlink()
            return True
        return False


class Session:
    """A conversation session.

    Tracks messages, tool calls, and provides persistence.
    """

    def __init__(
        self,
        metadata: SessionMetadata | None = None,
        messages: list[MessageRecord] | None = None,
    ) -> None:
        """Initialize Session.

        Args:
            metadata: Session metadata (created if not provided).
            messages: List of message records.
        """
        if metadata:
            self._metadata = metadata
        else:
            self._metadata = SessionMetadata(
                id=str(uuid4()),
                created_at=time.time(),
                last_active=time.time(),
                working_directory=os.getcwd(),
                model=os.getenv("CLAUDE_MODEL", DEFAULT_MODEL),
            )
        self._messages = messages or []
        self._store: SessionStore | None = None

    @property
    def metadata(self) -> SessionMetadata:
        """Get session metadata."""
        return self._metadata

    @property
    def messages(self) -> list[MessageRecord]:
        """Get session messages."""
        return self._messages

    @property
    def id(self) -> str:
        """Get session ID."""
        return self._metadata.id

    def attach_store(self, store: SessionStore) -> None:
        """Attach a session store for auto-save.

        Args:
            store: The session store to attach.
        """
        self._store = store

    def add_message(
        self,
        role: str,
        content: str | list[dict[str, Any]],
        **kwargs: Any,
    ) -> MessageRecord:
        """Add a message to the session.

        Args:
            role: Message role.
            content: Message content.
            **kwargs: Additional message fields (id, timestamp, tool_call_id, tool_name, metadata).

        Returns:
            The created MessageRecord.
        """
        msg = MessageRecord(
            id=kwargs.get("id", str(uuid4())),
            role=role,
            content=content,
            timestamp=kwargs.get("timestamp", time.time()),
            tool_call_id=kwargs.get("tool_call_id"),
            tool_name=kwargs.get("tool_name"),
            metadata=kwargs.get("metadata", {}),
        )
        self._messages.append(msg)
        self._metadata.message_count += 1
        self._metadata.last_active = time.time()

        if self._store:
            self._store.save_session(self)

        return msg

    def add_user_message(self, content: str) -> MessageRecord:
        """Add a user message.

        Args:
            content: Message content.

        Returns:
            The created MessageRecord.
        """
        return self.add_message(role="user", content=content)

    def add_assistant_message(self, content: str) -> MessageRecord:
        """Add an assistant message.

        Args:
            content: Message content.

        Returns:
            The created MessageRecord.
        """
        return self.add_message(role="assistant", content=content)

    def add_tool_result(
        self,
        tool_call_id: str,
        tool_name: str,
        content: str,
    ) -> MessageRecord:
        """Add a tool result as a user message.

        Args:
            tool_call_id: ID of the tool call.
            tool_name: Name of the tool.
            content: Result content.

        Returns:
            The created MessageRecord.
        """
        return self.add_message(
            role="user",
            content=content,
            tool_call_id=tool_call_id,
            tool_name=tool_name,
        )

    def get_messages(self) -> list[dict[str, Any]]:
        """Get all messages as dicts for API.

        Returns:
            List of message dictionaries.
        """
        return [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in self._messages
        ]

    def clear(self) -> None:
        """Clear session messages."""
        self._messages.clear()
        self._metadata.message_count = 0
        self._metadata.last_active = time.time()

        if self._store:
            self._store.save_session(self)

    def save(self) -> None:
        """Manually save session."""
        if self._store:
            self._store.save_session(self)

    def to_dict(self) -> dict[str, Any]:
        """Export session as dict.

        Returns:
            Dictionary representation.
        """
        return {
            "metadata": self._metadata.to_dict(),
            "messages": [msg.to_dict() for msg in self._messages],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        """Create session from dict.

        Args:
            data: Dictionary with session data.

        Returns:
            Session instance.
        """
        metadata = SessionMetadata.from_dict(data["metadata"])
        messages = [MessageRecord.from_dict(m) for m in data["messages"]]
        return cls(metadata=metadata, messages=messages)


class SessionManager:
    """Manages multiple sessions.

    Handles creating, loading, and switching between sessions.
    """

    def __init__(self, storage_dir: Path | str | None = None) -> None:
        """Initialize SessionManager.

        Args:
            storage_dir: Directory for session storage.
        """
        self._store = SessionStore(storage_dir)
        self._current_session: Session | None = None
        self._sessions: dict[str, Session] = {}

    @property
    def current_session(self) -> Session | None:
        """Get the current session."""
        return self._current_session

    @property
    def sessions(self) -> dict[str, Session]:
        """Get all managed sessions."""
        return self._sessions

    def create_session(self) -> Session:
        """Create a new session.

        Returns:
            The created session.
        """
        session = Session()
        session.attach_store(self._store)
        self._current_session = session
        self._sessions[session.id] = session
        self._store.save_session(session)
        return session

    def load_session(self, session_id: str) -> Session | None:
        """Load an existing session.

        Args:
            session_id: Session identifier.

        Returns:
            Session or None if not found.
        """
        session = self._store.load_session(session_id)
        if session:
            session.attach_store(self._store)
            self._current_session = session
            self._sessions[session.id] = session
        return session

    def switch_session(self, session_id: str) -> Session | None:
        """Switch to a different session.

        Args:
            session_id: Session identifier.

        Returns:
            Session or None if not found.
        """
        if session_id in self._sessions:
            self._current_session = self._sessions[session_id]
            return self._current_session

        return self.load_session(session_id)

    def list_sessions(self) -> list[SessionMetadata]:
        """List all sessions.

        Returns:
            List of session metadata.
        """
        return self._store.list_sessions()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session.

        Args:
            session_id: Session identifier.

        Returns:
            True if deleted.
        """
        if session_id in self._sessions:
            del self._sessions[session_id]

        if self._current_session and self._current_session.id == session_id:
            self._current_session = None

        return self._store.delete_session(session_id)

    def get_current_session(self) -> Session | None:
        """Get the current session.

        Returns:
            Current session or None.
        """
        return self._current_session

    def ensure_current_session(self) -> Session:
        """Ensure there's a current session.

        Returns:
            The current session.
        """
        if not self._current_session:
            return self.create_session()
        return self._current_session