"""Runtime event journal for audit and replay.

Stores structured events and provides filtered query/replay helpers.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4


EVENT_JOURNAL_SCHEMA_VERSION = 1
EVENT_JOURNAL_SCHEMA_KEY = "event_journal_schema_version"


@dataclass(frozen=True, slots=True)
class EventJournalEntry:
    """Single immutable event journal entry."""

    event_id: str
    version: int
    event_type: str
    sequence: int
    timestamp: float
    session_id: str | None = None
    conversation_id: str | None = None
    source: str = "runtime"
    payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "version": self.version,
            "event_type": self.event_type,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
            "conversation_id": self.conversation_id,
            "source": self.source,
            "payload": self.payload,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EventJournalEntry":
        version = int(data.get("version", EVENT_JOURNAL_SCHEMA_VERSION))
        if version <= 0:
            raise ValueError(f"invalid event journal version: {version}")

        event_type = str(data.get("event_type", "")).strip()
        if not event_type:
            raise ValueError("event_type is required")

        sequence = int(data.get("sequence", 0))
        if sequence <= 0:
            raise ValueError("sequence must be > 0")

        timestamp = float(data.get("timestamp", 0.0))
        if timestamp <= 0:
            raise ValueError("timestamp must be > 0")

        payload = data.get("payload", {})
        metadata = data.get("metadata", {})
        if not isinstance(payload, dict):
            raise ValueError("payload must be an object")
        if not isinstance(metadata, dict):
            raise ValueError("metadata must be an object")

        return cls(
            event_id=str(data.get("event_id") or uuid4().hex),
            version=version,
            event_type=event_type,
            sequence=sequence,
            timestamp=timestamp,
            session_id=data.get("session_id"),
            conversation_id=data.get("conversation_id"),
            source=str(data.get("source", "runtime")),
            payload=payload,
            metadata=metadata,
        )


class EventJournal:
    """File-backed event journal with query and replay capabilities."""

    def __init__(self, storage_path: str | Path) -> None:
        self._storage_path = Path(storage_path)
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._sequence = 1
        self._initialized = False
        self._last_parse_errors = 0
        self._last_invalid_lines = 0

    @property
    def storage_path(self) -> Path:
        return self._storage_path

    def append_event(
        self,
        *,
        event_type: str,
        payload: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        source: str = "runtime",
        metadata: Optional[dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> EventJournalEntry:
        """Append one event to journal."""
        normalized_type = str(event_type).strip()
        if not normalized_type:
            raise ValueError("event_type is required")

        with self._lock:
            self._ensure_sequence_initialized()
            entry = EventJournalEntry(
                event_id=uuid4().hex,
                version=EVENT_JOURNAL_SCHEMA_VERSION,
                event_type=normalized_type,
                sequence=self._sequence,
                timestamp=float(timestamp or time.time()),
                session_id=session_id,
                conversation_id=conversation_id,
                source=source,
                payload=dict(payload or {}),
                metadata=dict(metadata or {}),
            )
            self._sequence += 1
            self._append_line(entry)
            return entry

    def query_events(
        self,
        *,
        session_id: Optional[str] = None,
        event_types: Optional[list[str]] = None,
        limit: Optional[int] = None,
        since_sequence: Optional[int] = None,
        until_sequence: Optional[int] = None,
    ) -> list[EventJournalEntry]:
        """Query journal entries with basic filters."""
        entries = self._read_all_entries()
        types_filter = {item.strip() for item in (event_types or []) if item and item.strip()}

        filtered: list[EventJournalEntry] = []
        for entry in entries:
            if session_id and entry.session_id != session_id:
                continue
            if types_filter and entry.event_type not in types_filter:
                continue
            if since_sequence is not None and entry.sequence < since_sequence:
                continue
            if until_sequence is not None and entry.sequence > until_sequence:
                continue
            filtered.append(entry)

        filtered.sort(key=lambda item: (item.sequence, item.timestamp, item.event_id))
        if limit is not None and limit > 0:
            filtered = filtered[-limit:]
        return filtered

    def replay_events(
        self,
        *,
        session_id: Optional[str] = None,
        event_types: Optional[list[str]] = None,
        since_sequence: Optional[int] = None,
        until_sequence: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[EventJournalEntry]:
        """Replay events in stable sequence order."""
        return self.query_events(
            session_id=session_id,
            event_types=event_types,
            since_sequence=since_sequence,
            until_sequence=until_sequence,
            limit=limit,
        )

    def get_diagnostics(self) -> dict[str, Any]:
        """Return lightweight diagnostics for parser recovery visibility."""
        return {
            "storage_path": str(self._storage_path),
            "parse_errors": self._last_parse_errors,
            "invalid_lines": self._last_invalid_lines,
        }

    def _append_line(self, entry: EventJournalEntry) -> None:
        with open(self._storage_path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.to_dict(), ensure_ascii=False))
            handle.write("\n")

    def _ensure_sequence_initialized(self) -> None:
        if self._initialized:
            return
        entries = self._read_all_entries()
        if entries:
            self._sequence = max(item.sequence for item in entries) + 1
        self._initialized = True

    def _read_all_entries(self) -> list[EventJournalEntry]:
        if not self._storage_path.exists():
            self._last_parse_errors = 0
            self._last_invalid_lines = 0
            return []

        entries: list[EventJournalEntry] = []
        parse_errors = 0
        invalid_lines = 0
        with open(self._storage_path, "r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    raw_event = json.loads(line)
                    if not isinstance(raw_event, dict):
                        invalid_lines += 1
                        continue
                    entries.append(EventJournalEntry.from_dict(raw_event))
                except Exception:
                    parse_errors += 1
                    continue

        self._last_parse_errors = parse_errors
        self._last_invalid_lines = invalid_lines
        return entries


class SQLiteEventJournal:
    """SQLite-backed event journal with query/replay capabilities."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._initialize_schema()

    @property
    def storage_path(self) -> Path:
        return self._db_path

    def append_event(
        self,
        *,
        event_type: str,
        payload: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        source: str = "runtime",
        metadata: Optional[dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> EventJournalEntry:
        normalized_type = str(event_type).strip()
        if not normalized_type:
            raise ValueError("event_type is required")

        event_ts = float(timestamp or time.time())
        payload_json = json.dumps(dict(payload or {}), ensure_ascii=False)
        metadata_json = json.dumps(dict(metadata or {}), ensure_ascii=False)

        with self._lock:
            with self._connect() as conn:
                row = conn.execute(
                    "SELECT COALESCE(MAX(sequence), 0) + 1 FROM events"
                ).fetchone()
                sequence = int(row[0]) if row and row[0] is not None else 1
                event_id = uuid4().hex
                conn.execute(
                    """
                    INSERT INTO events (
                        event_id,
                        version,
                        event_type,
                        sequence,
                        timestamp,
                        session_id,
                        conversation_id,
                        source,
                        payload_json,
                        metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        EVENT_JOURNAL_SCHEMA_VERSION,
                        normalized_type,
                        sequence,
                        event_ts,
                        session_id,
                        conversation_id,
                        source,
                        payload_json,
                        metadata_json,
                    ),
                )

        return EventJournalEntry(
            event_id=event_id,
            version=EVENT_JOURNAL_SCHEMA_VERSION,
            event_type=normalized_type,
            sequence=sequence,
            timestamp=event_ts,
            session_id=session_id,
            conversation_id=conversation_id,
            source=source,
            payload=dict(payload or {}),
            metadata=dict(metadata or {}),
        )

    def query_events(
        self,
        *,
        session_id: Optional[str] = None,
        event_types: Optional[list[str]] = None,
        limit: Optional[int] = None,
        since_sequence: Optional[int] = None,
        until_sequence: Optional[int] = None,
    ) -> list[EventJournalEntry]:
        where: list[str] = []
        params: list[Any] = []
        if session_id:
            where.append("session_id = ?")
            params.append(session_id)
        normalized_types = [item.strip() for item in (event_types or []) if item and item.strip()]
        if normalized_types:
            placeholders = ",".join(["?"] * len(normalized_types))
            where.append(f"event_type IN ({placeholders})")
            params.extend(normalized_types)
        if since_sequence is not None:
            where.append("sequence >= ?")
            params.append(int(since_sequence))
        if until_sequence is not None:
            where.append("sequence <= ?")
            params.append(int(until_sequence))

        sql = """
            SELECT
                event_id,
                version,
                event_type,
                sequence,
                timestamp,
                session_id,
                conversation_id,
                source,
                payload_json,
                metadata_json
            FROM events
        """
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY sequence ASC, timestamp ASC, event_id ASC"
        if limit is not None and limit > 0:
            sql += " LIMIT ?"
            params.append(int(limit))

        with self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        entries: list[EventJournalEntry] = []
        for row in rows:
            payload = self._parse_json(row[8], default={})
            metadata = self._parse_json(row[9], default={})
            try:
                entries.append(
                    EventJournalEntry(
                        event_id=str(row[0]),
                        version=int(row[1]),
                        event_type=str(row[2]),
                        sequence=int(row[3]),
                        timestamp=float(row[4]),
                        session_id=row[5],
                        conversation_id=row[6],
                        source=str(row[7]),
                        payload=payload if isinstance(payload, dict) else {},
                        metadata=metadata if isinstance(metadata, dict) else {},
                    )
                )
            except Exception:
                continue
        return entries

    def replay_events(
        self,
        *,
        session_id: Optional[str] = None,
        event_types: Optional[list[str]] = None,
        since_sequence: Optional[int] = None,
        until_sequence: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[EventJournalEntry]:
        return self.query_events(
            session_id=session_id,
            event_types=event_types,
            since_sequence=since_sequence,
            until_sequence=until_sequence,
            limit=limit,
        )

    def get_diagnostics(self) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) FROM events").fetchone()
        count = int(row[0]) if row and row[0] is not None else 0
        return {
            "storage_path": str(self._db_path),
            "backend": "sqlite",
            "events_count": count,
            "parse_errors": 0,
            "invalid_lines": 0,
        }

    def _initialize_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS journal_metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    version INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    sequence INTEGER NOT NULL UNIQUE,
                    timestamp REAL NOT NULL,
                    session_id TEXT,
                    conversation_id TEXT,
                    source TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_session_sequence ON events (session_id, sequence)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_events_type_sequence ON events (event_type, sequence)"
            )
            version = self._read_schema_version(conn)
            if version is None:
                self._write_schema_version(conn, EVENT_JOURNAL_SCHEMA_VERSION)
            elif version > EVENT_JOURNAL_SCHEMA_VERSION:
                raise RuntimeError(
                    "Event journal SQLite schema is newer than this binary: "
                    f"{version} > {EVENT_JOURNAL_SCHEMA_VERSION}"
                )
            elif version < EVENT_JOURNAL_SCHEMA_VERSION:
                self._migrate_schema(conn, version, EVENT_JOURNAL_SCHEMA_VERSION)
                self._write_schema_version(conn, EVENT_JOURNAL_SCHEMA_VERSION)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path, timeout=5.0)

    @staticmethod
    def _parse_json(raw_value: Any, *, default: Any) -> Any:
        if not isinstance(raw_value, str):
            return default
        try:
            return json.loads(raw_value)
        except json.JSONDecodeError:
            return default

    @staticmethod
    def _read_schema_version(conn: sqlite3.Connection) -> int | None:
        row = conn.execute(
            "SELECT value FROM journal_metadata WHERE key = ?",
            (EVENT_JOURNAL_SCHEMA_KEY,),
        ).fetchone()
        if row is None:
            return None
        try:
            return int(row[0])
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _write_schema_version(conn: sqlite3.Connection, version: int) -> None:
        conn.execute(
            """
            INSERT INTO journal_metadata (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (EVENT_JOURNAL_SCHEMA_KEY, str(version)),
        )

    @staticmethod
    def _migrate_schema(conn: sqlite3.Connection, from_version: int, to_version: int) -> None:
        if from_version < 1:
            raise RuntimeError(f"Unsupported event journal schema version: {from_version}")
        if to_version != EVENT_JOURNAL_SCHEMA_VERSION:
            raise RuntimeError(f"Unsupported target event journal schema version: {to_version}")
        # Schema v1 is current. Future migrations will be appended here.


_event_journal: Optional[EventJournal | SQLiteEventJournal] = None


def get_event_journal(storage_path: Optional[str | Path] = None) -> EventJournal | SQLiteEventJournal:
    """Get global event journal singleton."""
    global _event_journal
    if _event_journal is None:
        path = storage_path or (Path.cwd() / ".claude" / "event_journal.jsonl")
        _event_journal = EventJournal(path)
    return _event_journal


def set_event_journal(journal: EventJournal | SQLiteEventJournal) -> None:
    """Override global event journal singleton."""
    global _event_journal
    _event_journal = journal


__all__ = [
    "EVENT_JOURNAL_SCHEMA_VERSION",
    "EVENT_JOURNAL_SCHEMA_KEY",
    "EventJournalEntry",
    "EventJournal",
    "SQLiteEventJournal",
    "get_event_journal",
    "set_event_journal",
]
