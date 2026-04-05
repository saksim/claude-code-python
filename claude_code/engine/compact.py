"""Compact Service for Claude Code Python.

Handles conversation compaction to reduce token usage.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable


class CompactTrigger(Enum):
    """What triggered the compaction."""

    MANUAL = "manual"
    AUTO = "auto"
    PARTIAL = "partial"


@dataclass(frozen=True, slots=True)
class CompactionResult:
    """Result from compaction operation.

    Attributes:
        success: Whether compaction succeeded.
        summary: Generated summary text.
        original_token_count: Token count before compaction.
        compacted_token_count: Token count after compaction.
        tokens_saved: Number of tokens saved.
        error: Error message if failed.
    """

    success: bool
    summary: str | None = None
    original_token_count: int = 0
    compacted_token_count: int = 0
    tokens_saved: int = 0
    error: str | None = None


@dataclass(frozen=True, slots=True)
class CompactConfig:
    """Configuration for compaction.

    Attributes:
        auto_compact_enabled: Whether to enable auto-compaction.
        auto_compact_threshold: Token count threshold for auto-compaction.
        max_compact_tokens: Maximum tokens for summary generation.
        partial_compact_enabled: Whether to enable partial compaction.
        preserve_recent_messages: Number of recent messages to preserve.
    """

    auto_compact_enabled: bool = True
    auto_compact_threshold: int = 150000
    max_compact_tokens: int = 50000
    partial_compact_enabled: bool = True
    preserve_recent_messages: int = 10


class CompactService:
    """Service for compacting conversations.

    Compaction summarizes older conversation history to reduce
    token usage while preserving the most important context.
    """

    def __init__(
        self,
        api_client: Any,
        config: CompactConfig | None = None,
    ) -> None:
        """Initialize CompactService.

        Args:
            api_client: API client for generating summaries.
            config: Compaction configuration.
        """
        self._api_client = api_client
        self._config = config or CompactConfig()
        self._last_compact_tokens: int = 0
        self._compaction_count: int = 0

    @property
    def last_compact_tokens(self) -> int:
        """Get token count at last compaction."""
        return self._last_compact_tokens

    @property
    def compaction_count(self) -> int:
        """Get number of compactions performed."""
        return self._compaction_count

    async def should_auto_compact(
        self,
        messages: list[Any],
        token_count: int,
    ) -> bool:
        """Check if auto-compaction should trigger.

        Args:
            messages: List of conversation messages.
            token_count: Current token count.

        Returns:
            True if auto-compaction should be triggered.
        """
        if not self._config.auto_compact_enabled:
            return False

        return token_count >= self._config.auto_compact_threshold

    async def compact(
        self,
        messages: list[Any],
        context: dict[str, Any],
        trigger: CompactTrigger = CompactTrigger.MANUAL,
        custom_instructions: str | None = None,
    ) -> CompactionResult:
        """Compact conversation by summarizing older messages.

        Args:
            messages: List of conversation messages.
            context: Additional context for summarization.
            trigger: What triggered this compaction.
            custom_instructions: Optional custom instructions for summarizer.

        Returns:
            CompactionResult with summary and statistics.
        """
        if len(messages) < 4:
            return CompactionResult(
                success=False,
                error="Not enough messages to compact (minimum 4 required)",
            )

        self._compaction_count += 1
        original_count = await self._count_tokens(messages)

        try:
            summary = await self._generate_summary(
                messages,
                context,
                custom_instructions,
            )

            if not summary:
                return CompactionResult(
                    success=False,
                    error="Failed to generate summary",
                    original_token_count=original_count,
                )

            compacted_messages = self._create_compacted_messages(
                messages,
                summary,
            )

            compacted_count = await self._count_tokens(compacted_messages)
            tokens_saved = original_count - compacted_count

            self._last_compact_tokens = compacted_count

            return CompactionResult(
                success=True,
                summary=summary,
                original_token_count=original_count,
                compacted_token_count=compacted_count,
                tokens_saved=tokens_saved,
            )

        except Exception as e:
            return CompactionResult(
                success=False,
                error=str(e),
                original_token_count=original_count,
            )

    async def partial_compact(
        self,
        messages: list[Any],
        pivot_index: int,
        context: dict[str, Any],
        direction: str = "up_to",
        feedback: str | None = None,
    ) -> CompactionResult:
        """Partially compact around a specific message.

        Args:
            messages: All messages.
            pivot_index: Index to compact around.
            context: Additional context.
            direction: "up_to" or "from" pivot.
            feedback: Optional user feedback for summarizer.

        Returns:
            CompactionResult with summary and statistics.
        """
        if not self._config.partial_compact_enabled:
            return CompactionResult(
                success=False,
                error="Partial compaction is disabled",
            )

        if pivot_index < 1 or pivot_index >= len(messages):
            return CompactionResult(
                success=False,
                error="Invalid pivot index",
            )

        if direction == "up_to":
            to_summarize = messages[:pivot_index]
            to_keep = messages[pivot_index:]
        else:
            to_keep = messages[: pivot_index + 1]
            to_summarize = messages[pivot_index + 1 :]

        if len(to_summarize) < 2:
            return CompactionResult(
                success=False,
                error="Not enough messages to summarize",
            )

        original_count = await self._count_tokens(messages)

        try:
            summary = await self._generate_summary(
                to_summarize,
                context,
                f"User context: {feedback}" if feedback else None,
            )

            if not summary:
                return CompactionResult(
                    success=False,
                    error="Failed to generate summary",
                    original_token_count=original_count,
                )

            new_messages = self._create_partial_compacted_messages(
                to_summarize,
                to_keep,
                summary,
                direction,
            )

            compacted_count = await self._count_tokens(new_messages)
            tokens_saved = original_count - compacted_count

            self._last_compact_tokens = compacted_count

            return CompactionResult(
                success=True,
                summary=summary,
                original_token_count=original_count,
                compacted_token_count=compacted_count,
                tokens_saved=tokens_saved,
            )

        except Exception as e:
            return CompactionResult(
                success=False,
                error=str(e),
                original_token_count=original_count,
            )

    async def _generate_summary(
        self,
        messages: list[Any],
        context: dict[str, Any],
        custom_instructions: str | None = None,
    ) -> str | None:
        """Generate a summary of messages using the API.

        Args:
            messages: Messages to summarize.
            context: Context information.
            custom_instructions: Custom instructions for summarizer.

        Returns:
            Summary text or None if failed.
        """
        prompt = self._build_summary_prompt(messages, custom_instructions)

        try:
            response = await self._api_client.create_message(
                messages=[{"role": "user", "content": prompt}],
                options={
                    "model": context.get("model", "claude-sonnet-4-20250514"),
                    "max_tokens": self._config.max_compact_tokens,
                },
            )

            if hasattr(response, "content"):
                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text.strip()

            return None

        except Exception:
            return None

    def _build_summary_prompt(
        self,
        messages: list[Any],
        custom_instructions: str | None = None,
    ) -> str:
        """Build prompt for summarization.

        Args:
            messages: Messages to summarize.
            custom_instructions: Optional custom instructions.

        Returns:
            Formatted prompt string.
        """
        lines = [
            "You are a helpful assistant tasked with summarizing conversations.",
            "",
            "Your task is to create a concise summary that preserves:",
            "1. Key decisions and conclusions reached",
            "2. Important code changes or files modified",
            "3. Any ongoing tasks or follow-ups",
            "4. User preferences or context established",
            "",
        ]

        if custom_instructions:
            lines.append(f"Additional instructions: {custom_instructions}")
            lines.append("")

        lines.append("## Conversation to Summarize:")
        lines.append("")

        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            if isinstance(content, str):
                lines.append(f"[{role.upper()}]: {content[:500]}")
                if len(content) > 500:
                    lines.append("... (truncated)")
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text = block.get("text", "")[:500]
                            lines.append(f"[{role.upper()}]: {text}")
                        elif block.get("type") == "tool_use":
                            name = block.get("name", "unknown")
                            lines.append(f"[{role.upper()}]: (tool: {name})")
            lines.append("")

        lines.append("")
        lines.append("## Summary:")
        lines.append("Please provide a concise summary of the conversation above.")

        return "\n".join(lines)

    def _create_compacted_messages(
        self,
        original: list[Any],
        summary: str,
    ) -> list[dict[str, Any]]:
        """Create new messages list after compaction.

        Args:
            original: Original message list.
            summary: Generated summary.

        Returns:
            New message list with summary.
        """
        keep_count = self._config.preserve_recent_messages

        summary_msg: dict[str, Any] = {
            "role": "system",
            "content": f"[Earlier conversation summarized]\n\n{summary}",
            "is_compact_summary": True,
        }

        recent = original[-keep_count:] if len(original) > keep_count else []

        return [summary_msg] + recent

    def _create_partial_compacted_messages(
        self,
        summarized: list[Any],
        kept: list[Any],
        summary: str,
        direction: str,
    ) -> list[dict[str, Any]]:
        """Create new messages list after partial compaction.

        Args:
            summarized: Messages that were summarized.
            kept: Messages to keep.
            summary: Generated summary.
            direction: Direction of compaction.

        Returns:
            New message list.
        """
        summary_msg: dict[str, Any] = {
            "role": "system",
            "content": f"[Conversation summarized - {len(summarized)} messages]\n\n{summary}",
            "is_compact_summary": True,
        }

        if direction == "up_to":
            return [summary_msg] + kept
        else:
            return kept + [summary_msg]

    async def _count_tokens(self, messages: list[Any]) -> int:
        """Estimate token count for messages.

        Args:
            messages: Messages to count.

        Returns:
            Estimated token count.
        """
        total = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total += len(content) // 4
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            total += len(block.get("text", "")) // 4
        return total

    def get_compact_stats(self) -> dict[str, Any]:
        """Get compaction statistics.

        Returns:
            Dictionary with statistics.
        """
        return {
            "compaction_count": self._compaction_count,
            "last_compact_tokens": self._last_compact_tokens,
            "auto_enabled": self._config.auto_compact_enabled,
            "auto_threshold": self._config.auto_compact_threshold,
        }


class AutoCompactManager:
    """Manages automatic compaction triggering."""

    def __init__(
        self,
        compact_service: CompactService,
        on_compact_start: Callable[..., Awaitable[None]] | None = None,
        on_compact_end: Callable[..., Awaitable[None]] | None = None,
    ) -> None:
        """Initialize AutoCompactManager.

        Args:
            compact_service: The compact service to manage.
            on_compact_start: Callback before compaction starts.
            on_compact_end: Callback after compaction ends.
        """
        self._compact_service = compact_service
        self._on_compact_start = on_compact_start
        self._on_compact_end = on_compact_end
        self._monitoring = False
        self._monitor_task: asyncio.Task | None = None

    async def start_monitoring(
        self,
        get_messages: Callable[[], list[Any]],
        get_token_count: Callable[[], int],
        check_interval: float = 30.0,
    ) -> None:
        """Start monitoring for auto-compaction.

        Args:
            get_messages: Function to get current messages.
            get_token_count: Function to get current token count.
            check_interval: Interval between checks in seconds.
        """
        self._monitoring = True

        async def monitor() -> None:
            while self._monitoring:
                await asyncio.sleep(check_interval)

                if not self._monitoring:
                    break

                messages = get_messages()
                token_count = get_token_count()

                should_compact = await self._compact_service.should_auto_compact(
                    messages,
                    token_count,
                )

                if should_compact:
                    if self._on_compact_start:
                        await self._on_compact_start()

                    result = await self._compact_service.compact(
                        messages,
                        {},
                        CompactTrigger.AUTO,
                    )

                    if self._on_compact_end:
                        await self._on_compact_end(result)

        self._monitor_task = asyncio.create_task(monitor())

    async def stop_monitoring(self) -> None:
        """Stop monitoring for auto-compaction."""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass