"""JSON utilities for Claude Code Python."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from typing import Any


def parse_json(text: str, default: Any = None) -> Any:
    """Parse JSON text, returning default on failure.

    Args:
        text: JSON string to parse.
        default: Value to return if parsing fails.

    Returns:
        Parsed JSON object, or default if invalid.
    """
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_parse(text: str) -> tuple[bool, Any]:
    """Parse JSON safely, returning (success, result).

    Args:
        text: JSON string to parse.

    Returns:
        Tuple of (success, parsed_result_or_error_message).
    """
    try:
        return True, json.loads(text)
    except json.JSONDecodeError as e:
        return False, str(e)


def stringify_json(
    obj: Any,
    indent: int | None = None,
    sort_keys: bool = False,
    default: Callable[[Any], Any] | None = None,
) -> str:
    """Stringify an object to JSON.

    Args:
        obj: Object to serialize.
        indent: Indentation level for pretty printing.
        sort_keys: Whether to sort dictionary keys.
        default: Custom serializer function for unsupported types.

    Returns:
        JSON string representation.
    """
    return json.dumps(
        obj,
        indent=indent,
        sort_keys=sort_keys,
        default=default,
        ensure_ascii=False,
    )


def pretty_json(obj: Any, sort_keys: bool = True) -> str:
    """Format an object as pretty JSON.

    Args:
        obj: Object to format.
        sort_keys: Whether to sort dictionary keys.

    Returns:
        Pretty-printed JSON string.
    """
    return json.dumps(obj, indent=2, sort_keys=sort_keys, ensure_ascii=False)


def is_json(text: str) -> bool:
    """Check if text is valid JSON.

    Args:
        text: String to validate.

    Returns:
        True if the string is valid JSON.
    """
    try:
        json.loads(text)
        return True
    except (json.JSONDecodeError, TypeError):
        return False


def merge_json(base: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Merge two JSON objects (deep merge).

    Args:
        base: Base dictionary to merge into.
        updates: Updates to apply.

    Returns:
        Merged dictionary.
    """
    result = base.copy()

    for key, value in updates.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = merge_json(result[key], value)
        else:
            result[key] = value

    return result


def get_json_path(obj: Any, path: str, default: Any = None) -> Any:
    """Get a value from nested JSON using dot notation.

    Args:
        obj: Dictionary or list to traverse.
        path: Dot-separated path (e.g., "foo.bar.baz" or "items[0].name").
        default: Default value if path doesn't exist.

    Returns:
        The value at the path, or default if not found.
    """
    keys = re.split(r"\.|\[|\]", path)
    keys = [k for k in keys if k]

    current = obj

    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        elif isinstance(current, list):
            try:
                index = int(key)
                current = current[index] if 0 <= index < len(current) else None
            except ValueError:
                return default
        else:
            return default

        if current is None:
            return default

    return current


def set_json_path(obj: dict[str, Any], path: str, value: Any) -> dict[str, Any]:
    """Set a value in nested JSON using dot notation.

    Args:
        obj: Dictionary to modify.
        path: Dot-separated path (e.g., "foo.bar.baz").
        value: Value to set.

    Returns:
        The modified dictionary.
    """
    keys = re.split(r"\.|\[|\]", path)
    keys = [k for k in keys if k]

    current = obj

    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]

    current[keys[-1]] = value
    return obj


def flatten_json(obj: dict[str, Any], separator: str = ".") -> dict[str, Any]:
    """Flatten a nested JSON object.

    Args:
        obj: Nested dictionary to flatten.
        separator: Separator to use in keys.

    Returns:
        Flattened dictionary with dot-notation keys.
    """
    result: dict[str, Any] = {}

    def _flatten(current: Any, prefix: str = "") -> None:
        if isinstance(current, dict):
            for key, value in current.items():
                new_key = f"{prefix}{separator}{key}" if prefix else key
                _flatten(value, new_key)
        elif isinstance(current, list):
            for i, item in enumerate(current):
                new_key = f"{prefix}[{i}]"
                _flatten(item, new_key)
        else:
            result[prefix] = current

    _flatten(obj)
    return result


def unflatten_json(obj: dict[str, Any], separator: str = ".") -> dict[str, Any]:
    """Unflatten a JSON object.

    Args:
        obj: Flattened dictionary with dot-notation keys.
        separator: Separator used in keys.

    Returns:
        Nested dictionary.
    """
    result: dict[str, Any] = {}

    for key, value in obj.items():
        parts = re.split(r"[\.\[\]]+", key)
        parts = [p for p in parts if p]

        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        current[parts[-1]] = value

    return result