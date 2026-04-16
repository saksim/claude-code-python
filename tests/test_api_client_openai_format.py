"""Tests for OpenAI-compatible message formatting in APIClient."""

from __future__ import annotations

import json

from claude_code.api.client import APIClient, MessageParam


def _new_client_without_init() -> APIClient:
    """Create APIClient instance without running network-dependent init."""
    return object.__new__(APIClient)


def test_format_openai_messages_with_tool_use_and_tool_result_blocks():
    client = _new_client_without_init()
    messages = [
        MessageParam(
            role="assistant",
            content=[
                {"type": "text", "text": "I will call tool"},
                {"type": "tool_use", "id": "call-1", "name": "read", "input": {"path": "a.txt"}},
            ],
        ),
        MessageParam(
            role="user",
            content=[
                {"type": "tool_result", "tool_use_id": "call-1", "content": "file content"},
            ],
        ),
    ]

    formatted = APIClient._format_openai_messages(client, messages, system="sys")

    assert formatted[0] == {"role": "system", "content": "sys"}
    assert formatted[1]["role"] == "assistant"
    assert formatted[1]["tool_calls"][0]["id"] == "call-1"
    assert formatted[1]["tool_calls"][0]["function"]["name"] == "read"
    assert json.loads(formatted[1]["tool_calls"][0]["function"]["arguments"]) == {"path": "a.txt"}
    assert formatted[2] == {"role": "tool", "tool_call_id": "call-1", "content": "file content"}
    assert len(formatted) == 3

