"""
Claude Code Python - Configuration
Settings and configuration management.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Pydantic for complex validation
- Dataclass patterns for configuration
- pathlib.Path for file operations
- Module-level constants
- frozenset for constant sets
"""

from __future__ import annotations

import logging
import os
import json
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)
from dataclasses import dataclass, field
from enum import Enum

from pydantic import BaseModel, Field, field_validator


# Module-level constants
DEFAULT_MODEL: str = "claude-sonnet-4-20250514"
DEFAULT_MAX_TOKENS: int = 8192
DEFAULT_AZURE_API_VERSION: str = "2024-01-01"
DEFAULT_COMPACT_THRESHOLD: int = 150000

# Permission mode — import from canonical source
from claude_code.permissions import PermissionMode, PERMISSION_MODES

# Constant sets using frozenset
VALID_PROVIDERS: frozenset[str] = frozenset({"anthropic", "bedrock", "vertex", "azure"})
VALID_PERMISSION_MODES: frozenset[str] = frozenset(PERMISSION_MODES)
SUPPORTED_AWS_REGIONS: frozenset[str] = frozenset({
    "us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "ap-northeast-1"
})


class APIConfig(BaseModel):
    """API configuration settings using Pydantic for validation."""
    model_config = {"frozen": True, "slots": True}
    
    provider: str = "anthropic"
    api_key: str | None = None
    model: str = DEFAULT_MODEL
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float | None = None
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v not in VALID_PROVIDERS:
            raise ValueError(f"Provider must be one of: {VALID_PROVIDERS}")
        return v
    
    @field_validator('max_tokens')
    @classmethod
    def validate_max_tokens(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("max_tokens must be positive")
        if v > 200000:
            raise ValueError("max_tokens cannot exceed 200000")
        return v
    
    @field_validator('temperature')
    @classmethod
    def validate_temperature(cls, v: float | None) -> float | None:
        if v is not None and (v < 0 or v > 2):
            raise ValueError("temperature must be between 0 and 2")
        return v


class ProviderConfig(BaseModel):
    """Provider-specific configuration using Pydantic."""
    model_config = {"frozen": True, "slots": True}
    
    aws_region: str | None = None
    aws_profile: str | None = None
    vertex_project: str | None = None
    vertex_location: str | None = None
    azure_endpoint: str | None = None
    azure_api_version: str = DEFAULT_AZURE_API_VERSION
    
    @field_validator('aws_region')
    @classmethod
    def validate_aws_region(cls, v: str | None) -> str | None:
        if v is not None and v not in SUPPORTED_AWS_REGIONS:
            raise ValueError(f"AWS region must be one of: {SUPPORTED_AWS_REGIONS}")
        return v


class Config(BaseModel):
    """Main configuration for Claude Code using Pydantic.
    
    Using Pydantic for automatic validation and better error handling.
    
    Attributes:
        api_provider: API provider name
        api_key: API key for authentication
        model: Model identifier
        max_tokens: Maximum tokens per request
        temperature: Optional sampling temperature
        aws_region: AWS region for Bedrock
        aws_profile: AWS profile for Bedrock
        vertex_project: Google Cloud project for Vertex
        vertex_location: Google Cloud location for Vertex
        azure_endpoint: Azure OpenAI endpoint
        azure_api_version: Azure API version
        permission_mode: Permission mode for tool execution
        always_allow: List of tool names to always allow
        always_deny: List of tool names to always deny
        verbose: Enable verbose output
        stream_output: Stream tool output in real-time
        show_timing: Show execution timing information
        config_dir: Directory for configuration files
        cache_dir: Directory for cache files
        data_dir: Directory for data files
        enable_compact: Enable automatic context compaction
        compact_threshold: Token threshold for compaction
        enable_telemetry: Enable telemetry reporting
    """
    model_config = {"arbitrary_types_allowed": True}
    
    # API settings
    api_provider: str = "anthropic"
    api_key: str | None = None
    model: str = DEFAULT_MODEL
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float | None = None
    
    # Provider-specific settings
    aws_region: str | None = None
    aws_profile: str | None = None
    vertex_project: str | None = None
    vertex_location: str | None = None
    azure_endpoint: str | None = None
    azure_api_version: str = DEFAULT_AZURE_API_VERSION
    
    # Behavior settings
    permission_mode: PermissionMode = PermissionMode.DEFAULT
    always_allow: list[str] = Field(default_factory=list)
    always_deny: list[str] = Field(default_factory=list)
    verbose: bool = False
    stream_output: bool = True
    show_timing: bool = True
    
    # Paths
    config_dir: Path = Field(default_factory=lambda: Path.home() / ".claude-code-python")
    cache_dir: Path | None = None
    data_dir: Path | None = None
    
    # Features
    enable_compact: bool = True
    compact_threshold: int = DEFAULT_COMPACT_THRESHOLD
    enable_telemetry: bool = False
    
    def __init__(self, **data: Any) -> None:
        """Initialize with path defaults."""
        super().__init__(**data)
        # Set default derived paths if not provided
        if self.cache_dir is None:
            object.__setattr__(self, 'cache_dir', self.config_dir / "cache")
        if self.data_dir is None:
            object.__setattr__(self, 'data_dir', self.config_dir / "data")
    
    @field_validator('api_provider')
    @classmethod
    def validate_api_provider(cls, v: str) -> str:
        if v not in VALID_PROVIDERS:
            raise ValueError(f"Provider must be one of: {VALID_PROVIDERS}")
        return v
    
    @field_validator('permission_mode', mode='before')
    def validate_permission_mode(cls, v: Any) -> PermissionMode:
        if isinstance(v, PermissionMode):
            return v
        if isinstance(v, str):
            return PermissionMode(v.lower())
        raise ValueError("Invalid permission mode")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation of config.
        """
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create from dictionary.
        
        Args:
            data: Dictionary with configuration values.
            
        Returns:
            Config instance.
        """
        return cls(**data)
    
    def save(self, path: Path | None = None) -> None:
        """Save configuration to file.
        
        Args:
            path: Optional path to save to. Defaults to config_dir/config.json.
        """
        if path is None:
            path = self.config_dir / "config.json"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    @classmethod
    def load(cls, path: Path | None = None, environment: str | None = None) -> Config:
        """Load configuration from file with environment support.
        
        Configuration loading order (later overwrites earlier):
        1. Default values
        2. base.json (if exists)
        3. {environment}.json (e.g., dev.json, prod.json)
        4. config.json (manual overrides)
        5. Environment variables
        
        Args:
            path: Optional path to load base config from.
            environment: Environment name (dev, staging, prod). 
                        If None, reads from CLAUDE_ENV env var.
            
        Returns:
            Config instance with merged configuration.
        """
        if path is None:
            path = cls().config_dir / "config.json"
        
        # Determine environment
        if environment is None:
            environment = os.getenv("CLAUDE_ENV", "default")
        
        # Start with default config
        config = cls()
        
        # Load and merge configuration files in order
        config_files = [
            config.config_dir / "base.json",
            config.config_dir / f"{environment}.json",
            path,  # config.json
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    config = cls.from_dict(data)
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_file}: {e}")
        
        # Apply environment variables (highest priority)
        config.update_from_env()
        
        return config
    
    @classmethod
    def load_environment_config(cls, environment: str) -> dict[str, Any]:
        """Load configuration for a specific environment.
        
        Args:
            environment: Environment name (dev, staging, prod)
            
        Returns:
            Dictionary of configuration values for the environment
        """
        config = cls()
        env_path = config.config_dir / f"{environment}.json"
        
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {}
    
    def update_from_env(self) -> None:
        """Update configuration from environment variables.
        
        Reads from standard environment variables:
        - ANTHROPIC_API_KEY
        - CLAUDE_API_PROVIDER
        - CLAUDE_MODEL
        - CLAUDE_MAX_TOKENS
        - CLAUDE_TEMPERATURE
        - AWS_REGION, AWS_PROFILE
        - VERTEX_PROJECT, VERTEX_LOCATION
        - AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_VERSION
        - CLAUDE_VERBOSE
        - CLAUDE_PERMISSION_MODE
        """
        # Use object.__setattr__ for Pydantic frozen model
        def _set(attr: str, value: Any) -> None:
            object.__setattr__(self, attr, value)
        
        # API settings
        if api_key := os.getenv("ANTHROPIC_API_KEY"):
            _set("api_key", api_key)
        
        if provider := os.getenv("CLAUDE_API_PROVIDER"):
            if provider in VALID_PROVIDERS:
                _set("api_provider", provider)
        
        if model := os.getenv("CLAUDE_MODEL"):
            _set("model", model)
        
        if max_tokens := os.getenv("CLAUDE_MAX_TOKENS"):
            try:
                tokens = int(max_tokens)
                if 0 < tokens <= 200000:
                    _set("max_tokens", tokens)
            except ValueError:
                pass
        
        if temp := os.getenv("CLAUDE_TEMPERATURE"):
            try:
                temp_val = float(temp)
                if 0 <= temp_val <= 2:
                    _set("temperature", temp_val)
            except ValueError:
                pass
        
        # AWS settings
        if region := os.getenv("AWS_REGION"):
            _set("aws_region", region)
        if profile := os.getenv("AWS_PROFILE"):
            _set("aws_profile", profile)
        
        # Vertex settings
        if project := os.getenv("VERTEX_PROJECT"):
            _set("vertex_project", project)
        if location := os.getenv("VERTEX_LOCATION"):
            _set("vertex_location", location)
        
        # Azure settings
        if endpoint := os.getenv("AZURE_OPENAI_ENDPOINT"):
            _set("azure_endpoint", endpoint)
        if api_version := os.getenv("AZURE_OPENAI_API_VERSION"):
            _set("azure_api_version", api_version)
        
        # Behavior settings
        if os.getenv("CLAUDE_VERBOSE"):
            _set("verbose", True)
        
        if mode := os.getenv("CLAUDE_PERMISSION_MODE"):
            try:
                _set("permission_mode", PermissionMode(mode.lower()))
            except ValueError:
                pass


class LocalSettings:
    """Local settings that can be saved per-project.
    
    Stored in .claude-code-python.json in the working directory.
    
    Following Python best practices:
    - Clear property definitions
    - Type hints
    - Docstrings
    - __slots__ for memory optimization
    """
    
    __slots__ = ('working_dir', '_settings')
    
    def __init__(self, working_dir: str | Path | None = None) -> None:
        """Initialize local settings.
        
        Args:
            working_dir: Working directory for settings. Defaults to current directory.
        """
        self.working_dir: Path = Path(working_dir or os.getcwd())
        self._settings: dict[str, Any] = {}
        self._load()
    
    @property
    def permission_mode(self) -> str:
        """Get permission mode setting."""
        return self._settings.get("permission_mode", "default")
    
    @permission_mode.setter
    def permission_mode(self, value: str) -> None:
        """Set permission mode."""
        self._settings["permission_mode"] = value
    
    @property
    def always_allow(self) -> list[str]:
        """Get list of always allowed tools."""
        return self._settings.get("always_allow", [])
    
    @always_allow.setter
    def always_allow(self, value: list[str]) -> None:
        """Set always allow list."""
        self._settings["always_allow"] = value
    
    @property
    def always_deny(self) -> list[str]:
        """Get list of always denied tools."""
        return self._settings.get("always_deny", [])
    
    @always_deny.setter
    def always_deny(self, value: list[str]) -> None:
        """Set always deny list."""
        self._settings["always_deny"] = value
    
    @property
    def additional_directories(self) -> list[str]:
        """Get additional directories list."""
        return self._settings.get("additional_directories", [])
    
    @additional_directories.setter
    def additional_directories(self, value: list[str]) -> None:
        """Set additional directories."""
        self._settings["additional_directories"] = value
    
    def _get_path(self) -> Path:
        """Get path to settings file."""
        return self.working_dir / ".claude-code-python.json"
    
    def _load(self) -> None:
        """Load settings from file."""
        path = self._get_path()
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    self._settings = json.load(f)
            except Exception:
                self._settings = {}
    
    def save(self) -> None:
        """Save settings to file."""
        path = self._get_path()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._settings, f, indent=2)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value.
        
        Args:
            key: Setting key to retrieve.
            default: Default value if key not found.
            
        Returns:
            Setting value or default.
        """
        return self._settings.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a setting value.
        
        Args:
            key: Setting key.
            value: Value to set.
        """
        self._settings[key] = value
    
    def clear(self) -> None:
        """Clear all settings and delete file."""
        self._settings = {}
        path = self._get_path()
        if path.exists():
            path.unlink()


