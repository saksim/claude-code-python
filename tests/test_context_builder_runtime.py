"""Runtime tests for ContextBuilder/ClaudeMdLoader behavior."""

from __future__ import annotations

import os
import shutil
import stat
import uuid
from pathlib import Path

import pytest

from claude_code.engine.context import ClaudeMdLoader, ContextBuilder


def _cleanup_tree(path: Path) -> None:
    """Best-effort recursive cleanup for Windows test temp directories."""

    def _onerror(func, value, exc_info):
        try:
            os.chmod(value, stat.S_IWRITE)
            func(value)
        except Exception:
            pass

    if path.exists():
        shutil.rmtree(path, onerror=_onerror)


def test_claude_md_loader_includes_parent_claude_md():
    base = Path("tests") / ".tmp_context" / f"case_{uuid.uuid4().hex}"
    try:
        root = base / "root"
        nested = root / "sub" / "deeper"
        nested.mkdir(parents=True, exist_ok=True)
        (root / "CLAUDE.md").write_text("root-level instructions", encoding="utf-8")
        loader = ClaudeMdLoader(nested)
        files = loader.find_claude_md_files()

        assert files
        content = loader.load_content()
        assert content is not None
        assert "root-level instructions" in content
    finally:
        _cleanup_tree(base)


def test_claude_md_loader_orders_files_from_root_to_current():
    base = Path("tests") / ".tmp_context" / f"order_{uuid.uuid4().hex}"
    try:
        root = base / "root"
        sub = root / "sub"
        nested = sub / "deep"
        nested.mkdir(parents=True, exist_ok=True)
        (root / "CLAUDE.md").write_text("root", encoding="utf-8")
        (sub / "CLAUDE.md").write_text("sub", encoding="utf-8")
        (nested / "CLAUDE.md").write_text("nested", encoding="utf-8")

        loader = ClaudeMdLoader(nested)
        files = loader.find_claude_md_files()

        assert files == [root / "CLAUDE.md", sub / "CLAUDE.md", nested / "CLAUDE.md"]

        content = loader.load_content()
        assert content is not None
        assert content.index("root") < content.index("sub") < content.index("nested")
    finally:
        _cleanup_tree(base)


def test_claude_md_loader_skips_single_unreadable_file(monkeypatch: pytest.MonkeyPatch):
    base = Path("tests") / ".tmp_context" / f"unreadable_{uuid.uuid4().hex}"
    try:
        root = base / "root"
        nested = root / "nested"
        nested.mkdir(parents=True, exist_ok=True)
        root_md = root / "CLAUDE.md"
        nested_md = nested / "CLAUDE.md"
        root_md.write_text("root text", encoding="utf-8")
        nested_md.write_text("nested text", encoding="utf-8")

        original_read_text = Path.read_text

        def _patched_read_text(self: Path, *args, **kwargs):
            if self == root_md:
                raise OSError("permission denied")
            return original_read_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", _patched_read_text)

        loader = ClaudeMdLoader(nested)
        content = loader.load_content()

        assert content is not None
        assert "nested text" in content
        assert "root text" not in content
    finally:
        _cleanup_tree(base)


def test_context_builder_user_context_keeps_session_history_memory_boundaries():
    base = Path("tests") / ".tmp_context" / f"context_{uuid.uuid4().hex}"
    try:
        base.mkdir(parents=True, exist_ok=True)
        context = ContextBuilder(base).get_user_context()

        assert "currentDate" in context
        assert "claudeMd" not in context
        assert "session" not in context
        assert "history" not in context
        assert "memory" not in context
    finally:
        _cleanup_tree(base)


def test_context_builder_includes_claude_md_without_injecting_history_or_memory():
    base = Path("tests") / ".tmp_context" / f"context_md_{uuid.uuid4().hex}"
    try:
        base.mkdir(parents=True, exist_ok=True)
        (base / "CLAUDE.md").write_text("project instructions", encoding="utf-8")
        context = ContextBuilder(base).get_user_context()

        assert "claudeMd" in context
        assert "project instructions" in str(context["claudeMd"])
        assert "history" not in context
        assert "memory" not in context
    finally:
        _cleanup_tree(base)
