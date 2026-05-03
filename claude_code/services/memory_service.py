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
VALID_MEMORY_SCOPES: frozenset[str] = frozenset({"user", "project", "local"})
DEFAULT_MEMORY_SCOPE = "project"


def _normalize_memory_scope(scope: str | None) -> str:
    """Normalize and validate memory scope."""
    candidate = (scope or DEFAULT_MEMORY_SCOPE).strip().lower()
    if candidate not in VALID_MEMORY_SCOPES:
        raise ValueError(f"Invalid memory scope: {scope}")
    return candidate


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

    This store is reserved for long-term structured knowledge and should not be
    used as a duplicate sink for active session transcripts or history archives.
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

    @staticmethod
    def _scope_namespace(
        scope: str,
        working_directory: Path | str | None = None,
    ) -> str:
        """Build deterministic namespace for a memory scope."""
        normalized_scope = _normalize_memory_scope(scope)
        if normalized_scope == "user":
            return "user"

        base_path = Path(working_directory).expanduser() if working_directory else Path.cwd()
        resolved = str(base_path.resolve(strict=False))
        digest = hashlib.md5(resolved.encode("utf-8")).hexdigest()[:16]
        return f"{normalized_scope}:{digest}"

    @classmethod
    def _scoped_key(
        cls,
        scope: str,
        key: str,
        working_directory: Path | str | None = None,
    ) -> str:
        namespace = cls._scope_namespace(scope, working_directory=working_directory)
        return f"{namespace}/{key}"

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

    async def set_scoped(
        self,
        scope: str,
        key: str,
        value: Any,
        *,
        working_directory: Path | str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store value inside a scoped memory namespace."""
        normalized_scope = _normalize_memory_scope(scope)
        namespaced_key = self._scoped_key(
            normalized_scope,
            key,
            working_directory=working_directory,
        )
        namespace = self._scope_namespace(
            normalized_scope,
            working_directory=working_directory,
        )
        merged_tags = list(tags or [])
        scope_tag = f"scope:{normalized_scope}"
        if scope_tag not in merged_tags:
            merged_tags.append(scope_tag)
        merged_metadata = dict(metadata or {})
        merged_metadata.setdefault("scope", normalized_scope)
        merged_metadata.setdefault("scope_namespace", namespace)
        await self.set(
            namespaced_key,
            value,
            tags=merged_tags,
            metadata=merged_metadata,
        )

    async def get_scoped(
        self,
        scope: str,
        key: str,
        *,
        working_directory: Path | str | None = None,
        default: Any = None,
    ) -> Any:
        """Read value from a scoped memory namespace."""
        normalized_scope = _normalize_memory_scope(scope)
        namespaced_key = self._scoped_key(
            normalized_scope,
            key,
            working_directory=working_directory,
        )
        return await self.get(namespaced_key, default)

    async def delete_scoped(
        self,
        scope: str,
        key: str,
        *,
        working_directory: Path | str | None = None,
    ) -> bool:
        """Delete value from a scoped memory namespace."""
        normalized_scope = _normalize_memory_scope(scope)
        namespaced_key = self._scoped_key(
            normalized_scope,
            key,
            working_directory=working_directory,
        )
        return await self.delete(namespaced_key)

    async def keys_scoped(
        self,
        scope: str,
        *,
        working_directory: Path | str | None = None,
    ) -> list[str]:
        """List keys inside a scoped memory namespace."""
        normalized_scope = _normalize_memory_scope(scope)
        namespace = self._scope_namespace(
            normalized_scope,
            working_directory=working_directory,
        )
        prefix = f"{namespace}/"
        scoped_keys = await self.keys(pattern=f"{prefix}*")
        return [key[len(prefix) :] for key in scoped_keys if key.startswith(prefix)]

    def snapshot_scoped(
        self,
        scope: str,
        *,
        working_directory: Path | str | None = None,
        limit: int = 12,
    ) -> dict[str, Any]:
        """Build best-effort scoped snapshot for runtime context injection."""
        normalized_scope = _normalize_memory_scope(scope)
        namespace = self._scope_namespace(
            normalized_scope,
            working_directory=working_directory,
        )
        prefix = f"{namespace}/"
        snapshot: dict[str, Any] = {}
        for key, entry in self._memory.items():
            if not key.startswith(prefix):
                continue
            short_key = key[len(prefix) :]
            snapshot[short_key] = entry.value
            if len(snapshot) >= limit:
                break
        return snapshot

    def supported_scopes(self) -> tuple[str, ...]:
        """Return supported memory scopes."""
        return tuple(sorted(VALID_MEMORY_SCOPES))

    async def set_knowledge(
        self,
        key: str,
        value: Any,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store long-term knowledge explicitly.

        Use this API when saving durable, structured memory. It marks entries
        with a ``knowledge`` tag and metadata kind.
        """
        merged_tags = list(tags or [])
        if "knowledge" not in merged_tags:
            merged_tags.append("knowledge")

        merged_metadata = dict(metadata or {})
        merged_metadata.setdefault("kind", "knowledge")
        await self.set(key, value, tags=merged_tags, metadata=merged_metadata)

    async def list_knowledge_keys(self) -> list[str]:
        """List keys marked as long-term knowledge."""
        async with self._lock:
            return [
                key
                for key, entry in self._memory.items()
                if "knowledge" in entry.tags or entry.metadata.get("kind") == "knowledge"
            ]


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
