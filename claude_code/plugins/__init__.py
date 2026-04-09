import warnings
warnings.warn(f"{__name__} is deprecated and will be removed in a future version.", DeprecationWarning, stacklevel=2)
"""
Claude Code Python - Plugin System
插件系统基础架构 - 借鉴 TS 版本设计
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional, Callable, Any, Awaitable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from abc import ABC, abstractmethod
import importlib.util
import sys


class PluginType(Enum):
    """插件类型"""
    BUILTIN = "builtin"
    LOCAL = "local"
    MARKETPLACE = "marketplace"
    MCP = "mcp"


class PluginCapability(Enum):
    """插件能力"""
    COMMAND = "command"
    TOOL = "tool"
    HOOK = "hook"
    PROVIDER = "provider"
    THEME = "theme"


@dataclass
class PluginMetadata:
    """插件元数据"""
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
    config_schema: dict = field(default_factory=dict)


@dataclass
class Plugin:
    """插件实例"""
    metadata: PluginMetadata
    root_path: Path
    enabled: bool = True
    loaded_at: Optional[str] = None
    _instance: Any = None
    
    @property
    def instance(self) -> Any:
        return self._instance
    
    @instance.setter
    def instance(self, value: Any):
        self._instance = value


class PluginHook(ABC):
    """插件钩子基类"""
    
    @abstractmethod
    async def on_load(self, plugin: Plugin) -> None:
        """插件加载时调用"""
        pass
    
    @abstractmethod
    async def on_unload(self, plugin: Plugin) -> None:
        """插件卸载时调用"""
        pass


class ToolPlugin(PluginHook):
    """工具插件"""
    
    @abstractmethod
    def get_tools(self) -> list[Any]:
        """获取插件提供的工具"""
        pass


class CommandPlugin(PluginHook):
    """命令插件"""
    
    @abstractmethod
    def get_commands(self) -> list[Any]:
        """获取插件提供的命令"""
        pass


class HookPlugin(PluginHook):
    """钩子插件"""
    
    @abstractmethod
    def get_hooks(self) -> dict[str, Callable]:
        """获取插件提供的钩子"""
        pass


class PluginManager:
    """
    插件管理器
    借鉴 TS 版本的 PluginInstallationManager 设计
    """
    
    def __init__(self, working_directory: str = None):
        self._working_directory = Path(working_directory or ".")
        self._plugins: dict[str, Plugin] = {}
        self._plugin_loaders: dict[str, Callable] = {}
        self._enabled_plugins: set[str] = set()
    
    def register_loader(
        self,
        plugin_type: PluginType,
        loader: Callable[[dict], Awaitable[Optional[Plugin]]],
    ) -> None:
        """注册插件加载器"""
        self._plugin_loaders[plugin_type.value] = loader
    
    async def load_plugin(
        self,
        plugin_id: str,
        plugin_config: dict,
    ) -> Plugin:
        """加载插件"""
        if plugin_id in self._plugins:
            return self._plugins[plugin_id]
        
        plugin_type = PluginType(plugin_config.get("type", "local"))
        loader = self._plugin_loaders.get(plugin_type.value)
        
        if loader:
            plugin = await loader(plugin_config)
            if plugin:
                self._plugins[plugin_id] = plugin
                await plugin.instance.on_load(plugin) if hasattr(plugin.instance, 'on_load') else None
                return plugin
        
        return None
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """卸载插件"""
        if plugin_id not in self._plugins:
            return False
        
        plugin = self._plugins[plugin_id]
        
        if hasattr(plugin.instance, 'on_unload'):
            await plugin.instance.on_unload(plugin)
        
        del self._plugins[plugin_id]
        self._enabled_plugins.discard(plugin_id)
        
        return True
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """启用插件"""
        if plugin_id not in self._plugins:
            return False
        
        self._enabled_plugins.add(plugin_id)
        self._plugins[plugin_id].enabled = True
        return True
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """禁用插件"""
        if plugin_id not in self._plugins:
            return False
        
        self._enabled_plugins.discard(plugin_id)
        self._plugins[plugin_id].enabled = False
        return True
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """获取插件"""
        return self._plugins.get(plugin_id)
    
    def list_plugins(
        self,
        plugin_type: PluginType = None,
        enabled_only: bool = False,
    ) -> list[Plugin]:
        """列出插件"""
        plugins = list(self._plugins.values())
        
        if plugin_type:
            plugins = [p for p in plugins if p.metadata.plugin_type == plugin_type]
        
        if enabled_only:
            plugins = [p for p in plugins if p.enabled]
        
        return plugins
    
    def get_all_tools(self) -> list[Any]:
        """获取所有插件提供的工具"""
        tools = []
        for plugin in self.list_plugins(enabled_only=True):
            if isinstance(plugin.instance, ToolPlugin):
                tools.extend(plugin.instance.get_tools())
        return tools
    
    def get_all_commands(self) -> list[Any]:
        """获取所有插件提供的命令"""
        commands = []
        for plugin in self.list_plugins(enabled_only=True):
            if isinstance(plugin.instance, CommandPlugin):
                commands.extend(plugin.instance.get_commands())
        return commands
    
    def get_all_hooks(self) -> dict[str, list[Callable]]:
        """获取所有插件提供的钩子"""
        hooks = {}
        for plugin in self.list_plugins(enabled_only=True):
            if isinstance(plugin.instance, HookPlugin):
                plugin_hooks = plugin.instance.get_hooks()
                for event, handlers in plugin_hooks.items():
                    if event not in hooks:
                        hooks[event] = []
                    hooks[event].extend(handlers)
        return hooks


class BuiltinPluginLoader:
    """内置插件加载器"""
    
    @staticmethod
    async def load(config: dict) -> Optional[Plugin]:
        """加载内置插件"""
        plugin_id = config.get("id")
        plugin_path = config.get("path")
        
        if not plugin_path:
            return None
        
        spec = importlib.util.spec_from_file_location(plugin_id, plugin_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_id] = module
            spec.loader.exec_module(module)
            
            if hasattr(module, "get_plugin"):
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
        
        return None


class LocalPluginLoader:
    """本地插件加载器"""
    
    @staticmethod
    async def load(config: dict) -> Optional[Plugin]:
        """加载本地插件"""
        plugin_id = config.get("id")
        plugin_path = Path(config.get("path", f"./plugins/{plugin_id}"))
        
        metadata_file = plugin_path / "plugin.json"
        
        if not metadata_file.exists():
            return None
        
        with open(metadata_file) as f:
            metadata = json.load(f)
        
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
        )


class MCPPluginLoader:
    """MCP 插件加载器"""
    
    @staticmethod
    async def load(config: dict) -> Optional[Plugin]:
        """加载 MCP 插件"""
        plugin_id = config.get("id")
        
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


def create_plugin_manager(working_directory: str = None) -> PluginManager:
    """创建插件管理器"""
    manager = PluginManager(working_directory)
    
    manager.register_loader(PluginType.BUILTIN, BuiltinPluginLoader.load)
    manager.register_loader(PluginType.LOCAL, LocalPluginLoader.load)
    manager.register_loader(PluginType.MCP, MCPPluginLoader.load)
    
    return manager


_default_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取默认插件管理器"""
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
