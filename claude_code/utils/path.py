"""Path utilities for Claude Code Python."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

if os.name == "nt":
    import ctypes


def expand_path(path: str | Path) -> Path:
    """Expand a path, resolving ~ and environment variables.

    Args:
        path: Path to expand.

    Returns:
        Expanded Path object.
    """
    return Path(os.path.expandvars(os.path.expanduser(str(path))))


def normalize_path(path: str | Path) -> str:
    """Normalize a path to use forward slashes.

    Args:
        path: Path to normalize.

    Returns:
        Normalized path string with forward slashes.
    """
    return Path(path).as_posix()


def is_absolute(path: str | Path) -> bool:
    """Check if a path is absolute.

    Args:
        path: Path to check.

    Returns:
        True if the path is absolute.
    """
    return Path(path).is_absolute()


def resolve_path(path: str | Path, base_dir: str | Path | None = None) -> str:
    """Resolve a path relative to a base directory.

    Args:
        path: The path to resolve.
        base_dir: Base directory to resolve from (defaults to cwd).

    Returns:
        Normalized absolute path as string.
    """
    path_obj = Path(path)
    if path_obj.is_absolute():
        return normalize_path(path_obj)

    base = Path(base_dir) if base_dir else Path.cwd()
    return normalize_path((base / path_obj).resolve())


def to_relative_path(path: str | Path, base_dir: str | Path | None = None) -> str:
    """Convert an absolute path to a relative path.

    Args:
        path: Absolute path to convert.
        base_dir: Base directory (defaults to cwd).

    Returns:
        Relative path string, or original path if not possible.
    """
    path_obj = Path(path).resolve()
    base = (Path(base_dir) if base_dir else Path.cwd()).resolve()

    try:
        return str(path_obj.relative_to(base))
    except ValueError:
        return str(path_obj)


def get_extension(path: str | Path) -> str:
    """Get the file extension from a path (lowercase, with dot).

    Args:
        path: Path to extract extension from.

    Returns:
        Lowercase file extension including the dot.
    """
    return Path(path).suffix.lower()


def get_filename(path: str | Path) -> str:
    """Get the filename from a path.

    Args:
        path: Path to extract filename from.

    Returns:
        The filename without directory.
    """
    return Path(path).name


def get_dirname(path: str | Path) -> str:
    """Get the directory name from a path.

    Args:
        path: Path to extract directory from.

    Returns:
        The parent directory as a string.
    """
    return str(Path(path).parent)


def join_paths(*parts: str | Path) -> str:
    """Join path parts and normalize the result.

    Args:
        parts: Path components to join.

    Returns:
        Normalized path string.
    """
    return normalize_path(Path(*parts))


def ensure_dir_exists(path: str | Path) -> None:
    """Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory.
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def is_subpath(path: str | Path, parent: str | Path) -> bool:
    """Check if path is a subpath of parent.

    Args:
        path: Path to check.
        parent: Potential parent path.

    Returns:
        True if path is under parent directory.
    """
    path_resolved = Path(path).resolve()
    parent_resolved = Path(parent).resolve()

    try:
        path_resolved.relative_to(parent_resolved)
        return True
    except ValueError:
        return path_resolved == parent_resolved


def get_project_root() -> str:
    """Get the project root (git repository root or cwd).

    Returns:
        Path to the project root directory.
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except FileNotFoundError:
        pass

    return os.getcwd()


def find_file_upwards(
    filename: str,
    start_dir: str | Path | None = None,
) -> str | None:
    """Find a file by searching upward from start_dir.

    Args:
        filename: Name of the file to find.
        start_dir: Directory to start searching from (defaults to cwd).

    Returns:
        Full path to the file if found, None otherwise.
    """
    current = Path(start_dir or os.getcwd()).resolve()

    while True:
        candidate = current / filename
        if candidate.is_file():
            return str(candidate)

        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def is_hidden(path: str | Path) -> bool:
    """Check if a file or directory is hidden.

    Args:
        path: Path to check.

    Returns:
        True if the path is hidden.
    """
    name = Path(path).name
    if name.startswith("."):
        return True

    if os.name == "nt":
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(Path(path).resolve()))
            return attrs != -1 and bool(attrs & 2)
        except Exception:
            pass

    return False