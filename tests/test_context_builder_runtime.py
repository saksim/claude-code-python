"""Runtime tests for ContextBuilder/ClaudeMdLoader behavior."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from claude_code.engine.context import ClaudeMdLoader


def test_claude_md_loader_includes_parent_claude_md():
    base = Path("tests") / ".tmp_context" / f"case_{uuid.uuid4().hex}"
    root = base / "root"
    nested = root / "sub" / "deeper"
    nested.mkdir(parents=True, exist_ok=True)
    try:
        (root / "CLAUDE.md").write_text("root-level instructions", encoding="utf-8")
        loader = ClaudeMdLoader(nested)
        files = loader.find_claude_md_files()

        assert files
        content = loader.load_content()
        assert content is not None
        assert "root-level instructions" in content
    finally:
        shutil.rmtree(base, ignore_errors=True)

