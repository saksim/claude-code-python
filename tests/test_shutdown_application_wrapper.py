"""Tests for shutdown lifecycle compatibility wrapper."""

from __future__ import annotations

import pytest

from claude_code.services.shutdown import ShutdownApplication, ShutdownConfig


class _DummyManagerConfig:
    def __init__(self):
        self.timeout = 30.0
        self.force_after = 60.0
        self.on_shutdown = None
        self.on_cleanup = None


class _DummyManager:
    def __init__(self):
        self.config = _DummyManagerConfig()


class _FakeCanonicalApp:
    def __init__(self):
        self._shutdown_manager = _DummyManager()
        self.entered = False
        self.exited = False
        self.stopped = False

    async def __aenter__(self):
        self.entered = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.exited = True

    async def run(self):
        return None

    def stop(self):
        self.stopped = True


@pytest.mark.asyncio
async def test_shutdown_application_delegates_to_canonical_app(monkeypatch):
    import claude_code.app as app_mod

    monkeypatch.setattr(app_mod, "Application", _FakeCanonicalApp)

    called = {"shutdown": False, "cleanup": False}

    async def _on_shutdown():
        called["shutdown"] = True

    async def _on_cleanup():
        called["cleanup"] = True

    wrapper = ShutdownApplication(
        ShutdownConfig(timeout=7.0, force_after=9.0, on_shutdown=_on_shutdown, on_cleanup=_on_cleanup)
    )
    app = await wrapper.__aenter__()
    assert isinstance(app, _FakeCanonicalApp)
    assert app._shutdown_manager.config.timeout == 7.0
    assert app._shutdown_manager.config.force_after == 9.0
    assert app._shutdown_manager.config.on_shutdown is _on_shutdown
    assert app._shutdown_manager.config.on_cleanup is _on_cleanup

    await wrapper.__aexit__(None, None, None)
    assert app.exited is True

