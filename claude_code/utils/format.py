"""Formatting utilities for Claude Code Python."""

from __future__ import annotations

import re
import textwrap
from typing import Any


def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text to max length, adding suffix if truncated.

    Args:
        text: Text to truncate.
        max_length: Maximum length including suffix.
        suffix: String to append when truncated.

    Returns:
        Truncated text with suffix if needed.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def truncate_middle(text: str, max_length: int, suffix: str = "...") -> str:
    """Truncate text in the middle, keeping start and end.

    Args:
        text: Text to truncate.
        max_length: Maximum length including suffix.
        suffix: String to use as middle separator.

    Returns:
        Truncated text with suffix in middle.
    """
    if len(text) <= max_length:
        return text

    available = max_length - len(suffix)
    start_len = available // 2
    end_len = available - start_len

    return text[:start_len] + suffix + text[-end_len:]


def word_wrap(text: str, width: int = 80) -> str:
    """Word wrap text to specified width.

    Args:
        text: Text to wrap.
        width: Maximum line width.

    Returns:
        Wrapped text with newlines.
    """
    return "\n".join(textwrap.wrap(text, width=width))


def indent(text: str, spaces: int = 2, skip_first: bool = False) -> str:
    """Indent text by specified number of spaces.

    Args:
        text: Text to indent.
        spaces: Number of spaces for indentation.
        skip_first: Whether to skip indenting the first line.

    Returns:
        Indented text.
    """
    prefix = " " * spaces
    lines = text.split("\n")

    if skip_first and lines:
        return lines[0] + "\n" + "\n".join(prefix + line for line in lines[1:])
    return "\n".join(prefix + line for line in lines)


ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


def remove_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text.

    Args:
        text: Text containing ANSI codes.

    Returns:
        Text with ANSI codes removed.
    """
    return ANSI_ESCAPE.sub("", text)


def strip_color_codes(text: str) -> str:
    """Strip common color codes from text.

    Args:
        text: Text with color codes to remove.

    Returns:
        Cleaned text.
    """
    patterns = [
        r"<[^>]+>",  # HTML-like tags
        r"\{[^}]+\}",  # Curly brace style
    ]

    result = text
    for pattern in patterns:
        result = re.sub(pattern, "", result)

    return result


def format_duration(ms: float) -> str:
    """Format duration in milliseconds to human-readable string.

    Args:
        ms: Duration in milliseconds.

    Returns:
        Human-readable duration string.
    """
    if ms < 1000:
        return f"{ms:.0f}ms"
    if ms < 60000:
        return f"{ms / 1000:.1f}s"
    if ms < 3600000:
        return f"{ms / 60000:.1f}m"
    return f"{ms / 3600000:.1f}h"


def format_bytes(size: int) -> str:
    """Format byte size to human-readable string.

    Args:
        size: Size in bytes.

    Returns:
        Human-readable size string (e.g., "1.5 MB").
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0

    size = float(size)
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.1f}{units[unit_index]}"


def format_number(num: int) -> str:
    """Format number with thousands separators.

    Args:
        num: Number to format.

    Returns:
        Formatted number string.
    """
    return f"{num:,}"


def format_list(items: list[Any], conjunction: str = "and") -> str:
    """Format a list with proper grammar.

    Args:
        items: List of items to format.
        conjunction: Conjunction to use before last item.

    Returns:
        Formatted list string (e.g., "a, b, and c").
    """
    if not items:
        return ""
    if len(items) == 1:
        return str(items[0])
    if len(items) == 2:
        return f"{items[0]} {conjunction} {items[1]}"
    return f"{', '.join(str(x) for x in items[:-1])}, {conjunction} {items[-1]}"


def pluralize(word: str, count: int, plural: str | None = None) -> str:
    """Pluralize a word based on count.

    Args:
        word: Singular form of the word.
        count: Count to determine singular/plural.
        plural: Custom plural form (optional).

    Returns:
        Singular or plural form based on count.
    """
    if count == 1:
        return word
    return plural or f"{word}s"


def format_table(
    headers: list[str],
    rows: list[list[Any]],
    padding: int = 2,
) -> str:
    """Format data as a simple text table.

    Args:
        headers: Column headers.
        rows: Data rows.
        padding: Space between columns.

    Returns:
        Formatted table string.
    """
    col_widths = [len(h) for h in headers]

    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(cell)))

    pad = " " * padding
    header_row = pad + pad.join(
        h.ljust(w) for h, w in zip(headers, col_widths)
    )

    separator = pad + pad.join("-" * w for w in col_widths)

    data_rows = []
    for row in rows:
        data_rows.append(
            pad
            + pad.join(str(cell).ljust(w) for cell, w in zip(row, col_widths))
        )

    return "\n".join([header_row, separator] + data_rows)


def highlight_text(
    text: str,
    pattern: str,
    prefix: str = "[",
    suffix: str = "]",
) -> str:
    """Highlight pattern matches in text.

    Args:
        text: Text to search in.
        pattern: Pattern to highlight.
        prefix: String to prepend to matches.
        suffix: String to append to matches.

    Returns:
        Text with highlighted matches.
    """
    if not pattern:
        return text

    escaped = re.escape(pattern)
    return re.sub(
        f"({escaped})",
        f"{prefix}\\1{suffix}",
        text,
        flags=re.IGNORECASE,
    )


def extract_code_blocks(text: str) -> list[tuple[str, str]]:
    """Extract code blocks from markdown text.

    Args:
        text: Markdown text containing code blocks.

    Returns:
        List of (language, code) tuples.
    """
    pattern = r"```(\w*)\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches


def remove_extra_whitespace(text: str) -> str:
    """Remove extra whitespace from text.

    Args:
        text: Text to clean.

    Returns:
        Text with extra whitespace removed.
    """
    lines = text.split("\n")
    lines = [line.strip() for line in lines]
    lines = [line for line in lines if line]
    return "\n".join(lines)


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text.

    Args:
        text: Text to normalize.

    Returns:
        Text with normalized whitespace (single spaces between words).
    """
    return " ".join(text.split())