"""Runtime regression tests for the default tool registry."""

from __future__ import annotations

import claude_code.tools.registry as registry_mod


def test_create_default_registry_is_module_lazy(monkeypatch):
    imported_modules: list[str] = []
    real_import = registry_mod.importlib.import_module

    def _tracked_import(module_name: str, package: str | None = None):
        imported_modules.append(module_name)
        return real_import(module_name, package)

    monkeypatch.setattr(registry_mod.importlib, "import_module", _tracked_import)

    registry = registry_mod.create_default_registry()
    assert imported_modules == []

    bash_tool = registry.get("bash")
    assert bash_tool is not None
    assert bash_tool.name == "bash"
    assert "claude_code.tools.builtin.bash" in imported_modules


def test_create_default_registry_includes_expected_tool_names():
    registry = registry_mod.create_default_registry()
    names = registry.get_names()

    assert "bash" in names
    assert "cron_create" in names
    assert "lsp" in names


def test_default_registry_resolves_lsp_tool():
    registry = registry_mod.create_default_registry()
    lsp_tool = registry.get("lsp")

    assert lsp_tool is not None
    assert lsp_tool.name == "lsp"
