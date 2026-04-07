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

import os
import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field
from enum import Enum


# Module-level constants
DEFAULT_MODEL: str = "claude-sonnet-4-20250514"
DEFAULT_MAX_TOKENS: int = 8192
DEFAULT_AZURE_API_VERSION: str = "2024-01-01"
DEFAULT_COMPACT_THRESHOLD: int = 150000

# Permission mode enum
class PermissionMode(Enum):
    """Permission mode for tool execution.
    
    Attributes:
        DEFAULT: Ask for permission before dangerous operations
        AUTO: Auto-approve safe operations
        PLAN: Plan mode, ask for everything
        BYPASS: No permission checks (dangerous)
    """
    DEFAULT = "default"
    AUTO = "auto"
    PLAN = "plan"
    BYPASS = "bypass"


# Constant sets using frozenset
VALID_PROVIDERS: frozenset[str] = frozenset({"anthropic", "bedrock", "vertex", "azure"})
VALID_PERMISSION_MODES: frozenset[str] = frozenset({"default", "auto", "plan", "bypass"})
SUPPORTED_AWS_REGIONS: frozenset[str] = frozenset({
    "us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "ap-northeast-1"
})


@dataclass(frozen=True, slots=True)
class APIConfig:
    """API configuration settings.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        provider: API provider name
        api_key: Optional API key
        model: Model identifier
        max_tokens: Maximum tokens in response
        temperature: Optional sampling temperature
    """
    provider: str = "anthropic"
    api_key: Optional[str] = None
    model: str = DEFAULT_MODEL
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: Optional[float] = None


@dataclass(frozen=True, slots=True)
class ProviderConfig:
    """Provider-specific configuration.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        aws_region: AWS region for Bedrock
        aws_profile: AWS profile for Bedrock
        vertex_project: Google Cloud project for Vertex
        vertex_location: Google Cloud location for Vertex
        azure_endpoint: Azure OpenAI endpoint
        azure_api_version: Azure API version
    """
    aws_region: Optional[str] = None
    aws_profile: Optional[str] = None
    vertex_project: Optional[str] = None
    vertex_location: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_api_version: str = DEFAULT_AZURE_API_VERSION


@dataclass
class Config:
    """Main configuration for Claude Code.
    
    Using standard dataclass (not frozen) because it needs to support
    runtime updates from environment variables and user settings.
    
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
    
    # API settings
    api_provider: str = "anthropic"
    api_key: Optional[str] = None
    model: str = DEFAULT_MODEL
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: Optional[float] = None
    
    # Provider-specific settings
    aws_region: Optional[str] = None
    aws_profile: Optional[str] = None
    vertex_project: Optional[str] = None
    vertex_location: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_api_version: str = DEFAULT_AZURE_API_VERSION
    
    # Behavior settings
    permission_mode: PermissionMode = PermissionMode.DEFAULT
    always_allow: list[str] = field(default_factory=list)
    always_deny: list[str] = field(default_factory=list)
    verbose: bool = False
    stream_output: bool = True
    show_timing: bool = True
    
    # Paths
    config_dir: Path = field(default_factory=lambda: Path.home() / ".claude-code-python")
    cache_dir: Optional[Path] = None
    data_dir: Optional[Path] = None
    
    # Features
    enable_compact: bool = True
    compact_threshold: int = DEFAULT_COMPACT_THRESHOLD
    enable_telemetry: bool = False
    
    def __post_init__(self) -> None:
        """Post-initialization processing."""
        if self.cache_dir is None:
            self.cache_dir = self.config_dir / "cache"
        
        if self.data_dir is None:
            self.data_dir = self.config_dir / "data"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation of config.
        """
        return {
            "api_provider": self.api_provider,
            "api_key": self.api_key,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "aws_region": self.aws_region,
            "aws_profile": self.aws_profile,
            "vertex_project": self.vertex_project,
            "vertex_location": self.vertex_location,
            "azure_endpoint": self.azure_endpoint,
            "azure_api_version": self.azure_api_version,
            "permission_mode": self.permission_mode.value,
            "always_allow": self.always_allow,
            "always_deny": self.always_deny,
            "verbose": self.verbose,
            "stream_output": self.stream_output,
            "show_timing": self.show_timing,
            "enable_compact": self.enable_compact,
            "compact_threshold": self.compact_threshold,
            "enable_telemetry": self.enable_telemetry,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Config:
        """Create from dictionary.
        
        Args:
            data: Dictionary with configuration values.
            
        Returns:
            Config instance.
        """
        if "permission_mode" in data:
            data["permission_mode"] = PermissionMode(data["permission_mode"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to file.
        
        Args:
            path: Optional path to save to. Defaults to config_dir/config.json.
        """
        if path is None:
            path = self.config_dir / "config.json"
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> Config:
        """Load configuration from file.
        
        Args:
            path: Optional path to load from.
            
        Returns:
            Config instance, or default if file doesn't exist.
        """
        if path is None:
            path = cls().config_dir / "config.json"
        
        if not path.exists():
            return cls()
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls.from_dict(data)
        except Exception:
            return cls()
    
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
        # API settings
        if api_key := os.getenv("ANTHROPIC_API_KEY"):
            self.api_key = api_key
        
        if provider := os.getenv("CLAUDE_API_PROVIDER"):
            self.api_provider = provider
        
        if model := os.getenv("CLAUDE_MODEL"):
            self.model = model
        
        if max_tokens := os.getenv("CLAUDE_MAX_TOKENS"):
            try:
                self.max_tokens = int(max_tokens)
            except ValueError:
                pass
        
        if temp := os.getenv("CLAUDE_TEMPERATURE"):
            try:
                self.temperature = float(temp)
            except ValueError:
                pass
        
        # AWS settings
        if region := os.getenv("AWS_REGION"):
            self.aws_region = region
        if profile := os.getenv("AWS_PROFILE"):
            self.aws_profile = profile
        
        # Vertex settings
        if project := os.getenv("VERTEX_PROJECT"):
            self.vertex_project = project
        if location := os.getenv("VERTEX_LOCATION"):
            self.vertex_location = location
        
        # Azure settings
        if endpoint := os.getenv("AZURE_OPENAI_ENDPOINT"):
            self.azure_endpoint = endpoint
        if api_version := os.getenv("AZURE_OPENAI_API_VERSION"):
            self.azure_api_version = api_version
        
        # Behavior settings
        if os.getenv("CLAUDE_VERBOSE"):
            self.verbose = True
        
        if mode := os.getenv("CLAUDE_PERMISSION_MODE"):
            try:
                self.permission_mode = PermissionMode(mode.lower())
            except ValueError:
                pass


class LocalSettings:
    """
    Local settings that can be saved per-project.
    
    Stored in .claude-code-python.json in the working directory.
    
    Following Python best practices:
    - Clear property definitions
    - Type hints
    - Docstrings
    """
    
    def __init__(self, working_dir: Optional[str] = None) -> None:
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
_config: Optional[Config] = None


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
