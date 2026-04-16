"""Performance smoke tests.

These tests are intentionally lightweight and deterministic. They are used as
guardrails to catch obvious regressions in hot paths without external API calls.
"""

from __future__ import annotations

import asyncio
import statistics
import time
from pathlib import Path

import pytest


class _FakeStreamEvent:
    def __init__(self, event_type: str, content: dict | None = None) -> None:
        self.type = event_type
        self.content = content
        self.usage = None
        self.error = None


class _FakeAPIClient:
    async def create_message_streaming(self, messages, options):
        yield _FakeStreamEvent("text", {"text": "ok"})
        yield _FakeStreamEvent("message", {"content": [{"type": "text", "text": "ok"}]})

    async def create_message(self, messages, options):
        class _Response:
            content = [{"type": "text", "text": "ok"}]

        return _Response()


@pytest.mark.perf
def test_read_only_syntax_scan_smoke():
    root = Path("claude_code")
    errors = []
    for path in root.rglob("*.py"):
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            errors.append((str(path), exc.lineno, exc.msg))
    assert errors == []


@pytest.mark.perf
@pytest.mark.asyncio
async def test_query_engine_stub_latency_smoke():
    from claude_code.engine.query import QueryConfig, QueryEngine
    from claude_code.tools.registry import ToolRegistry

    engine = QueryEngine(
        api_client=_FakeAPIClient(),
        config=QueryConfig(),
        tool_registry=ToolRegistry(),
    )

    durations = []
    for i in range(5):
        start = time.perf_counter()
        async for _ in engine.query(f"smoke-{i}"):
            pass
        durations.append((time.perf_counter() - start) * 1000.0)
        engine.clear()

    # Very relaxed guardrail to catch catastrophic regressions only.
    assert statistics.fmean(durations) < 500.0

