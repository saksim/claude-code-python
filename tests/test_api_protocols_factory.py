"""Tests for unified adapter factory in api.protocols."""

from __future__ import annotations

import pytest

from claude_code.api.client import APIProvider, StreamEvent
from claude_code.api.protocols import (
    APIClientAdapter,
    ChatMessage,
    LLMClientFactory,
)


class _FakeAPIClient:
    def __init__(self, config):
        self.config = config

    async def create_message(self, messages, options):
        class _Resp:
            content = [{"type": "text", "text": "ok"}]
            usage = {"input_tokens": 3, "output_tokens": 5}

        return _Resp()

    async def create_message_streaming(self, messages, options):
        yield StreamEvent(type="text", content={"text": "s"})
        yield StreamEvent(type="message", content={"content": [{"type": "text", "text": "t"}]})


def test_factory_returns_unified_adapter_for_ollama(monkeypatch):
    import claude_code.api.protocols as protocols_mod

    monkeypatch.setattr(protocols_mod, "APIClient", _FakeAPIClient)

    adapter = LLMClientFactory.create(provider="ollama")
    assert isinstance(adapter, APIClientAdapter)
    assert adapter.provider == "ollama"
    assert adapter._client.config.provider == APIProvider.OPENAI
    assert adapter._client.config.base_url == "http://localhost:11434/v1"


@pytest.mark.asyncio
async def test_unified_adapter_chat_once_and_stream(monkeypatch):
    import claude_code.api.protocols as protocols_mod

    monkeypatch.setattr(protocols_mod, "APIClient", _FakeAPIClient)
    adapter = APIClientAdapter(provider="anthropic", model="x")

    text, usage = await adapter.chat_once([ChatMessage(role="user", content="hi")])
    assert text == "ok"
    assert usage.input_tokens == 3
    assert usage.output_tokens == 5
    assert usage.total_tokens == 8

    chunks = []
    async for chunk in adapter.chat([ChatMessage(role="user", content="hi")]):
        chunks.append(chunk)
    assert chunks == ["s", "t"]