# Global configuration instance
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration.
    
    Returns:
        Global Config instance, loaded from file and environment.
    """
    global _config
    
    if _config is None:
        _config = Config.load()
        _config.update_from_env()
    
    return _config


def save_config() -> None:
    """Save the global configuration."""
    global _config
    
    if _config is not None:
        _config.save()


# Environment variable prefix
ENV_PREFIX = "CLAUDE_"

# Lazy import for features to avoid circular import
def _get_features():
    from claude_code.utils.features_config import features
    return features

_features = None

def get_features():
    """Get the global features instance."""
    global _features
    if _features is None:
        _features = _get_features()
    return _features

class _FeaturesProxy:
    """Proxy to lazy-loaded features."""
    def __getattr__(self, name):
        return getattr(get_features(), name)

# For backwards compatibility
Features = _FeaturesProxy()


# Lazy import for settings
def _get_settings():
    from claude_code.utils.unified_settings import Settings
    return Settings()


_settings: Any = None


def get_settings() -> Any:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = _get_settings()
    return _settings


__all__ = [
    "APIConfig",
    "ProviderConfig",
    "Config",
    "LocalSettings",
    "PermissionMode",
    "DEFAULT_MODEL",
    "DEFAULT_MAX_TOKENS",
    "DEFAULT_AZURE_API_VERSION",
    "DEFAULT_COMPACT_THRESHOLD",
    "VALID_PROVIDERS",
    "VALID_PERMISSION_MODES",
    "SUPPORTED_AWS_REGIONS",
    "ENV_PREFIX",
    "get_config",
    "save_config",
    "get_features",
    "get_settings",
]
