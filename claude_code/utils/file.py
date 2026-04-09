"""File utilities for Claude Code Python.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Async versions for I/O operations
- Frozen dataclass with __slots__ for memory optimization
- Context managers for resource management
"""

from __future__ import annotations

import hashlib
import mimetypes
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

DEFAULT_ENCODING = "utf-8"
CHUNK_SIZE = 8192
SAMPLE_SIZE = 4096


def read_file(path: str | Path, encoding: str = DEFAULT_ENCODING) -> str:
    """Read a file and return its contents.

    Args:
        path: Path to the file.
        encoding: Character encoding to use.

    Returns:
        The file contents as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    with open(path, "r", encoding=encoding, errors="replace") as f:
        return f.read()


async def read_file_async(path: str | Path, encoding: str = DEFAULT_ENCODING) -> str:
    """Read a file asynchronously and return its contents.

    Args:
        path: Path to the file.
        encoding: Character encoding to use.

    Returns:
        The file contents as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    import aiofiles
    async with aiofiles.open(path, "r", encoding=encoding, errors="replace") as f:
        return await f.read()


def write_file(path: str | Path, content: str, encoding: str = DEFAULT_ENCODING) -> None:
    """Write content to a file.

    Args:
        path: Path to the file.
        content: Content to write.
        encoding: Character encoding to use.

    Raises:
        IOError: If the file cannot be written.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding=encoding) as f:
        f.write(content)


async def write_file_async(path: str | Path, content: str, encoding: str = DEFAULT_ENCODING) -> None:
    """Write content to a file asynchronously.

    Args:
        path: Path to the file.
        content: Content to write.
        encoding: Character encoding to use.

    Raises:
        IOError: If the file cannot be written.
    """
    import aiofiles
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w", encoding=encoding) as f:
        await f.write(content)


def read_file_lines(path: str | Path, encoding: str = DEFAULT_ENCODING) -> list[str]:
    """Read a file and return its lines.

    Args:
        path: Path to the file.
        encoding: Character encoding to use.

    Returns:
        List of lines from the file.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    with open(path, "r", encoding=encoding, errors="replace") as f:
        return f.readlines()


def get_file_size(path: str | Path) -> int:
    """Get the size of a file in bytes.

    Args:
        path: Path to the file.

    Returns:
        File size in bytes.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    return Path(path).stat().st_size


def get_file_mtime(path: str | Path) -> float:
    """Get the modification time of a file.

    Args:
        path: Path to the file.

    Returns:
        Modification timestamp (seconds since epoch).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    return Path(path).stat().st_mtime


def file_exists(path: str | Path) -> bool:
    """Check if a file exists.

    Args:
        path: Path to check.

    Returns:
        True if the path is a file, False otherwise.
    """
    return Path(path).is_file()


def dir_exists(path: str | Path) -> bool:
    """Check if a directory exists.

    Args:
        path: Path to check.

    Returns:
        True if the path is a directory, False otherwise.
    """
    return Path(path).is_dir()


