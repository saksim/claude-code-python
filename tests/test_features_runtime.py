"""Runtime tests for feature registry state and precedence semantics."""

from __future__ import annotations

import pytest

import claude_code.features as features_mod
from claude_code.features import Feature, FeatureRegistry


@pytest.fixture(autouse=True)
def _reset_global_registry() -> None:
    """Ensure global feature registry state does not leak across tests."""
    features_mod._global_registry = None
    yield
    features_mod._global_registry = None


def _clear_feature_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for feature in Feature:
        monkeypatch.delenv(f"FEATURE_{feature.value.upper()}", raising=False)
    monkeypatch.delenv("FEATURE_EXPERIMENT_X", raising=False)


def test_enable_disable_does_not_mutate_frozen_dataclass(monkeypatch):
    _clear_feature_env(monkeypatch)
    registry = FeatureRegistry()

    registry.enable(Feature.DAEMON)
    assert registry.is_enabled(Feature.DAEMON) is True

    registry.disable(Feature.DAEMON)
    assert registry.is_enabled(Feature.DAEMON) is False


def test_env_fallback_is_dynamic_when_no_runtime_override(monkeypatch):
    _clear_feature_env(monkeypatch)
    monkeypatch.setenv("FEATURE_DAEMON", "1")
    registry = FeatureRegistry()
    assert registry.is_enabled(Feature.DAEMON) is True

    monkeypatch.setenv("FEATURE_DAEMON", "0")
    assert registry.is_enabled(Feature.DAEMON) is False


def test_runtime_override_takes_precedence_over_env(monkeypatch):
    _clear_feature_env(monkeypatch)
    monkeypatch.setenv("FEATURE_REMOTE", "1")
    registry = FeatureRegistry()
    assert registry.is_enabled(Feature.REMOTE) is True

    registry.disable(Feature.REMOTE)
    assert registry.is_enabled(Feature.REMOTE) is False


def test_get_all_configs_reports_runtime_env_default_sources(monkeypatch):
    _clear_feature_env(monkeypatch)
    registry = FeatureRegistry()

    default_snapshot = registry.get_all_configs()["buddy"]
    assert default_snapshot["source"] == "default"
    assert default_snapshot["enabled"] is False

    monkeypatch.setenv("FEATURE_BUDDY", "1")
    env_snapshot = registry.get_all_configs()["buddy"]
    assert env_snapshot["source"] == "env"
    assert env_snapshot["enabled"] is True

    registry.disable(Feature.BUDDY)
    runtime_snapshot = registry.get_all_configs()["buddy"]
    assert runtime_snapshot["source"] == "runtime"
    assert runtime_snapshot["enabled"] is False


def test_global_registry_state_is_consistent_across_get_calls(monkeypatch):
    _clear_feature_env(monkeypatch)
    first = features_mod.get_feature_registry()
    second = features_mod.get_feature_registry()

    assert first is second
    first.enable(Feature.MCP_OAUTH)
    assert second.is_enabled(Feature.MCP_OAUTH) is True


def test_unknown_feature_helper_uses_boolean_env_parsing(monkeypatch):
    _clear_feature_env(monkeypatch)
    monkeypatch.setenv("FEATURE_EXPERIMENT_X", "true")
    assert features_mod.feature("experiment_x") is True

    monkeypatch.setenv("FEATURE_EXPERIMENT_X", "off")
    assert features_mod.feature("experiment_x") is False
