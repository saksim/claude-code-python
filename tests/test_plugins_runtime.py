"""Runtime tests for local plugin loading."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from claude_code.plugins import create_plugin_manager


def _safe_rmtree(path: Path) -> None:
    """Best-effort recursive delete for temp test directories."""
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)


def _cleanup_plugin_temp_root(root: Path) -> None:
    """Remove plugin_* temp children under tests/.tmp_plugins."""
    if not root.exists():
        return
    for child in root.iterdir():
        if child.is_dir() and child.name.startswith("plugin_"):
            _safe_rmtree(child)


@pytest.fixture
def plugin_temp_root() -> Path:
    """Workspace-scoped temp root used by plugin runtime tests."""
    root = Path("tests") / ".tmp_plugins"
    root.mkdir(parents=True, exist_ok=True)
    _cleanup_plugin_temp_root(root)
    yield root
    _cleanup_plugin_temp_root(root)
    if root.exists() and not any(root.iterdir()):
        root.rmdir()


@pytest.fixture
def plugin_case_factory(plugin_temp_root: Path):
    """Factory fixture that tracks plugin temp dirs and enforces teardown cleanup."""
    created: list[Path] = []

    def _create() -> Path:
        case_dir = plugin_temp_root / f"plugin_{uuid.uuid4().hex}"
        case_dir.mkdir(parents=True, exist_ok=True)
        created.append(case_dir)
        return case_dir

    yield _create

    for case_dir in created:
        _safe_rmtree(case_dir)
    for case_dir in created:
        assert not case_dir.exists()


@pytest.mark.asyncio
async def test_local_plugin_loader_instantiates_plugin_entrypoint(plugin_case_factory):
    base = plugin_case_factory()

    (base / "plugin.json").write_text(
        json.dumps(
            {
                "id": "local-demo",
                "name": "Local Demo",
                "version": "0.1.0",
                "description": "runtime test plugin",
                "entry": "plugin.py",
            }
        ),
        encoding="utf-8",
    )
    (base / "plugin.py").write_text(
        "\n".join(
            [
                "class DemoPlugin:",
                "    def get_tools(self):",
                "        return ['tool-a']",
                "    def get_commands(self):",
                "        return ['cmd-a']",
                "    def get_hooks(self):",
                "        return {'event.a': [lambda payload: payload]}",
                "",
                "def get_plugin():",
                "    return DemoPlugin()",
            ]
        ),
        encoding="utf-8",
    )

    manager = create_plugin_manager()
    plugin = await manager.load_plugin(
        "local-demo",
        {
            "id": "local-demo",
            "type": "local",
            "path": str(base),
        },
    )

    assert plugin is not None
    assert plugin.instance is not None
    assert manager.get_all_tools() == ["tool-a"]
    assert manager.get_all_commands() == ["cmd-a"]
    assert "event.a" in manager.get_all_hooks()


def test_plugin_temp_cleanup_is_idempotent(plugin_temp_root: Path):
    stale_one = plugin_temp_root / "plugin_stale_one"
    stale_two = plugin_temp_root / "plugin_stale_two"
    stale_one.mkdir(parents=True, exist_ok=True)
    stale_two.mkdir(parents=True, exist_ok=True)
    (stale_one / "marker.txt").write_text("x", encoding="utf-8")
    (stale_two / "marker.txt").write_text("y", encoding="utf-8")

    _cleanup_plugin_temp_root(plugin_temp_root)
    _cleanup_plugin_temp_root(plugin_temp_root)

    leftovers = [path for path in plugin_temp_root.glob("plugin_*") if path.is_dir()]
    assert leftovers == []
