"""
Hooks configuration for Claude Code Python.

Manages loading and saving hook configurations.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- pathlib.Path for file operations
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, field

from claude_code.hooks.registry import HookConfig, HookRegistry, get_hook_registry


# Default constants
DEFAULT_CONFIG_VERSION: str = "1.0"
DEFAULT_TIMEOUT_MS: int = 15000
DEFAULT_SETTINGS_PATH: Path = Path.home() / ".claude" / "settings.json"


@dataclass(frozen=True, slots=True)
class HooksConfig:
    """Configuration for hooks.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        version: Configuration version string
        hooks: List of hook configuration dictionaries
        enabled: Whether hooks are enabled
    """
    version: str = DEFAULT_CONFIG_VERSION
    hooks: list[dict[str, Any]] = field(default_factory=list)
    enabled: bool = True


class HooksConfigManager:
    """Manages hooks configuration.
    
    Handles loading hooks from and saving hooks to configuration files.
    
    Attributes:
        config_path: Path to the configuration file
    
    Example:
        >>> manager = HooksConfigManager()
        >>> config = manager.load()
        >>> manager.add_hook(HookConfig(name="test", command="echo test", event="on_start"))
        >>> manager.save(config)
    """
    
    def __init__(self, config_path: Optional[str | Path] = None) -> None:
        """Initialize hooks config manager.
        
        Args:
            config_path: Optional custom configuration path
        """
        if config_path:
            self._config_path = Path(config_path)
        else:
            self._config_path = DEFAULT_SETTINGS_PATH
    
    @property
    def config_path(self) -> Path:
        """Get the configuration file path."""
        return self._config_path
    
    def load(self) -> HooksConfig:
        """Load hooks configuration from file.
        
        Returns:
            HooksConfig instance with loaded settings
        """
        if not self._config_path.exists():
            return HooksConfig()
        
        try:
            with open(self._config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            hooks_data = data.get("hooks", [])
            
            return HooksConfig(
                version=data.get("version", DEFAULT_CONFIG_VERSION),
                hooks=hooks_data,
                enabled=data.get("hooksEnabled", True),
            )
        except (json.JSONDecodeError, IOError):
            return HooksConfig()
    
    def save(self, config: HooksConfig) -> None:
        """Save hooks configuration to file.
        
        Args:
            config: Configuration to save
        """
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data: dict[str, Any] = {
            "version": config.version,
            "hooks": config.hooks,
            "hooksEnabled": config.enabled,
        }
        
        with open(self._config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def load_into_registry(self, registry: Optional[HookRegistry] = None) -> None:
        """Load configuration and register hooks.
        
        Args:
            registry: Optional hook registry to use
        """
        reg = registry or get_hook_registry()
        config = self.load()
        
        if not config.enabled:
            return
        
        for hook_data in config.hooks:
            hook = HookConfig(
                name=hook_data.get("name", ""),
                command=hook_data.get("command", ""),
                event=hook_data.get("event", ""),
                timeout_ms=hook_data.get("timeoutMs", DEFAULT_TIMEOUT_MS),
                async_timeout_ms=hook_data.get("asyncTimeoutMs", DEFAULT_TIMEOUT_MS),
                enabled=hook_data.get("enabled", True),
                cwd=hook_data.get("cwd"),
                env=hook_data.get("env", {}),
            )
            
            if hook.name and hook.command and hook.event:
                reg.register(hook)
    
    def add_hook(self, hook: HookConfig) -> None:
        """Add a hook to configuration.
        
        Args:
            hook: Hook configuration to add
        """
        config = self.load()
        
        config.hooks = [h for h in config.hooks if h.get("name") != hook.name]
        
        config.hooks.append({
            "name": hook.name,
            "command": hook.command,
            "event": hook.event,
            "timeoutMs": hook.timeout_ms,
            "asyncTimeoutMs": hook.async_timeout_ms,
            "enabled": hook.enabled,
            "cwd": hook.cwd,
            "env": hook.env,
        })
        
        self.save(config)
    
    def remove_hook(self, name: str) -> bool:
        """Remove a hook from configuration.
        
        Args:
            name: Name of the hook to remove
            
        Returns:
            True if removed, False if not found
        """
        config = self.load()
        
        original_count = len(config.hooks)
        config.hooks = [h for h in config.hooks if h.get("name") != name]
        
        if len(config.hooks) < original_count:
            self.save(config)
            return True
        return False
    
    def get_hook(self, name: str) -> Optional[dict[str, Any]]:
        """Get a hook configuration by name.
        
        Args:
            name: Hook name to retrieve
            
        Returns:
            Hook configuration dictionary or None
        """
        config = self.load()
        for hook in config.hooks:
            if hook.get("name") == name:
                return hook
        return None


def load_hooks_from_file(
    file_path: Optional[str | Path] = None,
    registry: Optional[HookRegistry] = None,
) -> HookRegistry:
    """Load hooks from a configuration file.
    
    Args:
        file_path: Optional path to hooks configuration file
        registry: Optional hook registry to register hooks in
        
    Returns:
        The hook registry with loaded hooks
    """
    reg = registry or get_hook_registry()
    
    manager = HooksConfigManager(file_path) if file_path else HooksConfigManager()
    manager.load_into_registry(reg)
    return reg


def create_hook_from_config(
    name: str,
    command: str,
    event: str,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    **kwargs: Any,
) -> HookConfig:
    """Create a hook configuration from parameters.
    
    Args:
        name: Hook name
        command: Command to execute
        event: Event that triggers the hook
        timeout_ms: Timeout in milliseconds
        **kwargs: Additional hook configuration
        
    Returns:
        HookConfig instance
    """
    return HookConfig(
        name=name,
        command=command,
        event=event,
        timeout_ms=timeout_ms,
        **kwargs,
    )
