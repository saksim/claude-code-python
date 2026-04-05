"""Session Memory Service for Claude Code Python.

Provides session-based memory storage for persisting context across sessions.
"""

from __future__ import annotations

import fnmatch
import hashlib
import json
from asyncio import Lock
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_STORAGE_DIR = Path.home() / ".claude" / "memory"


@dataclass(slots=True)
class MemoryEntry:
    """A single memory entry.

    Attributes:
        key: Unique identifier for the memory.
        value: The stored value.
        created_at: When the entry was created.
        updated_at: When the entry was last updated.
        access_count: Number of times the entry has been accessed.
        last_accessed: When the entry was last accessed.
        tags: Tags associated with the entry.
        metadata: Additional metadata.
    """

    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: datetime | None = None
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionMemory:
    """Session memory storage.

    Provides persistent memory storage that survives across sessions.
    Useful for storing user preferences, project context, and learned information.
    """

    def __init__(self, storage_dir: Path | str | None = None) -> None:
        """Initialize session memory.

        Args:
            storage_dir: Directory for storing memory data (default: ~/.claude/memory).
        """
        self._storage_dir = Path(storage_dir) if storage_dir else DEFAULT_STORAGE_DIR
        self._memory: dict[str, MemoryEntry] = {}
        self._lock = Lock()

        self._storage_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _get_file_path(self, namespace: str = "default") -> Path:
        """Get the file path for a namespace.

        Args:
            namespace: Memory namespace identifier.

        Returns:
            Path to the storage file.
        """
        safe_name = hashlib.md5(namespace.encode()).hexdigest()[:16]
        return self._storage_dir / f"{safe_name}.json"

    def _load(self) -> None:
        """Load memory from disk."""
        try:
            file_path = self._get_file_path()
            if file_path.is_file():
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                for key, value in data.items():
                    entry = MemoryEntry(
                        key=key,
                        value=value.get("value"),
                        created_at=datetime.fromisoformat(
                            value.get("created_at", datetime.now().isoformat())
                        ),
                        updated_at=datetime.fromisoformat(
                            value.get("updated_at", datetime.now().isoformat())
                        ),
                        access_count=value.get("access_count", 0),
                        tags=value.get("tags", []),
                        metadata=value.get("metadata", {}),
                    )
                    self._memory[key] = entry
        except Exception:
            pass

    def _save(self) -> None:
        """Save memory to disk."""
        try:
            data = {}
            for key, entry in self._memory.items():
                data[key] = {
                    "value": entry.value,
                    "created_at": entry.created_at.isoformat(),
                    "updated_at": entry.updated_at.isoformat(),
                    "access_count": entry.access_count,
                    "tags": entry.tags,
                    "metadata": entry.metadata,
                }

            file_path = self._get_file_path()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception:
            pass

    async def set(
        self,
        key: str,
        value: Any,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store a value in memory.

        Args:
            key: Unique identifier for the memory.
            value: Value to store.
            tags: Optional tags for categorization.
            metadata: Optional metadata dictionary.
        """
        async with self._lock:
            now = datetime.now()

            if key in self._memory:
                entry = self._memory[key]
                entry.value = value  # type: ignore[attr-defined]
                entry.updated_at = now  # type: ignore[attr-defined]
                if tags:
                    entry.tags = tags  # type: ignore[attr-defined]
                if metadata:
                    entry.metadata = metadata  # type: ignore[attr-defined]
            else:
                self._memory[key] = MemoryEntry(
                    key=key,
                    value=value,
                    created_at=now,
                    updated_at=now,
                    tags=tags or [],
                    metadata=metadata or {},
                )

            self._save()

    async def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from memory.

        Args:
            key: Unique identifier for the memory.
            default: Default value if key not found.

        Returns:
            The stored value or default.
        """
        async with self._lock:
            entry = self._memory.get(key)
            if entry is None:
                return default

            now = datetime.now()
            entry.access_count += 1  # type: ignore[attr-defined]
            entry.last_accessed = now  # type: ignore[attr-defined]

            return entry.value

    async def delete(self, key: str) -> bool:
        """Delete a value from memory.

        Args:
            key: Unique identifier for the memory.

        Returns:
            True if the key was deleted, False if not found.
        """
        async with self._lock:
            if key in self._memory:
                del self._memory[key]
                self._save()
                return True
            return False

    async def exists(self, key: str) -> bool:
        """Check if a key exists in memory.

        Args:
            key: Unique identifier to check.

        Returns:
            True if the key exists.
        """
        return key in self._memory

    async def keys(self, pattern: str | None = None) -> list[str]:
        """Get all keys, optionally filtered by pattern.

        Args:
            pattern: Optional fnmatch pattern to filter keys.

        Returns:
            List of matching keys.
        """
        async with self._lock:
            keys = list(self._memory.keys())

            if pattern:
                keys = [k for k in keys if fnmatch.fnmatch(k, pattern)]

            return keys

    async def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[tuple[str, Any, float]]:
        """Search memory for entries matching query.

        Args:
            query: Search query string.
            limit: Maximum number of results to return.

        Returns:
            List of (key, value, score) tuples sorted by relevance.
        """
        async with self._lock:
            results: list[tuple[str, Any, float]] = []
            query_lower = query.lower()

            for key, entry in self._memory.items():
                score = 0.0

                if query_lower in key.lower():
                    score += 2.0

                value_str = str(entry.value).lower()
                if query_lower in value_str:
                    score += 1.0

                for tag in entry.tags:
                    if query_lower in tag.lower():
                        score += 1.5

                if score > 0:
                    results.append((key, entry.value, score))

            results.sort(key=lambda x: x[2], reverse=True)
            return results[:limit]

    async def get_stats(self) -> dict[str, Any]:
        """Get memory statistics.

        Returns:
            Dictionary with memory statistics.
        """
        async with self._lock:
            total_accesses = sum(e.access_count for e in self._memory.values())

            return {
                "total_entries": len(self._memory),
                "total_accesses": total_accesses,
                "storage_dir": str(self._storage_dir),
            }

    async def clear(self) -> None:
        """Clear all memory."""
        async with self._lock:
            self._memory.clear()
            self._save()

    async def export(self) -> dict[str, Any]:
        """Export all memory as a dictionary.

        Returns:
            Dictionary mapping keys to values.
        """
        async with self._lock:
            return {
                key: entry.value for key, entry in self._memory.items()
            }

    async def import_data(self, data: dict[str, Any]) -> None:
        """Import memory from a dictionary.

        Args:
            data: Dictionary to import.
        """
        async with self._lock:
            now = datetime.now()
            for key, value in data.items():
                self._memory[key] = MemoryEntry(
                    key=key,
                    value=value,
                    created_at=now,
                    updated_at=now,
                )
            self._save()


class MemoryNamespace:
    """A namespace within session memory for organizing related memories."""

    def __init__(self, memory: SessionMemory, namespace: str) -> None:
        """Initialize a memory namespace.

        Args:
            memory: The parent SessionMemory instance.
            namespace: Namespace identifier.
        """
        self._memory = memory
        self._namespace = namespace

    def _prefix_key(self, key: str) -> str:
        """Add namespace prefix to key.

        Args:
            key: Original key.

        Returns:
            Namespaced key.
        """
        return f"{self._namespace}:{key}"

    async def set(
        self,
        key: str,
        value: Any,
        **kwargs: Any,
    ) -> None:
        """Set a value in this namespace.

        Args:
            key: Key within the namespace.
            value: Value to store.
            **kwargs: Additional arguments for SessionMemory.set.
        """
        await self._memory.set(self._prefix_key(key), value, **kwargs)

    async def get(self, key: str, default: Any = None) -> Any:
        """Get a value from this namespace.

        Args:
            key: Key within the namespace.
            default: Default value if not found.

        Returns:
            The stored value or default.
        """
        return await self._memory.get(self._prefix_key(key), default)

    async def delete(self, key: str) -> bool:
        """Delete a value from this namespace.

        Args:
            key: Key within the namespace.

        Returns:
            True if deleted, False if not found.
        """
        return await self._memory.delete(self._prefix_key(key))

    async def keys(self) -> list[str]:
        """Get all keys in this namespace.

        Returns:
            List of keys without namespace prefix.
        """
        all_keys = await self._memory.keys()
        prefix = self._namespace + ":"
        return [k[len(prefix) :] for k in all_keys if k.startswith(prefix)]


_memory: SessionMemory | None = None


def get_memory() -> SessionMemory:
    """Get global session memory instance.

    Returns:
        The global SessionMemory singleton.
    """
    global _memory
    if _memory is None:
        _memory = SessionMemory()
    return _memory


def get_namespace(name: str) -> MemoryNamespace:
    """Get a memory namespace.

    Args:
        name: Namespace identifier.

    Returns:
        A MemoryNamespace instance.
    """
    return MemoryNamespace(get_memory(), name)