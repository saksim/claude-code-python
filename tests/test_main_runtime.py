"""Runtime tests for main entry helpers."""

from __future__ import annotations

import pytest

import claude_code.main as main_mod


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
    monkeypatch.setattr(main_mod, "create_engine", lambda model=None: _FakeEngine())

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