def compute_file_hash(path: str | Path, algorithm: str = "sha256") -> str:
    """Compute a hash of a file's contents.

    Args:
        path: Path to the file.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal digest of the file contents.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    hash_func = hashlib.new(algorithm)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def compute_content_hash(content: str, algorithm: str = "sha256") -> str:
    """Compute a hash of string content.

    Args:
        content: String content to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal digest of the content.
    """
    return hashlib.new(algorithm, content.encode(DEFAULT_ENCODING)).hexdigest()


def get_file_extension(path: str | Path) -> str:
    """Get the file extension (lowercase, with dot).

    Args:
        path: Path to the file.

    Returns:
        Lowercase file extension including the dot, or empty string.
    """
    return Path(path).suffix.lower()


def get_mime_type(path: str | Path) -> str:
    """Get the MIME type based on file extension.

    Args:
        path: Path to the file.

    Returns:
        MIME type string, or 'application/octet-stream' if unknown.
    """
    mime_type, _ = mimetypes.guess_type(str(path))
    return mime_type or "application/octet-stream"


def detect_line_endings(path: str | Path) -> str:
    """Detect the line ending style of a file.

    Args:
        path: Path to the file.

    Returns:
        '\r\n' for Windows, '\n' for Unix, '\r' for old Mac.
    """
    with open(path, "rb") as f:
        sample = f.read(SAMPLE_SIZE)

    if b"\r\n" in sample:
        return "\r\n"
    elif b"\n" in sample:
        return "\n"
    elif b"\r" in sample:
        return "\r"
    return "\n"


def detect_encoding(path: str | Path) -> str:
    """Detect the encoding of a file.

    Args:
        path: Path to the file.

    Returns:
        Detected encoding (defaults to 'utf-8' if detection fails).

    Raises:
        ImportError: If chardet is not installed.
    """
    import chardet

    with open(path, "rb") as f:
        raw = f.read(SAMPLE_SIZE)

    result = chardet.detect(raw)
    return result.get("encoding") or "utf-8"


def read_file_with_metadata(
    path: str | Path,
) -> tuple[str, str, str]:
    """Read a file with metadata.

    Args:
        path: Path to the file.

    Returns:
        Tuple of (content, encoding, line_endings).
    """
    encoding = detect_encoding(path)
    line_endings = detect_line_endings(path)
    content = read_file(path, encoding)
    return content, encoding, line_endings


def write_file_with_metadata(
    path: str | Path,
    content: str,
    encoding: str = DEFAULT_ENCODING,
    line_endings: str = "\n",
) -> None:
    """Write content preserving line endings.

    Args:
        path: Path to the file.
        content: Content to write.
        encoding: Character encoding to use.
        line_endings: Line ending style to use.
    """
    if line_endings != "\n":
        content = content.replace("\n", line_endings)
    write_file(path, content, encoding)


@dataclass(frozen=True, slots=True)
class FileModificationInfo:
    """Information about a file modification.

    Attributes:
        path: Path to the file.
        mtime: Modification timestamp.
        size: File size in bytes.
        hash: Optional hash of file contents.
    """

    path: str
    mtime: float
    size: int
    hash: str | None = None


def get_file_modification_info(path: str | Path) -> FileModificationInfo:
    """Get modification info for a file.

    Args:
        path: Path to the file.

    Returns:
        FileModificationInfo with current file state.
    """
    return FileModificationInfo(
        path=str(path),
        mtime=get_file_mtime(path),
        size=get_file_size(path),
        hash=compute_file_hash(path),
    )


def has_file_changed(path: str | Path, old_info: FileModificationInfo) -> bool:
    """Check if a file has changed since old_info.

    Args:
        path: Path to the file.
        old_info: Previous FileModificationInfo.

    Returns:
        True if the file has changed or no longer exists.
    """
    try:
        new_info = get_file_modification_info(path)
        return (
            new_info.mtime != old_info.mtime
            or new_info.size != old_info.size
            or new_info.hash != old_info.hash
        )
    except FileNotFoundError:
        return True


def safe_write_file(
    path: str | Path,
    content: str,
    encoding: str = DEFAULT_ENCODING,
) -> None:
    """Write a file safely using a temporary file and atomic rename.

    Args:
        path: Path to the destination file.
        content: Content to write.
        encoding: Character encoding to use.

    Raises:
        IOError: If the write fails.
    """
    path = Path(path)
    dir_path = path.parent
    if dir_path:
        dir_path.mkdir(parents=True, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")

    try:
        with open(fd, "w", encoding=encoding) as f:
            f.write(content)
        shutil.move(temp_path, path)
    except Exception:
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception:
            pass
        raise


def truncate_file(path: str | Path, max_lines: int) -> str:
    """Truncate a file to max_lines and return removed content.

    Args:
        path: Path to the file.
        max_lines: Maximum number of lines to keep.

    Returns:
        The removed content as a string.
    """
    lines = read_file_lines(path)

    if len(lines) <= max_lines:
        return ""

    kept = lines[:max_lines]
    removed = lines[max_lines:]

    write_file(path, "".join(kept))

    return "".join(removed)


__all__ = [
    "DEFAULT_ENCODING",
    "CHUNK_SIZE",
    "SAMPLE_SIZE",
    "read_file",
    "read_file_async",
    "write_file",
    "write_file_async",
    "read_file_lines",
    "get_file_size",
    "get_file_mtime",
    "file_exists",
    "dir_exists",
    "compute_file_hash",
    "compute_content_hash",
    "get_file_extension",
    "get_mime_type",
    "detect_line_endings",
    "detect_encoding",
    "read_file_with_metadata",
    "write_file_with_metadata",
    "FileModificationInfo",
    "get_file_modification_info",
    "has_file_changed",
    "safe_write_file",
    "truncate_file",
]