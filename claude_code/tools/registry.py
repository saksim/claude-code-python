"""Tools module - Registry with default tool registration."""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any, Callable, Optional

from claude_code.tools.base import (
    Tool,
    ToolCallback,
    ToolContext,
    ToolDefinition,
    ToolInput,
    ToolProgress,
    ToolResult,
)


class ToolRegistry:
    """Registry for all available tools.

    Manages tool registration, retrieval, and aliasing.
    Supports lazy loading - tools are only instantiated when accessed.

    Attributes:
        _tools: Dictionary mapping tool names to Tool instances (or factories)
        _aliases: Dictionary mapping aliases to tool names
        _lazy_factories: Dictionary mapping tool names to factory functions
    """

    def __init__(self, lazy: bool = True) -> None:
        """Initialize tool registry.

        Args:
            lazy: If True, tools are loaded lazily on first access.
        """
        self._tools: dict[str, Tool | None] = {}
        self._aliases: dict[str, str] = {}
        self._lazy_factories: dict[str, Callable[[], Tool]] = {}
        self._lazy = lazy

    def register(self, tool: Tool) -> None:
        """Register a tool.

        Args:
            tool: Tool instance to register
        """
        self._tools[tool.name] = tool

        definition = tool.get_definition()
        for alias in definition.aliases:
            self._aliases[alias] = tool.name

    def register_lazy(self, name: str, factory: Callable[[], Tool], aliases: Optional[list[str]] = None) -> None:
        """Register a tool factory for lazy loading.

        Args:
            name: Tool name
            factory: Factory function that creates the tool instance
            aliases: Optional list of aliases for the tool
        """
        self._lazy_factories[name] = factory
        self._tools[name] = None

        if aliases:
            for alias in aliases:
                self._aliases[alias] = name

    def _resolve_tool(self, name: str) -> Optional[Tool]:
        """Resolve a lazy-loaded tool if needed.

        Args:
            name: Tool name to resolve

        Returns:
            Tool instance or None if not found
        """
        if name not in self._tools:
            return None

        tool = self._tools[name]
        if tool is not None:
            return tool

        factory = self._lazy_factories.pop(name, None)
        if factory is None:
            return None

        tool = factory()
        self._tools[name] = tool
        return tool

    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name or alias.

        Optimized lookup order:
        1. Direct name in _tools (O(1) dict lookup)
        2. Alias resolution (O(1) dict lookup)

        Args:
            name: Tool name or alias

        Returns:
            Tool instance or None if not found
        """
        tool = self._resolve_tool(name)
        if tool is not None:
            return tool

        real_name = self._aliases.get(name)
        if real_name is not None:
            return self._resolve_tool(real_name)

        return None

    def preload(self) -> None:
        """Preload all lazy tools (for eager initialization when needed)."""
        for name in list(self._lazy_factories.keys()):
            try:
                self._resolve_tool(name)
            except Exception:
                # Keep startup resilient when optional/experimental tools cannot load.
                continue

    def list_all(self) -> list[Tool]:
        """List all registered tools.

        Returns:
            List of all Tool instances
        """
        self.preload()
        return [tool for tool in self._tools.values() if tool is not None]

    def get_definitions(self) -> list[dict[str, Any]]:
        """Get all tool definitions for API.

        Optimized to avoid preloading all tools.
        Only resolves tools that have already been accessed.
        """
        return [
            tool.get_definition().__dict__
            for tool in self._tools.values()
            if tool is not None
        ]

    def get_names(self) -> list[str]:
        """Get all tool names.

        Returns:
            List of tool names
        """
        return sorted(set(self._tools.keys()) | set(self._lazy_factories.keys()))


@dataclass(frozen=True, slots=True)
class _LazyToolSpec:
    """Static lazy-registration specification for a tool."""

    name: str
    module: str
    class_name: str
    aliases: tuple[str, ...] = ()


def _create_tool_instance(module_name: str, class_name: str, tool_name: str) -> Tool:
    """Import a tool class and create an instance on-demand."""
    module = importlib.import_module(module_name)
    try:
        tool_class = getattr(module, class_name)
    except AttributeError as exc:
        raise ImportError(
            f"Tool '{tool_name}' could not be loaded: missing {class_name} in {module_name}"
        ) from exc

    tool = tool_class()
    if not isinstance(tool, Tool):
        raise TypeError(
            f"Tool '{tool_name}' loaded from {module_name}.{class_name} is not a Tool instance"
        )
    return tool


def _register_lazy_spec(registry: ToolRegistry, spec: _LazyToolSpec) -> None:
    """Register one lazy tool spec into registry."""

    def _factory(module_name: str = spec.module, class_name: str = spec.class_name, tool_name: str = spec.name) -> Tool:
        return _create_tool_instance(module_name, class_name, tool_name)

    registry.register_lazy(spec.name, _factory, list(spec.aliases))


def create_default_registry() -> ToolRegistry:
    """Create the default tool registry with lazy module imports.

    Compared with the previous implementation, this function no longer imports
    all tool modules up front. Each module is imported only when the tool is
    first resolved via ``get()`` / ``preload()``.
    """

    registry = ToolRegistry(lazy=True)

    specs: tuple[_LazyToolSpec, ...] = (
        # Builtin tools
        _LazyToolSpec("bash", "claude_code.tools.builtin.bash", "BashTool", ("shell", "sh")),
        _LazyToolSpec("read", "claude_code.tools.builtin.read", "ReadTool", ("file_read", "read_file")),
        _LazyToolSpec("write", "claude_code.tools.builtin.write", "WriteTool", ("file_write", "write_file")),
        _LazyToolSpec("edit", "claude_code.tools.builtin.edit", "EditTool", ("file_edit",)),
        _LazyToolSpec("glob", "claude_code.tools.builtin.glob", "GlobTool", ("glob_files",)),
        _LazyToolSpec("grep", "claude_code.tools.builtin.grep", "GrepTool", ("search", "find")),
        _LazyToolSpec("notebook_edit", "claude_code.tools.builtin.notebook_edit", "NotebookEditTool"),
        # Utility tools
        _LazyToolSpec("todo_write", "claude_code.tools.utility.todo", "TodoWriteTool", ("todo", "task")),
        _LazyToolSpec("web_search", "claude_code.tools.utility.web_search", "WebSearchTool", ("search_web",)),
        _LazyToolSpec("web_fetch", "claude_code.tools.utility.web_fetch", "WebFetchTool", ("fetch_url", "http_get")),
        _LazyToolSpec("send_message", "claude_code.tools.utility.send_message", "SendMessageTool"),
        _LazyToolSpec("snip", "claude_code.tools.utility.snip", "SnipTool"),
        _LazyToolSpec("brief", "claude_code.tools.utility.brief", "BriefTool"),
        _LazyToolSpec("send_user_file", "claude_code.tools.utility.send_user_file", "SendUserFileTool"),
        _LazyToolSpec("suggest_background_pr", "claude_code.tools.utility.suggest_background_pr", "SuggestBackgroundPRTool"),
        _LazyToolSpec("overflow_test", "claude_code.tools.utility.overflow_test", "OverflowTestTool"),
        _LazyToolSpec("synthetic_output", "claude_code.tools.utility.synthetic_output", "SyntheticOutputTool"),
        # System tools
        _LazyToolSpec("sleep", "claude_code.tools.system.sleep", "SleepTool"),
        _LazyToolSpec("powershell", "claude_code.tools.system.powershell", "PowerShellTool", ("ps1",)),
        _LazyToolSpec("monitor", "claude_code.tools.system.monitor", "MonitorTool"),
        _LazyToolSpec("config", "claude_code.tools.system.config", "ConfigTool"),
        # Workflow tools
        _LazyToolSpec("verify", "claude_code.tools.workflow.verify", "VerifyTool"),
        _LazyToolSpec("enter_plan_mode", "claude_code.tools.workflow.plan_mode", "EnterPlanModeTool"),
        _LazyToolSpec("exit_plan_mode", "claude_code.tools.workflow.plan_mode", "ExitPlanModeTool"),
        _LazyToolSpec("workflow", "claude_code.tools.workflow.plan_mode", "WorkflowTool"),
        _LazyToolSpec("task_create", "claude_code.tools.workflow.task_create", "TaskCreateTool"),
        _LazyToolSpec("task_get", "claude_code.tools.workflow.task_get", "TaskGetTool"),
        _LazyToolSpec("task_update", "claude_code.tools.workflow.task_update", "TaskUpdateTool"),
        _LazyToolSpec("task_list", "claude_code.tools.workflow.task_list", "TaskListTool"),
        _LazyToolSpec("task_control_list", "claude_code.tools.control", "TaskControlListTool"),
        _LazyToolSpec("repl", "claude_code.tools.workflow.repl_tool", "REPLTool"),
        _LazyToolSpec("review_artifact", "claude_code.tools.workflow.review_artifact", "ReviewArtifactTool"),
        # Agent tools
        _LazyToolSpec("agent", "claude_code.tools.agent", "AgentTool"),
        # MCP tools
        _LazyToolSpec("mcp", "claude_code.tools.mcp", "MCPTool", ("mcp_tool",)),
        _LazyToolSpec("list_mcp_resources", "claude_code.tools.mcp", "ListMcpResourcesTool"),
        _LazyToolSpec("read_mcp_resource", "claude_code.tools.mcp", "ReadMcpResourceTool"),
        _LazyToolSpec("mcp_auth", "claude_code.tools.mcp", "McpAuthTool"),
        _LazyToolSpec("list_mcp_tools", "claude_code.tools.mcp", "ListMcpToolsTool"),
        _LazyToolSpec("list_mcp_prompts", "claude_code.tools.mcp", "ListMcpPromptsTool"),
        # Skills tools
        _LazyToolSpec("skill", "claude_code.tools.skills", "SkillTool"),
        _LazyToolSpec("list_skills", "claude_code.tools.skills", "ListSkillsTool"),
        _LazyToolSpec("discover_skills", "claude_code.tools.skills", "DiscoverSkillsTool"),
        # Control tools
        _LazyToolSpec("task_stop", "claude_code.tools.control", "TaskStopTool"),
        _LazyToolSpec("task_output", "claude_code.tools.control", "TaskOutputTool"),
        # Analysis/LSP tools
        _LazyToolSpec("lsp", "claude_code.tools.analysis.lsp", "LSPTool"),
        _LazyToolSpec("browser", "claude_code.tools.browser", "BrowserTool"),
        _LazyToolSpec("analyze", "claude_code.tools.analysis.tool", "AnalyzeTool"),
        _LazyToolSpec("ask_question", "claude_code.tools.ask_question", "AskUserQuestionTool"),
        # Worktree tools
        _LazyToolSpec("enter_worktree", "claude_code.tools.worktree", "EnterWorktreeTool"),
        _LazyToolSpec("exit_worktree", "claude_code.tools.worktree", "ExitWorktreeTool"),
        _LazyToolSpec("list_worktrees", "claude_code.tools.worktree", "ListWorktreesTool"),
        # Cron tools
        _LazyToolSpec("schedule_cron", "claude_code.tools.cron", "ScheduleCronTool"),
        _LazyToolSpec("cron_create", "claude_code.tools.cron.create", "CronCreateTool"),
        _LazyToolSpec("cron_list", "claude_code.tools.cron", "CronListTool"),
        _LazyToolSpec("cron_delete", "claude_code.tools.cron", "CronDeleteTool"),
        # Team tools
        _LazyToolSpec("team_create", "claude_code.tools.team", "TeamCreateTool"),
        _LazyToolSpec("team_delete", "claude_code.tools.team", "TeamDeleteTool"),
        _LazyToolSpec("team_add_member", "claude_code.tools.team", "TeamAddMemberTool"),
        _LazyToolSpec("team_list", "claude_code.tools.team", "TeamListTool"),
        # Terminal/Search tools
        _LazyToolSpec("terminal_capture", "claude_code.tools.terminal", "TerminalCaptureTool"),
        _LazyToolSpec("tool_search", "claude_code.tools.search", "ToolSearchTool"),
        _LazyToolSpec("remote_trigger", "claude_code.tools.search", "RemoteTriggerTool"),
    )

    for spec in specs:
        _register_lazy_spec(registry, spec)

    # Note: Internal/feature-gated tools (tungsten, web_browser, push_notification,
    # subscribe_pr, ctx_inspect, list_peers, verify_plan_execution) are not registered
    # because they always return "not available" errors. They can be re-enabled
    # when their features are implemented.

    return registry


__all__ = [
    "ToolRegistry",
    "create_default_registry",
    "Tool",
    "ToolResult",
    "ToolContext",
    "ToolDefinition",
    "ToolCallback",
    "ToolInput",
    "ToolProgress",
]
