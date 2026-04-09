"""Tools module - Registry with default tool registration."""

from typing import Optional, Any, Callable
from claude_code.tools.base import Tool, ToolDefinition, ToolContext, ToolResult, ToolInput, ToolProgress


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
        
        # Register aliases
        definition = tool.get_definition()
        for alias in definition.aliases:
            self._aliases[alias] = tool.name
    
    def register_lazy(self, name: str, factory: Callable[[], Tool], aliases: list[str] = None) -> None:
        """Register a tool factory for lazy loading.
        
        Args:
            name: Tool name
            factory: Factory function that creates the tool instance
            aliases: Optional list of aliases for the tool
        """
        self._lazy_factories[name] = factory
        self._tools[name] = None  # Placeholder until first access
        
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
            # Check if we have a lazy factory for this
            if name in self._lazy_factories:
                self._tools[name] = self._lazy_factories[name]()
                del self._lazy_factories[name]  # No longer needed
            else:
                return None
        
        # Check if it's a lazy placeholder
        tool = self._tools[name]
        if tool is None and name in self._lazy_factories:
            tool = self._lazy_factories[name]()
            self._tools[name] = tool
            del self._lazy_factories[name]
        
        return tool
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name or alias.
        
        Optimized lookup order:
        1. Direct name in _tools (O(1) dict lookup)
        2. Alias resolution (O(1) dict lookup)
        3. Lazy factory resolution (O(1) dict lookup)
        
        Args:
            name: Tool name or alias
            
        Returns:
            Tool instance or None if not found
        """
        # Direct lookup — most common case
        tool = self._tools.get(name)
        if tool is not None:
            return tool
        
        # Check if it's a lazy placeholder that needs resolution
        if name in self._lazy_factories:
            resolved = self._lazy_factories.pop(name)
            tool = resolved()
            self._tools[name] = tool
            return tool
        
        # Check aliases
        real_name = self._aliases.get(name)
        if real_name is not None:
            # Alias resolution — recurse with real name
            return self.get(real_name)
        
        return None
    
    def preload(self) -> None:
        """Preload all lazy tools (for eager initialization when needed)."""
        for name in list(self._lazy_factories.keys()):
            self._resolve_tool(name)
    
    def list_all(self) -> list[Tool]:
        """List all registered tools.
        
        Returns:
            List of all Tool instances
        """
        # Resolve all lazy tools first
        self.preload()
        return list(self._tools.values())
    
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
        return list(self._tools.keys()) + list(self._lazy_factories.keys())


def create_default_registry() -> ToolRegistry:
    """Create the default tool registry with all built-in tools.
    
    Uses lazy loading - tools are only instantiated when first accessed.
    This significantly improves startup time by deferring object creation.
    
    Returns:
        Configured ToolRegistry with all tools registered (lazy)
    """
    # Import tools here to avoid circular imports
    from claude_code.tools.builtin import (
        BashTool, ReadTool, WriteTool, EditTool,
        GlobTool, GrepTool, NotebookEditTool,
    )
    from claude_code.tools.utility import (
        TodoWriteTool, WebSearchTool, WebFetchTool, SendMessageTool,
        SnipTool, BriefTool, SendUserFileTool, SuggestBackgroundPRTool,
        OverflowTestTool, SyntheticOutputTool,
    )
    from claude_code.tools.system import (
        SleepTool, PowerShellTool, MonitorTool, ConfigTool,
    )
    from claude_code.tools.workflow import (
        VerifyTool, EnterPlanModeTool, ExitPlanModeTool, WorkflowTool,
        TaskCreateTool, TaskGetTool, TaskUpdateTool,
        REPLTool, ReviewArtifactTool,
    )
    from claude_code.tools.agent import AgentTool
    from claude_code.tools.mcp import (
        MCPTool, ListMcpResourcesTool, ReadMcpResourceTool,
        McpAuthTool, ListMcpToolsTool, ListMcpPromptsTool,
    )
    from claude_code.tools.skills import (
        SkillTool, ListSkillsTool, DiscoverSkillsTool,
    )
    from claude_code.tools.control import (
        TaskStopTool, TaskOutputTool, TaskControlListTool,
    )
    from claude_code.tools.lsp import LSPTool
    from claude_code.tools.browser import BrowserTool
    from claude_code.tools.analysis.tool import AnalyzeTool
    from claude_code.tools.ask_question import AskUserQuestionTool
    from claude_code.tools.worktree import (
        EnterWorktreeTool, ExitWorktreeTool, ListWorktreesTool,
    )
    from claude_code.tools.cron import (
        ScheduleCronTool, CronListTool, CronDeleteTool, CronCreateTool,
    )
    from claude_code.tools.team import (
        TeamCreateTool, TeamDeleteTool, TeamAddMemberTool, TeamListTool,
    )
    from claude_code.tools.terminal import TerminalCaptureTool
    from claude_code.tools.search import ToolSearchTool, RemoteTriggerTool
    
    # Workflow TaskListTool (also registered by control module under same key)
    from claude_code.tools.workflow import TaskListTool as WorkflowTaskListTool
    
    registry = ToolRegistry(lazy=True)
    
    # Builtin tools
    registry.register_lazy("bash", lambda: BashTool(), ["shell", "sh"])
    registry.register_lazy("read", lambda: ReadTool(), ["file_read", "read_file"])
    registry.register_lazy("write", lambda: WriteTool(), ["file_write", "write_file"])
    registry.register_lazy("edit", lambda: EditTool(), ["file_edit"])
    registry.register_lazy("glob", lambda: GlobTool(), ["glob_files"])
    registry.register_lazy("grep", lambda: GrepTool(), ["search", "find"])
    registry.register_lazy("notebook_edit", lambda: NotebookEditTool())
    
    # Utility tools
    registry.register_lazy("todo_write", lambda: TodoWriteTool(), ["todo", "task"])
    registry.register_lazy("web_search", lambda: WebSearchTool(), ["search_web"])
    registry.register_lazy("web_fetch", lambda: WebFetchTool(), ["fetch_url", "http_get"])
    registry.register_lazy("send_message", lambda: SendMessageTool())
    registry.register_lazy("snip", lambda: SnipTool())
    registry.register_lazy("brief", lambda: BriefTool())
    registry.register_lazy("send_user_file", lambda: SendUserFileTool())
    registry.register_lazy("suggest_background_pr", lambda: SuggestBackgroundPRTool())
    registry.register_lazy("overflow_test", lambda: OverflowTestTool())
    registry.register_lazy("synthetic_output", lambda: SyntheticOutputTool())
    
    # System tools
    registry.register_lazy("sleep", lambda: SleepTool())
    registry.register_lazy("powershell", lambda: PowerShellTool(), ["ps1"])
    registry.register_lazy("monitor", lambda: MonitorTool())
    registry.register_lazy("config", lambda: ConfigTool())
    
    # Workflow tools
    registry.register_lazy("verify", lambda: VerifyTool())
    registry.register_lazy("enter_plan_mode", lambda: EnterPlanModeTool())
    registry.register_lazy("exit_plan_mode", lambda: ExitPlanModeTool())
    registry.register_lazy("workflow", lambda: WorkflowTool())
    registry.register_lazy("task_create", lambda: TaskCreateTool())
    registry.register_lazy("task_get", lambda: TaskGetTool())
    registry.register_lazy("task_update", lambda: TaskUpdateTool())
    registry.register_lazy("task_list", lambda: WorkflowTaskListTool())
    registry.register_lazy("task_control_list", lambda: TaskControlListTool())
    registry.register_lazy("repl", lambda: REPLTool())
    registry.register_lazy("review_artifact", lambda: ReviewArtifactTool())
    
    # Agent tools
    registry.register_lazy("agent", lambda: AgentTool())
    
    # MCP tools
    registry.register_lazy("mcp", lambda: MCPTool(), ["mcp_tool"])
    registry.register_lazy("list_mcp_resources", lambda: ListMcpResourcesTool())
    registry.register_lazy("read_mcp_resource", lambda: ReadMcpResourceTool())
    registry.register_lazy("mcp_auth", lambda: McpAuthTool())
    registry.register_lazy("list_mcp_tools", lambda: ListMcpToolsTool())
    registry.register_lazy("list_mcp_prompts", lambda: ListMcpPromptsTool())
    
    # Skills tools
    registry.register_lazy("skill", lambda: SkillTool())
    registry.register_lazy("list_skills", lambda: ListSkillsTool())
    registry.register_lazy("discover_skills", lambda: DiscoverSkillsTool())
    
    # Control tools
    registry.register_lazy("task_stop", lambda: TaskStopTool())
    registry.register_lazy("task_output", lambda: TaskOutputTool())
    
    # LSP tools (may fail if dependencies not available)
    try:
        registry.register_lazy("lsp", lambda: LSPTool())
    except Exception:
        pass
    
    # Browser tools (if playwright available)
    try:
        registry.register_lazy("browser", lambda: BrowserTool())
    except Exception:
        pass
    
    # Analysis tools
    registry.register_lazy("analyze", lambda: AnalyzeTool())
    
    # Ask question tools
    registry.register_lazy("ask_question", lambda: AskUserQuestionTool())
    
    # Worktree tools
    registry.register_lazy("enter_worktree", lambda: EnterWorktreeTool())
    registry.register_lazy("exit_worktree", lambda: ExitWorktreeTool())
    registry.register_lazy("list_worktrees", lambda: ListWorktreesTool())
    
    # Cron tools
    registry.register_lazy("schedule_cron", lambda: ScheduleCronTool())
    registry.register_lazy("cron_create", lambda: CronCreateTool())
    registry.register_lazy("cron_list", lambda: CronListTool())
    registry.register_lazy("cron_delete", lambda: CronDeleteTool())
    
    # Team tools
    registry.register_lazy("team_create", lambda: TeamCreateTool())
    registry.register_lazy("team_delete", lambda: TeamDeleteTool())
    registry.register_lazy("team_add_member", lambda: TeamAddMemberTool())
    registry.register_lazy("team_list", lambda: TeamListTool())
    
    # Terminal tools (may fail if dependencies not available)
    try:
        registry.register_lazy("terminal_capture", lambda: TerminalCaptureTool())
    except Exception:
        pass
    
    # Search tools
    registry.register_lazy("tool_search", lambda: ToolSearchTool())
    registry.register_lazy("remote_trigger", lambda: RemoteTriggerTool())
    
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