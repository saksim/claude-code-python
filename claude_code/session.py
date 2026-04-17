"""Claude Code Python - Session Persistence."""

from __future__ import annotations

import json
import os
import warnings
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

warnings.warn(
    f"{__name__} is deprecated and will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)


@dataclass(frozen=True, slots=True)
class StoredSession:
    """Immutable session data for persistence."""

    session_id: str
    created_at: str
    messages: tuple[str, ...]
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = "claude-sonnet-4-20250514"
    workspace: str = ""

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def message_count(self) -> int:
        return len(self.messages)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StoredSession":
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
        for idx, msg in enumerate(self.messages, 1):
            preview = f"{msg[:100]}..." if len(msg) > 100 else msg
            lines.append(f"{idx}. {preview}")
        return "\n".join(lines)


class SessionStore:
    """Session storage manager."""

    __slots__ = ("_storage_dir",)

    def __init__(self, storage_dir: str | Path | None = None) -> None:
        if storage_dir is None:
            storage_dir = os.path.expanduser("~/.claude-code-python/sessions")
        self._storage_dir = Path(storage_dir)
        self._storage_dir.mkdir(parents=True, exist_ok=True)

    def _session_path(self, session_id: str) -> Path:
        return self._storage_dir / f"{session_id}.json"

    def save_session(self, session: StoredSession) -> str:
        path = self._session_path(session.session_id)
        path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")
        return str(path)

    def load_session(self, session_id: str) -> Optional[StoredSession]:
        path = self._session_path(session_id)
        if not path.exists():
            return None

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return StoredSession.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def list_sessions(self, limit: int = 10) -> list[StoredSession]:
        sessions: list[StoredSession] = []
        for path in sorted(
            self._storage_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        ):
            session = self.load_session(path.stem)
            if session is not None:
                sessions.append(session)
            if len(sessions) >= limit:
                break
        return sessions

    def delete_session(self, session_id: str) -> bool:
        path = self._session_path(session_id)
        if path.exists():
            path.unlink()
            return True
        return False

    def get_session_count(self) -> int:
        return len(list(self._storage_dir.glob("*.json")))


class RuntimeSession:
    """Active runtime session."""

    __slots__ = (
        "session_id",
        "workspace",
        "model",
        "messages",
        "input_tokens",
        "output_tokens",
        "created_at",
        "last_activity",
        "_store",
    )

    def __init__(
        self,
        session_id: str | None = None,
        workspace: str | Path | None = None,
        model: str = "claude-sonnet-4-20250514",
    ) -> None:
        self.session_id = session_id or str(uuid4())[:8]
        self.workspace = str(workspace or os.getcwd())
        self.model = model

        self.messages: list[str] = []
        self.input_tokens = 0
        self.output_tokens = 0
        self.created_at = datetime.now().isoformat()
        self.last_activity = datetime.now().isoformat()

        self._store = SessionStore()

    def add_message(self, message: str) -> None:
        self.messages.append(message)
        self.last_activity = datetime.now().isoformat()

    def add_usage(self, input_tokens: int, output_tokens: int) -> None:
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def to_stored_session(self) -> StoredSession:
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
        return self._store.save_session(self.to_stored_session())

    @classmethod
    def load(cls, session_id: str) -> Optional["RuntimeSession"]:
        stored = SessionStore().load_session(session_id)
        if stored is None:
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
        return self.to_stored_session().as_markdown()


_default_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    """Get the default global session store."""
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
