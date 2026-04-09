import warnings
warnings.warn(f"{__name__} is deprecated and will be removed in a future version.", DeprecationWarning, stacklevel=2)
"""
Claude Code Python - Tool Registry
支持延迟加载的工具注册表.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Lazy loading for performance
"""

from __future__ import annotations

import importlib
import logging
from typing import Any, Optional

from claude_code.tools.base import Tool

logger = logging.getLogger(__name__)


# 工具模块映射表 (延迟加载)
TOOL_REGISTRY: dict[str, tuple[str, str]] = {
    # Builtin tools
    "bash": ("claude_code.tools.builtin", "BashTool"),
    "read": ("claude_code.tools.builtin", "ReadTool"),
    "write": ("claude_code.tools.builtin", "WriteTool"),
    "edit": ("claude_code.tools.builtin", "EditTool"),
    "glob": ("claude_code.tools.builtin", "GlobTool"),
    "grep": ("claude_code.tools.builtin", "GrepTool"),
    "notebook_edit": ("claude_code.tools.builtin", "NotebookEditTool"),
    
    # Utility tools
    "todo_write": ("claude_code.tools.utility", "TodoWriteTool"),
    "web_search": ("claude_code.tools.utility", "WebSearchTool"),
    "web_fetch": ("claude_code.tools.utility", "WebFetchTool"),
    "send_message": ("claude_code.tools.utility", "SendMessageTool"),
    "snip": ("claude_code.tools.utility", "SnipTool"),
    "brief": ("claude_code.tools.utility", "BriefTool"),
    "send_user_file": ("claude_code.tools.utility", "SendUserFileTool"),
    "suggest_background_pr": ("claude_code.tools.utility", "SuggestBackgroundPRTool"),
    "overflow_test": ("claude_code.tools.utility", "OverflowTestTool"),
    "synthetic_output": ("claude_code.tools.utility", "SyntheticOutputTool"),
    
    # System tools
    "sleep": ("claude_code.tools.system", "SleepTool"),
    "powershell": ("claude_code.tools.system", "PowerShellTool"),
    "monitor": ("claude_code.tools.system", "MonitorTool"),
    "config": ("claude_code.tools.system", "ConfigTool"),
    
    # Workflow tools
    "verify": ("claude_code.tools.workflow", "VerifyTool"),
    "enter_plan_mode": ("claude_code.tools.workflow", "EnterPlanModeTool"),
    "exit_plan_mode": ("claude_code.tools.workflow", "ExitPlanModeTool"),
    "workflow": ("claude_code.tools.workflow", "WorkflowTool"),
    "task_create": ("claude_code.tools.workflow", "TaskCreateTool"),
    "task_get": ("claude_code.tools.workflow", "TaskGetTool"),
    "task_update": ("claude_code.tools.workflow", "TaskUpdateTool"),
    "task_list": ("claude_code.tools.workflow", "TaskListTool"),
    "repl": ("claude_code.tools.workflow", "REPLTool"),
    "review_artifact": ("claude_code.tools.workflow", "ReviewArtifactTool"),
    
    # Agent tools
    "agent": ("claude_code.tools.agent", "AgentTool"),
    
    # MCP tools
    "mcp": ("claude_code.tools.mcp", "MCPTool"),
    "list_mcp_resources": ("claude_code.tools.mcp", "ListMcpResourcesTool"),
    "read_mcp_resource": ("claude_code.tools.mcp", "ReadMcpResourceTool"),
    "mcp_auth": ("claude_code.tools.mcp", "McpAuthTool"),
    "list_mcp_tools": ("claude_code.tools.mcp", "ListMcpToolsTool"),
    "list_mcp_prompts": ("claude_code.tools.mcp", "ListMcpPromptsTool"),
    
    # Skills tools
    "skill": ("claude_code.tools.skills", "SkillTool"),
    "list_skills": ("claude_code.tools.skills", "ListSkillsTool"),
    "discover_skills": ("claude_code.tools.skills", "DiscoverSkillsTool"),
    
    # Control tools
    "task_stop": ("claude_code.tools.control", "TaskStopTool"),
    "task_output": ("claude_code.tools.control", "TaskOutputTool"),
    "task_list": ("claude_code.tools.control", "TaskListTool"),
    
    # LSP tools
    "lsp": ("claude_code.tools.analysis.lsp", "LSPTool"),
    
    # Browser tools
    "browser": ("claude_code.tools.browser", "BrowserTool"),
    
    # Analysis tools
    "analyze": ("claude_code.tools.analysis.tool", "AnalyzeTool"),
    
    # Ask question tools
    "ask_user_question": ("claude_code.tools.ask_question", "AskUserQuestionTool"),
    
    # Worktree tools
    "enter_worktree": ("claude_code.tools.worktree", "EnterWorktreeTool"),
    "exit_worktree": ("claude_code.tools.worktree", "ExitWorktreeTool"),
    "list_worktrees": ("claude_code.tools.worktree", "ListWorktreesTool"),
    
    # Cron tools
    "schedule_cron": ("claude_code.tools.cron", "ScheduleCronTool"),
    "cron_create": ("claude_code.tools.cron", "CronCreateTool"),
    "cron_list": ("claude_code.tools.cron", "CronListTool"),
    "cron_delete": ("claude_code.tools.cron", "CronDeleteTool"),
    
    # Team tools
    "team_create": ("claude_code.tools.team", "TeamCreateTool"),
    "team_delete": ("claude_code.tools.team", "TeamDeleteTool"),
    "team_add_member": ("claude_code.tools.team", "TeamAddMemberTool"),
    "team_list": ("claude_code.tools.team", "TeamListTool"),
    
    # Terminal tools
    "terminal_capture": ("claude_code.tools.terminal", "TerminalCaptureTool"),
    
    # Search tools
    "tool_search": ("claude_code.tools.search", "ToolSearchTool"),
    "remote_trigger": ("claude_code.tools.search", "RemoteTriggerTool"),
    
    # Internal/feature-gated tools
    "tungsten": ("claude_code.tools.internal.tungsten", "TungstenTool"),
    "web_browser": ("claude_code.tools.internal.web_browser", "WebBrowserTool"),
    "push_notification": ("claude_code.tools.internal.push_notification", "PushNotificationTool"),
    "subscribe_pr": ("claude_code.tools.internal.subscribe_pr", "SubscribePRTool"),
    "ctx_inspect": ("claude_code.tools.internal.ctx_inspect", "CtxInspectTool"),
    "list_peers": ("claude_code.tools.internal.list_peers", "ListPeersTool"),
    "verify_plan_execution": ("claude_code.tools.internal.verify_plan_execution", "VerifyPlanExecutionTool"),
}


