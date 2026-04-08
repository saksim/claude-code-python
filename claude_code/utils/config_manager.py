"""Unified Configuration Management for Claude Code Python.

Provides centralized configuration with priority: env > config file > defaults.
"""

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Union


class ConfigSource(Enum):
    """Configuration source priority."""

    ENVIRONMENT = "environment"
    CONFIG_FILE = "config_file"
    DEFAULT = "default"


@dataclass
class ConfigValue:
    """Represents a configuration value with its source."""

    value: Any
    source: ConfigSource
    key: str


class ConfigManager:
    """Unified configuration manager.

    Features:
    - Environment variable support with prefix
    - Config file support (JSON, YAML)
    - Default values with validation
    - Type coercion
    - Hot-reload capability

    Priority: env > config file > defaults
    """

    def __init__(
        self,
        env_prefix: str = "CLAUDE_",
        config_file: Optional[Union[str, Path]] = None,
    ) -> None:
        """Initialize configuration manager.

        Args:
            env_prefix: Prefix for environment variables.
            config_file: Optional path to config file.
        """
        self._env_prefix = env_prefix.upper()
        self._config_file = config_file
        self._defaults: Dict[str, Any] = {}
        self._file_config: Dict[str, Any] = {}
        self._cache: Dict[str, ConfigValue] = {}

        # Load config file if provided
        if config_file:
            self._load_config_file(config_file)

    def _load_config_file(self, path: Union[str, Path]) -> None:
        """Load configuration from file."""
        path = Path(path)
        if not path.exists():
            return

        try:
            if path.suffix == ".json":
                import json

                with open(path) as f:
                    self._file_config = json.load(f)
            elif path.suffix in (".yaml", ".yml"):
                try:
                    import yaml

                    with open(path) as f:
                        self._file_config = yaml.safe_load(f) or {}
                except ImportError:
                    pass  # yaml not installed
        except Exception:
            pass  # Silently ignore config file errors

    def set_defaults(self, defaults: Dict[str, Any]) -> None:
        """Set default values.

        Args:
            defaults: Dictionary of default values.
        """
        self._defaults = defaults

    def get(
        self,
        key: str,
        default: Any = None,
        value_type: Optional[type] = None,
    ) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (supports dot notation for nested).
            default: Default value if not found.
            value_type: Optional type to coerce to.

        Returns:
            Configuration value.

        Examples:
            config.get("api_key")
            config.get("database.host", default="localhost")
            config.get("timeout", value_type=int, default=30)
        """
        # Check cache
        if key in self._cache:
            return self._cache[key].value

        # 1. Check environment variable (highest priority)
        env_key = self._get_env_key(key)
        if env_key in os.environ:
            value = os.environ[env_key]
            value = self._coerce_value(value, value_type)
            self._cache[key] = ConfigValue(value, ConfigSource.ENVIRONMENT, key)
            return value

        # 2. Check config file
        file_value = self._get_nested(self._file_config, key)
        if file_value is not None:
            file_value = self._coerce_value(file_value, value_type)
            self._cache[key] = ConfigValue(file_value, ConfigSource.CONFIG_FILE, key)
            return file_value

        # 3. Check defaults
        default_value = self._get_nested(self._defaults, key)
        if default_value is not None:
            default_value = self._coerce_value(default_value, value_type)
            self._cache[key] = ConfigValue(default_value, ConfigSource.DEFAULT, key)
            return default_value

        # 4. Return provided default
        return default

    def set(self, key: str, value: Any, source: ConfigSource = ConfigSource.DEFAULT) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key.
            value: Value to set.
            source: Source of the value.
        """
        self._cache[key] = ConfigValue(value, source, key)

    def _get_env_key(self, key: str) -> str:
        """Convert config key to environment variable name."""
        # Convert "api_key" -> "CLAUDE_API_KEY"
        # Convert "database.host" -> "CLAUDE_DATABASE_HOST"
        parts = key.upper().split(".")
        return self._env_prefix + "_".join(parts)

    def _get_nested(self, data: Dict[str, Any], key: str) -> Any:
        """Get nested value using dot notation."""
        parts = key.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        return current

    def _coerce_value(self, value: Any, value_type: Optional[type]) -> Any:
        """Coerce value to specified type."""
        if value_type is None:
            return value

        if value_type == bool:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
        elif value_type == int:
            return int(value)
        elif value_type == float:
            return float(value)
        elif value_type == str:
            return str(value)
        elif value_type == list:
            if isinstance(value, str):
                return [v.strip() for v in value.split(",")]
            return list(value)
        elif value_type == dict:
            if isinstance(value, str):
                import json

                return json.loads(value)
            return dict(value)

        return value

    def get_source(self, key: str) -> Optional[ConfigSource]:
        """Get the source of a configuration value.

        Args:
            key: Configuration key.

        Returns:
            ConfigSource or None if not found.
        """
        return self._cache.get(key, {}).get("source")

    def reset_cache(self) -> None:
        """Reset the configuration cache."""
        self._cache.clear()

    def load_env_file(self, path: Union[str, Path] = ".env") -> None:
        """Load environment variables from .env file.

        Args:
            path: Path to .env file.
        """
        path = Path(path)
        if not path.exists():
            return

        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("'").strip('"')
                    os.environ[key] = value


# Global config manager
_config_manager: Optional[ConfigManager] = None


def get_config_manager(env_prefix: str = "CLAUDE_") -> ConfigManager:
    """Get or create the global configuration manager.

    Args:
        env_prefix: Prefix for environment variables.

    Returns:
        Global ConfigManager instance.
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(env_prefix=env_prefix)
    return _config_manager


def set_config_manager(manager: ConfigManager) -> None:
    """Set the global configuration manager.

    Args:
        manager: ConfigManager to use globally.
    """
    global _config_manager
    _config_manager = manager


# Decorator for configuration-backed settings
def config_value(
    key: str,
    default: Any = None,
    value_type: Optional[type] = None,
) -> Any:
    """Decorator/function to get config value with caching.

    Args:
        key: Configuration key.
        default: Default value.
        value_type: Type to coerce to.

    Returns:
        Configuration value.
    """
    return get_config_manager().get(key, default, value_type)