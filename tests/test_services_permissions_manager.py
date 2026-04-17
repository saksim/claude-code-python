"""Tests for services.permissions_manager compatibility behavior."""

from __future__ import annotations

from claude_code.permissions import PermissionMode
import claude_code.services.permissions_manager as pm_mod


def test_get_permissions_manager_prefers_claude_permission_mode(monkeypatch):
    monkeypatch.setenv("CLAUDE_PERMISSION_MODE", "plan")
    monkeypatch.delenv("CLAUDE_PERMISSIONS", raising=False)
    pm_mod._permissions_manager = None

    manager = pm_mod.get_permissions_manager()

    assert manager.mode == PermissionMode.PLAN
    pm_mod._permissions_manager = None

