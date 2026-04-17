"""Claude Code Python - Plugin System."""

from __future__ import annotations

import importlib.util
import inspect
import json
import sys
import warnings
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Optional

warnings.warn(
    f"{__name__} is deprecated and will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)


class PluginType(Enum):
    BUILTIN = "builtin"
    LOCAL = "local"
    MARKETPLACE = "marketplace"
    MCP = "mcp"


class PluginCapability(Enum):
    COMMAND = "command"
    TOOL = "tool"
    HOOK = "hook"
    PROVIDER = "provider"
    THEME = "theme"


@dataclass
class PluginMetadata:
    id: str
    name: str
    version: str
    description: str
    author: str = ""
    homepage: str = ""
    license: str = "MIT"
    plugin_type: PluginType = PluginType.LOCAL
    capabilities: list[PluginCapability] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    config_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plugin:
    metadata: PluginMetadata
    root_path: Path
    enabled: bool = True
    loaded_at: Optional[str] = None
    _instance: Any = None

    @property
    def instance(self) -> Any:
        return self._instance

    @instance.setter
    def instance(self, value: Any) -> None:
        self._instance = value


class PluginHook(ABC):
    @abstractmethod
    async def on_load(self, plugin: Plugin) -> None:
        pass

    @abstractmethod
    async def on_unload(self, plugin: Plugin) -> None:
        pass


class ToolPlugin(PluginHook):
    @abstractmethod
    def get_tools(self) -> list[Any]:
        pass


class CommandPlugin(PluginHook):
    @abstractmethod
    def get_commands(self) -> list[Any]:
        pass


class HookPlugin(PluginHook):
    @abstractmethod
    def get_hooks(self) -> dict[str, list[Callable[..., Any]]]:
        pass


async def _maybe_await(value: Any) -> None:
    if inspect.isawaitable(value):
        await value


class PluginManager:
    """Plugin manager with loader registration + lifecycle control."""

    def __init__(self, working_directory: str | None = None) -> None:
        self._working_directory = Path(working_directory or ".")
        self._plugins: dict[str, Plugin] = {}
        self._plugin_loaders: dict[str, Callable[[dict[str, Any]], Awaitable[Optional[Plugin]]]] = {}
        self._enabled_plugins: set[str] = set()

    def register_loader(
        self,
        plugin_type: PluginType,
        loader: Callable[[dict[str, Any]], Awaitable[Optional[Plugin]]],
    ) -> None:
        self._plugin_loaders[plugin_type.value] = loader

    async def load_plugin(self, plugin_id: str, plugin_config: dict[str, Any]) -> Optional[Plugin]:
        if plugin_id in self._plugins:
            return self._plugins[plugin_id]

        plugin_type = PluginType(plugin_config.get("type", "local"))
        loader = self._plugin_loaders.get(plugin_type.value)
        if loader is None:
            return None

        plugin = await loader(plugin_config)
        if plugin is None:
            return None

        self._plugins[plugin_id] = plugin
        if plugin.enabled:
            self._enabled_plugins.add(plugin_id)

        hook = getattr(plugin.instance, "on_load", None)
        if hook is not None:
            await _maybe_await(hook(plugin))

        return plugin

    async def unload_plugin(self, plugin_id: str) -> bool:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            return False

        hook = getattr(plugin.instance, "on_unload", None)
        if hook is not None:
            await _maybe_await(hook(plugin))

        self._enabled_plugins.discard(plugin_id)
        del self._plugins[plugin_id]
        return True

    def enable_plugin(self, plugin_id: str) -> bool:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            return False
        plugin.enabled = True
        self._enabled_plugins.add(plugin_id)
        return True

    def disable_plugin(self, plugin_id: str) -> bool:
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            return False
        plugin.enabled = False
        self._enabled_plugins.discard(plugin_id)
        return True

    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        return self._plugins.get(plugin_id)

    def list_plugins(
        self,
        plugin_type: PluginType | None = None,
        enabled_only: bool = False,
    ) -> list[Plugin]:
        plugins = list(self._plugins.values())
        if plugin_type is not None:
            plugins = [p for p in plugins if p.metadata.plugin_type == plugin_type]
        if enabled_only:
            plugins = [p for p in plugins if p.enabled]
        return plugins

    def get_all_tools(self) -> list[Any]:
        tools: list[Any] = []
        for plugin in self.list_plugins(enabled_only=True):
            instance = plugin.instance
            if instance is None:
                continue
            if isinstance(instance, ToolPlugin) or hasattr(instance, "get_tools"):
                tools.extend(instance.get_tools())
        return tools

    def get_all_commands(self) -> list[Any]:
        commands: list[Any] = []
        for plugin in self.list_plugins(enabled_only=True):
            instance = plugin.instance
            if instance is None:
                continue
            if isinstance(instance, CommandPlugin) or hasattr(instance, "get_commands"):
                commands.extend(instance.get_commands())
        return commands

    def get_all_hooks(self) -> dict[str, list[Callable[..., Any]]]:
        hooks: dict[str, list[Callable[..., Any]]] = {}
        for plugin in self.list_plugins(enabled_only=True):
            instance = plugin.instance
            if instance is None:
                continue
            if isinstance(instance, HookPlugin) or hasattr(instance, "get_hooks"):
                plugin_hooks = instance.get_hooks()
                for event, handlers in plugin_hooks.items():
                    hooks.setdefault(event, []).extend(handlers)
        return hooks


class BuiltinPluginLoader:
    """Load built-in plugin modules from file path."""

    @staticmethod
    async def load(config: dict[str, Any]) -> Optional[Plugin]:
        plugin_id = config.get("id")
        plugin_path = config.get("path")
        if not plugin_id or not plugin_path:
            return None

        spec = importlib.util.spec_from_file_location(plugin_id, plugin_path)
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[plugin_id] = module
        spec.loader.exec_module(module)

        if not hasattr(module, "get_plugin"):
            return None

        plugin_instance = module.get_plugin()
        return Plugin(
            metadata=PluginMetadata(
                id=plugin_id,
                name=config.get("name", plugin_id),
                version=config.get("version", "1.0.0"),
                description=config.get("description", ""),
                plugin_type=PluginType.BUILTIN,
            ),
            root_path=Path(plugin_path),
            _instance=plugin_instance,
        )


class LocalPluginLoader:
    """Load local plugins from plugin.json."""

    @staticmethod
    async def load(config: dict[str, Any]) -> Optional[Plugin]:
        plugin_id = config.get("id")
        if not plugin_id:
            return None

        plugin_path = Path(config.get("path", f"./plugins/{plugin_id}"))
        metadata_file = plugin_path / "plugin.json"
        if not metadata_file.exists():
            return None

        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
        plugin_instance = None
        entry_file = metadata.get("entry", "plugin.py")
        entry_path = plugin_path / entry_file
        if entry_path.is_file():
            module_name = (
                f"claude_code_local_plugin_{plugin_id}_"
                f"{abs(hash(str(entry_path.resolve())))}"
            )
            spec = importlib.util.spec_from_file_location(module_name, str(entry_path))
            if spec is not None and spec.loader is not None:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                if hasattr(module, "get_plugin"):
                    plugin_instance = module.get_plugin()

        return Plugin(
            metadata=PluginMetadata(
                id=metadata.get("id", plugin_id),
                name=metadata.get("name", plugin_id),
                version=metadata.get("version", "1.0.0"),
                description=metadata.get("description", ""),
                author=metadata.get("author", ""),
                plugin_type=PluginType.LOCAL,
            ),
            root_path=plugin_path,
            _instance=plugin_instance,
        )


class MCPPluginLoader:
    """Placeholder MCP plugin loader."""

    @staticmethod
    async def load(config: dict[str, Any]) -> Optional[Plugin]:
        plugin_id = config.get("id")
        if not plugin_id:
            return None

        return Plugin(
            metadata=PluginMetadata(
                id=plugin_id,
                name=config.get("name", plugin_id),
                version=config.get("version", "1.0.0"),
                description=config.get("description", "MCP Plugin"),
                plugin_type=PluginType.MCP,
                capabilities=[PluginCapability.TOOL],
            ),
            root_path=Path("."),
        )


def create_plugin_manager(working_directory: str | None = None) -> PluginManager:
    manager = PluginManager(working_directory)
    manager.register_loader(PluginType.BUILTIN, BuiltinPluginLoader.load)
    manager.register_loader(PluginType.LOCAL, LocalPluginLoader.load)
    manager.register_loader(PluginType.MCP, MCPPluginLoader.load)
    return manager


_default_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    global _default_manager
    if _default_manager is None:
        _default_manager = create_plugin_manager()
    return _default_manager


__all__ = [
    "PluginType",
    "PluginCapability",
    "PluginMetadata",
    "Plugin",
    "PluginHook",
    "ToolPlugin",
    "CommandPlugin",
    "HookPlugin",
    "PluginManager",
    "create_plugin_manager",
    "get_plugin_manager",
]
