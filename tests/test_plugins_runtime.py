"""Runtime tests for local plugin loading."""

from __future__ import annotations

import json
import shutil
import uuid
from pathlib import Path

import pytest

from claude_code.plugins import create_plugin_manager


@pytest.mark.asyncio
async def test_local_plugin_loader_instantiates_plugin_entrypoint():
    base = Path("tests") / ".tmp_plugins" / f"plugin_{uuid.uuid4().hex}"
    base.mkdir(parents=True, exist_ok=True)
    try:
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
    finally:
        shutil.rmtree(base, ignore_errors=True)

