"""Task queue abstraction for background task dispatch."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass(frozen=True, slots=True)
class QueueItem:
    """A queued task reference."""

    task_id: str
    enqueued_at: datetime = field(default_factory=datetime.now)


class TaskQueue(ABC):
    """Queue interface used by TaskManager for dispatch."""

    @abstractmethod
    async def enqueue(self, item: QueueItem) -> None:
        """Enqueue a task reference."""

    @abstractmethod
    async def dequeue(self, timeout: Optional[float] = None) -> QueueItem | None:
        """Dequeue a task reference or return None on timeout."""

    @abstractmethod
    def qsize(self) -> int:
        """Return approximate queue size."""

    @abstractmethod
    async def clear(self) -> int:
        """Remove all queued items and return removed count."""


class InMemoryTaskQueue(TaskQueue):
    """Default in-memory queue implementation."""

    def __init__(self) -> None:
        self._queue: asyncio.Queue[QueueItem] = asyncio.Queue()

    async def enqueue(self, item: QueueItem) -> None:
        await self._queue.put(item)

    async def dequeue(self, timeout: Optional[float] = None) -> QueueItem | None:
        try:
            if timeout is None:
                return await self._queue.get()
            if timeout <= 0:
                return self._queue.get_nowait()
            return await asyncio.wait_for(self._queue.get(), timeout=timeout)
        except (asyncio.TimeoutError, asyncio.QueueEmpty):
            return None

    def qsize(self) -> int:
        return self._queue.qsize()

    async def clear(self) -> int:
        cleared = 0
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            cleared += 1
        return cleared


__all__ = ["QueueItem", "TaskQueue", "InMemoryTaskQueue"]
