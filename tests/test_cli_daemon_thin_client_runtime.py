"""Runtime tests for P1-06 CLI daemon thin-client migration helpers."""

from __future__ import annotations

from argparse import Namespace

import claude_code.main as main_mod


def test_resolve_daemon_client_mode_defaults_to_host_port_when_enabled():
    args = Namespace(
        daemon_client=True,
        daemon_url=None,
        daemon_host="127.0.0.8",
        daemon_port=9001,
        daemon_timeout=12.5,
        daemon_required=False,
    )

    mode = main_mod._resolve_daemon_client_mode(args)

    assert mode.enabled is True
    assert mode.base_url == "http://127.0.0.8:9001"
    assert mode.timeout_seconds == 12.5
    assert mode.required is False


def test_resolve_daemon_client_mode_prefers_explicit_url():
    args = Namespace(
        daemon_client=False,
        daemon_url="http://127.0.0.77:9900",
        daemon_host="127.0.0.1",
        daemon_port=8787,
        daemon_timeout=30.0,
        daemon_required=True,
    )

    mode = main_mod._resolve_daemon_client_mode(args)

    assert mode.enabled is True
    assert mode.base_url == "http://127.0.0.77:9900"
    assert mode.required is True

