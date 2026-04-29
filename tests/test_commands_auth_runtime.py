"""Runtime tests for auth commands and config/env key resolution."""

from __future__ import annotations

import io
import os
from types import SimpleNamespace

import pytest
from rich.console import Console

import claude_code.commands.auth as auth_mod
from claude_code.commands.base import CommandContext


def _context(tmp_path) -> CommandContext:
    return CommandContext(
        working_directory=str(tmp_path),
        console=Console(file=io.StringIO(), force_terminal=False, width=120),
        engine=None,
        session=None,
        config=None,
    )


def _clear_auth_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "CLAUDE_API_PROVIDER",
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "AZURE_OPENAI_API_KEY",
    ):
        monkeypatch.delenv(key, raising=False)


@pytest.mark.asyncio
async def test_auth_status_prefers_env_key_over_config_key(monkeypatch, tmp_path):
    _clear_auth_env(monkeypatch)
    config = SimpleNamespace(api_provider="anthropic", api_key="sk-ant-config-0000")
    monkeypatch.setattr(auth_mod, "get_config", lambda: config)
    monkeypatch.setattr(auth_mod, "save_config", lambda: None)
    monkeypatch.setenv("CLAUDE_API_PROVIDER", "anthropic")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-9999")

    result = await auth_mod.AuthStatusCommand().execute("", _context(tmp_path))

    assert result.success
    assert "Status: Logged in" in str(result.content)
    assert "Source: environment variable" in str(result.content)
    assert "sk-ant-env-9999" not in str(result.content)
    assert "...9999" in str(result.content)


@pytest.mark.asyncio
async def test_auth_status_uses_config_key_for_matching_openai_family_provider(monkeypatch, tmp_path):
    _clear_auth_env(monkeypatch)
    config = SimpleNamespace(api_provider="openai", api_key="sk-openai-config-1234")
    monkeypatch.setattr(auth_mod, "get_config", lambda: config)
    monkeypatch.setattr(auth_mod, "save_config", lambda: None)
    monkeypatch.setenv("CLAUDE_API_PROVIDER", "vllm")

    result = await auth_mod.AuthStatusCommand().execute("", _context(tmp_path))

    assert result.success
    assert "Provider: vllm" in str(result.content)
    assert "Source: config file" in str(result.content)
    assert "sk-openai-config-1234" not in str(result.content)
    assert "...1234" in str(result.content)


@pytest.mark.asyncio
async def test_auth_status_ignores_mismatched_config_key_provider(monkeypatch, tmp_path):
    _clear_auth_env(monkeypatch)
    config = SimpleNamespace(api_provider="anthropic", api_key="sk-ant-config-2222")
    monkeypatch.setattr(auth_mod, "get_config", lambda: config)
    monkeypatch.setattr(auth_mod, "save_config", lambda: None)
    monkeypatch.setenv("CLAUDE_API_PROVIDER", "openai")

    result = await auth_mod.AuthStatusCommand().execute("", _context(tmp_path))

    assert result.success
    assert "Status: Not logged in" in str(result.content)
    assert "Expected Key: OPENAI_API_KEY" in str(result.content)


@pytest.mark.asyncio
async def test_login_command_reports_provider_specific_env_var(monkeypatch, tmp_path):
    _clear_auth_env(monkeypatch)
    config = SimpleNamespace(api_provider="openai", api_key=None)
    monkeypatch.setattr(auth_mod, "get_config", lambda: config)
    monkeypatch.setattr(auth_mod, "save_config", lambda: None)
    monkeypatch.setenv("CLAUDE_API_PROVIDER", "openai")

    result = await auth_mod.LoginCommand().execute("", _context(tmp_path))

    assert result.success
    assert "Active provider: openai" in str(result.content)
    assert "OPENAI_API_KEY" in str(result.content)


@pytest.mark.asyncio
async def test_logout_clears_runtime_env_and_persisted_config_key(monkeypatch, tmp_path):
    _clear_auth_env(monkeypatch)
    config = SimpleNamespace(api_provider="anthropic", api_key="sk-ant-config-4444")
    save_called = {"value": False}

    def _save() -> None:
        save_called["value"] = True

    monkeypatch.setattr(auth_mod, "get_config", lambda: config)
    monkeypatch.setattr(auth_mod, "save_config", _save)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env-3333")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-env-3333")

    result = await auth_mod.LogoutCommand().execute("", _context(tmp_path))

    assert result.success
    assert "Logged out successfully." in str(result.content)
    assert "env:ANTHROPIC_API_KEY" in str(result.content)
    assert "env:OPENAI_API_KEY" in str(result.content)
    assert "config:api_key" in str(result.content)
    assert config.api_key is None
    assert save_called["value"] is True
    assert os.getenv("ANTHROPIC_API_KEY") is None
    assert os.getenv("OPENAI_API_KEY") is None


@pytest.mark.asyncio
async def test_auth_status_for_credential_based_provider(monkeypatch, tmp_path):
    _clear_auth_env(monkeypatch)
    config = SimpleNamespace(api_provider="bedrock", api_key=None)
    monkeypatch.setattr(auth_mod, "get_config", lambda: config)
    monkeypatch.setattr(auth_mod, "save_config", lambda: None)
    monkeypatch.setenv("CLAUDE_API_PROVIDER", "bedrock")

    result = await auth_mod.AuthStatusCommand().execute("", _context(tmp_path))

    assert result.success
    assert "Status: Credential-based" in str(result.content)
    assert "Provider: bedrock" in str(result.content)
    assert "API Key: not required" in str(result.content)
