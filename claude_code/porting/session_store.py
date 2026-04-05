"""
Claude Code Python - Session Store

Provides session persistence functionality for saving and loading
conversation sessions.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


DEFAULT_SESSION_DIR = Path.home() / ".claude" / "sessions"


@dataclass(frozen=True)
class StoredSession:
    """A persisted session.
    
    Attributes:
        session_id: Unique session identifier
        messages: Tuple of message strings
        input_tokens: Total input tokens used
        output_tokens: Total output tokens used
        created_at: When the session was created
        metadata: Additional session metadata
    """
    session_id: str
    messages: tuple[str, ...]
    input_tokens: int
    output_tokens: int
    created_at: str = ""
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            object.__setattr__(self, 'metadata', {})


def save_session(
    session: StoredSession,
    directory: Optional[Path] = None,
) -> Path:
    """Save a session to disk.
    
    Args:
        session: The session to save
        directory: Optional custom directory
        
    Returns:
        Path to the saved session file
    """
    target_dir = directory or DEFAULT_SESSION_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    
    path = target_dir / f"{session.session_id}.json"
    path.write_text(json.dumps(asdict(session), indent=2), encoding="utf-8")
    return path


def load_session(
    session_id: str,
    directory: Optional[Path] = None,
) -> StoredSession:
    """Load a session from disk.
    
    Args:
        session_id: The session ID to load
        directory: Optional custom directory
        
    Returns:
        The loaded StoredSession
    """
    target_dir = directory or DEFAULT_SESSION_DIR
    path = target_dir / f"{session_id}.json"
    
    if not path.exists():
        raise FileNotFoundError(f"Session not found: {session_id}")
    
    data = json.loads(path.read_text(encoding="utf-8"))
    return StoredSession(
        session_id=data["session_id"],
        messages=tuple(data["messages"]),
        input_tokens=data["input_tokens"],
        output_tokens=data["output_tokens"],
        created_at=data.get("created_at", ""),
        metadata=data.get("metadata", {}),
    )


def list_sessions(
    directory: Optional[Path] = None,
) -> list[str]:
    """List all available sessions.
    
    Args:
        directory: Optional custom directory
        
    Returns:
        List of session IDs
    """
    target_dir = directory or DEFAULT_SESSION_DIR
    
    if not target_dir.exists():
        return []
    
    return [
        p.stem for p in target_dir.glob("*.json")
        if p.is_file()
    ]


def delete_session(
    session_id: str,
    directory: Optional[Path] = None,
) -> bool:
    """Delete a session.
    
    Args:
        session_id: The session ID to delete
        directory: Optional custom directory
        
    Returns:
        True if deleted, False if not found
    """
    target_dir = directory or DEFAULT_SESSION_DIR
    path = target_dir / f"{session_id}.json"
    
    if path.exists():
        path.unlink()
        return True
    return False


def get_session_path(
    session_id: str,
    directory: Optional[Path] = None,
) -> Path:
    """Get the path for a session file.
    
    Args:
        session_id: The session ID
        directory: Optional custom directory
        
    Returns:
        Path to the session file
    """
    target_dir = directory or DEFAULT_SESSION_DIR
    return target_dir / f"{session_id}.json"


__all__ = [
    "StoredSession",
    "DEFAULT_SESSION_DIR",
    "save_session",
    "load_session",
    "list_sessions",
    "delete_session",
    "get_session_path",
]