class LazyToolRegistry:
    """支持延迟加载的工具注册表.
    
    优点:
    - 启动时只加载必要的工具
    - 减少内存占用
    - 加快启动速度
    - 工具加载失败不影响其他工具
    
    Example:
        >>> registry = LazyToolRegistry()
        >>> tool = registry.get('bash')  # 首次访问时加载
        >>> print(tool.name)
        bash
    """
    
    def __init__(self) -> None:
        """Initialize lazy registry."""
        self._tools: dict[str, Tool] = {}
        self._aliases: dict[str, str] = {}
        self._loaded: set[str] = set()  # 记录已加载的工具
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name or alias (lazy loading).
        
        Args:
            name: Tool name or alias
            
        Returns:
            Tool instance or None if not found
        """
        # Check if already loaded
        if name in self._tools:
            return self._tools[name]
        
        # Check alias
        if name in self._aliases:
            return self.get(self._aliases[name])
        
        # Lazy load
        return self._lazy_load(name)
    
    def _lazy_load(self, name: str) -> Optional[Tool]:
        """Lazy load a tool by name.
        
        Args:
            name: Tool name
            
        Returns:
            Tool instance or None
        """
        if name in self._loaded:
            return None  # Already tried and failed
        
        if name not in TOOL_REGISTRY:
            self._loaded.add(name)
            logger.debug(f"Tool '{name}' not found in registry")
            return None
        
        module_path, class_name = TOOL_REGISTRY[name]
        
        try:
            module = importlib.import_module(module_path)
            tool_class = getattr(module, class_name)
            tool = tool_class()
            
            self._tools[name] = tool
            self._loaded.add(name)
            
            # Register aliases
            definition = tool.get_definition()
            for alias in definition.aliases:
                self._aliases[alias] = name
            
            logger.debug(f"Loaded tool: {name}")
            return tool
            
        except ImportError as e:
            logger.warning(f"Failed to import tool '{name}': {e}")
            self._loaded.add(name)
            return None
        except Exception as e:
            logger.error(f"Failed to load tool '{name}': {e}")
            self._loaded.add(name)
            return None
    
    def register(self, tool: Tool) -> None:
        """Register a tool (eager loading).
        
        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool
        
        # Register aliases
        definition = tool.get_definition()
        for alias in definition.aliases:
            self._aliases[alias] = tool.name
        
        # Mark as loaded
        self._loaded.add(tool.name)
    
    def list_all(self) -> list[Tool]:
        """List all registered tools (triggers lazy loading for all).
        
        Returns:
            List of all Tool instances
        """
        # Load all tools defined in registry
        for name in TOOL_REGISTRY:
            self.get(name)
        
        return list(self._tools.values())
    
    def get_definitions(self) -> list[dict[str, Any]]:
        """Get all tool definitions for API.
        
        Returns:
            List of tool definition dictionaries
        """
        return [tool.get_definition().__dict__ for tool in self._tools.values()]
    
    def get_names(self) -> list[str]:
        """Get all tool names.
        
        Returns:
            List of tool names
        """
        # Ensure all tools are loaded
        self.list_all()
        return list(self._tools.keys())
    
    @property
    def loaded_count(self) -> int:
        """Number of actually loaded tools."""
        return len(self._tools)
    
    @property
    def available_count(self) -> int:
        """Number of available tools in registry."""
        return len(TOOL_REGISTRY)


# 向后兼容: 默认的 ToolRegistry 类
class ToolRegistry(LazyToolRegistry):
    """Tool Registry - 向后兼容别名."""
    pass


def create_default_registry(force_eager: bool = False) -> LazyToolRegistry:
    """Create the default tool registry.
    
    Args:
        force_eager: If True, load all tools immediately (legacy behavior)
        
    Returns:
        Configured LazyToolRegistry with tools
    """
    registry = LazyToolRegistry()
    
    if force_eager:
        # Legacy eager loading mode
        registry.list_all()
    
    return registry


# 保留旧的函数签名用于向后兼容
def create_default_registry_old() -> ToolRegistry:
    """Create default registry with all tools loaded (legacy)."""
    return create_default_registry(force_eager=True)


__all__ = [
    "LazyToolRegistry",
    "ToolRegistry",
    "create_default_registry",
    "create_default_registry_old",
    "TOOL_REGISTRY",
]