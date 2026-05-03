"""
Claude Code Python - Feature Flag System
Runtime feature toggles inspired by TS version
"""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from typing import Callable, Optional
from enum import Enum


class Feature(Enum):
    """Feature flags."""
    BUDDY = "buddy"
    FORK_SUBAGENT = "fork_subagent"
    PROACTIVE = "proactive"
    KAIROS = "kairos"
    VOICE_MODE = "voice_mode"
    DAEMON = "daemon"
    REMOTE = "remote"
    MCP_OAUTH = "mcp_oauth"
    PLUGINS = "plugins"
    ADVANCED_ORCHESTRATION = "advanced_orchestration"
    ENHANCED_HOOKS = "enhanced_hooks"


@dataclass(frozen=True, slots=True)
class FeatureConfig:
    """Feature configuration."""
    name: Feature
    enabled: bool = False
    env_var: str = ""
    description: str = ""
    default_value: bool = False


class FeatureRegistry:
    """Registry for feature flags."""
    
    def __init__(self):
        self._features: dict[Feature, FeatureConfig] = {}
        self._feature_checks: dict[Feature, Callable[[], bool]] = {}
        self._explicit_overrides: set[Feature] = set()
        self._initialize_defaults()

    @staticmethod
    def _env_enabled(env_var: str) -> bool:
        """Resolve boolean value from environment variable."""
        value = os.environ.get(env_var)
        if value is None:
            return False
        return str(value).strip().lower() in {"1", "true", "yes", "on"}
    
    def _initialize_defaults(self) -> None:
        """Initialize default feature configurations."""
        defaults = [
            (Feature.BUDDY, "FEATURE_BUDDY", "Buddy assistant feature"),
            (Feature.FORK_SUBAGENT, "FEATURE_FORK_SUBAGENT", "Fork subagent feature"),
            (Feature.PROACTIVE, "FEATURE_PROACTIVE", "Proactive suggestions"),
            (Feature.KAIROS, "FEATURE_KAIROS", "Kairos time tracking"),
            (Feature.VOICE_MODE, "FEATURE_VOICE_MODE", "Voice mode"),
            (Feature.DAEMON, "FEATURE_DAEMON", "Daemon mode"),
            (Feature.REMOTE, "FEATURE_REMOTE", "Remote sessions"),
            (Feature.MCP_OAUTH, "FEATURE_MCP_OAUTH", "MCP OAuth support"),
            (Feature.PLUGINS, "FEATURE_PLUGINS", "Plugin system"),
            (Feature.ADVANCED_ORCHESTRATION, "FEATURE_ADVANCED_ORCHESTRATION", "Advanced tool orchestration"),
            (Feature.ENHANCED_HOOKS, "FEATURE_ENHANCED_HOOKS", "Enhanced hooks pipeline"),
        ]
        
        for feature, env_var, description in defaults:
            default_value = self._env_enabled(env_var)
            self._features[feature] = FeatureConfig(
                name=feature,
                env_var=env_var,
                description=description,
                default_value=default_value,
                enabled=default_value,
            )
    
    def register_check(self, feature: Feature, check: Callable[[], bool]) -> None:
        """Register a custom check function for a feature."""
        self._feature_checks[feature] = check
    
    def is_enabled(self, feature: Feature) -> bool:
        """Check if a feature is enabled."""
        if feature in self._feature_checks:
            return self._feature_checks[feature]()
        
        config = self._features.get(feature)
        if config is None:
            env_var = f"FEATURE_{feature.value.upper()}"
            return self._env_enabled(env_var)

        if feature in self._explicit_overrides:
            return config.enabled
        if config.env_var in os.environ:
            return self._env_enabled(config.env_var)
        return config.default_value
    
    def enable(self, feature: Feature) -> None:
        """Enable a feature."""
        if feature in self._features:
            self._features[feature] = replace(self._features[feature], enabled=True)
            self._explicit_overrides.add(feature)
    
    def disable(self, feature: Feature) -> None:
        """Disable a feature."""
        if feature in self._features:
            self._features[feature] = replace(self._features[feature], enabled=False)
            self._explicit_overrides.add(feature)

    def _resolve_source(self, feature: Feature) -> str:
        """Resolve the active source for a feature value."""
        if feature in self._feature_checks:
            return "check"
        if feature in self._explicit_overrides:
            return "runtime"
        config = self._features[feature]
        if config.env_var in os.environ:
            return "env"
        return "default"
    
    def get_enabled_features(self) -> list[Feature]:
        """Get list of enabled features."""
        return [f for f in Feature if self.is_enabled(f)]
    
    def get_all_configs(self) -> dict[str, dict]:
        """Get all feature configurations."""
        return {
            f.value: {
                "enabled": self.is_enabled(f),
                "env_var": config.env_var,
                "description": config.description,
                "default_value": config.default_value,
                "source": self._resolve_source(f),
            }
            for f, config in self._features.items()
        }


_global_registry: Optional[FeatureRegistry] = None


def get_feature_registry() -> FeatureRegistry:
    """Get the global feature registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = FeatureRegistry()
    return _global_registry


def feature(name: str) -> bool:
    """Check if a feature is enabled by name (for compatibility with TS code patterns)."""
    try:
        feature_enum = Feature(name.lower())
        return get_feature_registry().is_enabled(feature_enum)
    except ValueError:
        env_var = f"FEATURE_{name.upper()}"
        return FeatureRegistry._env_enabled(env_var)


__all__ = [
    "Feature",
    "FeatureConfig",
    "FeatureRegistry",
    "get_feature_registry",
    "feature",
]
