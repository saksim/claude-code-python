"""Runtime tests for main entry helpers."""

from __future__ import annotations

import pytest

import claude_code.main as main_mod
from claude_code.permissions import PermissionMode


class _AssistantMessage:
    def __init__(self, content):
        self.role = "assistant"
        self.content = content


class _FakeEngine:
    async def query(self, query: str):
        yield {"type": "text", "content": "stream-"}
        yield _AssistantMessage([{"type": "text", "text": "final"}])


@pytest.mark.asyncio
async def test_run_single_query_prints_stream_and_final_text(monkeypatch, capsys):
    monkeypatch.setattr(
        main_mod,
        "create_engine",
        lambda model=None, working_dir=None: _FakeEngine(),
    )

    code = await main_mod.run_single_query("hello")

    out = capsys.readouterr().out
    assert code == 0
    assert "stream-final" in out


def test_setup_api_client_openai_requires_api_key(monkeypatch):
    monkeypatch.setenv("CLAUDE_API_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    with pytest.raises(ValueError):
        main_mod.setup_api_client()


def test_setup_api_client_ollama_allows_dummy_key(monkeypatch):
    monkeypatch.setenv("CLAUDE_API_PROVIDER", "ollama")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    captured = {}

    class _FakeApiClient:
        def __init__(self, config):
            captured["config"] = config

    monkeypatch.setattr(main_mod, "APIClient", _FakeApiClient)

    client = main_mod.setup_api_client()

    assert isinstance(client, _FakeApiClient)
    assert captured["config"].provider.value == "openai"
    assert captured["config"].api_key == "dummy"
    assert captured["config"].base_url == "http://localhost:11434/v1"


def test_setup_api_client_accepts_config_provider_without_env(monkeypatch):
    monkeypatch.delenv("CLAUDE_API_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

    captured = {}

    class _FakeApiClient:
        def __init__(self, config):
            captured["config"] = config

    monkeypatch.setattr(main_mod, "APIClient", _FakeApiClient)
    config = main_mod.Config(
        api_provider="ollama",
        openai_base_url="http://localhost:11434/v1",
    )

    client = main_mod.setup_api_client(config)

    assert isinstance(client, _FakeApiClient)
    assert captured["config"].provider.value == "openai"
    assert captured["config"].api_key == "dummy"


def test_create_engine_uses_model_from_config_when_arg_missing(monkeypatch):
    captured = {}

    class _FakeQueryEngine:
        def __init__(self, api_client, config, tool_registry):
            captured["config"] = config

    cfg = main_mod.Config(
        model="claude-haiku-20240307",
        permission_mode=PermissionMode.DEFAULT,
    )

    monkeypatch.setattr(main_mod, "get_config", lambda: cfg)
    monkeypatch.setattr(main_mod, "setup_api_client", lambda app_config=None: object())
    monkeypatch.setattr(main_mod, "create_default_registry", lambda: object())
    monkeypatch.setattr(main_mod, "QueryEngine", _FakeQueryEngine)

    main_mod.create_engine()

    assert captured["config"].model == "claude-haiku-20240307"


def test_config_accepts_local_openai_compatible_providers():
    assert main_mod.Config(api_provider="ollama").api_provider == "ollama"
    assert main_mod.Config(api_provider="vllm").api_provider == "vllm"
    assert main_mod.Config(api_provider="deepseek").api_provider == "deepseek"
