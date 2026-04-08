"""
Claude Code Python - Tools Module
Modular tool system for Claude Code.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Modular design
- Tool registry pattern
"""

from __future__ import annotations

from typing import Optional, Any, TYPE_CHECKING

# Base classes - fix import path
if TYPE_CHECKING:
    from claude_code.tools.base import (
        Tool,
        ToolResult,
        ToolContext,
        ToolDefinition,
        ToolCallback,
        ToolInput,
        ToolProgress,
    )
else:
    # Runtime imports
    from claude_code.tools.base import (
        Tool as Tool,
        ToolResult,
        ToolContext,
        ToolDefinition,
        ToolCallback,
        ToolInput,
        ToolProgress,
    )

# Re-export for convenience
from claude_code.tools.registry import ToolRegistry
Tool = Tool
ToolResult = ToolResult
ToolContext = ToolContext
ToolDefinition = ToolDefinition
ToolCallback = ToolCallback
ToolInput = ToolInput
ToolProgress = ToolProgress

# Builtin tools
from claude_code.tools.builtin import (
    BashTool,
    ReadTool,
    WriteTool,
    EditTool,
    GlobTool,
    GrepTool,
    NotebookEditTool,
)

# Utility tools
from claude_code.tools.utility import (
    TodoWriteTool,
    WebSearchTool,
    WebFetchTool,
    SendMessageTool,
    SnipTool,
    BriefTool,
    SendUserFileTool,
    SuggestBackgroundPRTool,
    OverflowTestTool,
    SyntheticOutputTool,
)

# System tools
from claude_code.tools.system import (
    SleepTool,
    PowerShellTool,
    MonitorTool,
    ConfigTool,
)

# Workflow tools
from claude_code.tools.workflow import (
    VerifyTool,
    EnterPlanModeTool,
    ExitPlanModeTool,
    WorkflowTool,
    TaskCreateTool,
    TaskGetTool,
    TaskUpdateTool,
    TaskListTool,
    REPLTool,
    ReviewArtifactTool,
)

# Agent tools
from claude_code.tools.agent import AgentTool

# MCP tools
from claude_code.tools.mcp import (
    MCPTool,
    ListMcpResourcesTool,
    ReadMcpResourceTool,
    McpAuthTool,
    ListMcpToolsTool,
    ListMcpPromptsTool,
)

# Skills tools
from claude_code.tools.skills import (
    SkillTool,
    ListSkillsTool,
    DiscoverSkillsTool,
)

# Control tools
from claude_code.tools.control import (
    TaskStopTool,
    TaskOutputTool,
    TaskListTool,
)

# LSP tools
from claude_code.tools.lsp import LSPClient, LSPServerManager, get_lsp_manager
from claude_code.tools.analysis.lsp import LSPTool

# Browser tools
from claude_code.tools.browser import BrowserTool, BrowserConfig, create_browser_tool

# Analysis tools
from claude_code.tools.analysis.tool import AnalyzeTool
from claude_code.tools.analysis import CodeAnalyzer, ComplexityAnalyzer

# Ask question tools
from claude_code.tools.ask_question import AskUserQuestionTool, AskFollowUpQuestionTool

# Worktree tools
from claude_code.tools.worktree import EnterWorktreeTool, ExitWorktreeTool, ListWorktreesTool

# Cron tools
from claude_code.tools.cron import ScheduleCronTool, CronListTool, CronDeleteTool, CronCreateTool

# Team tools
from claude_code.tools.team import TeamCreateTool, TeamDeleteTool, TeamAddMemberTool, TeamListTool

# Terminal tools
from claude_code.tools.terminal import TerminalCaptureTool

# Search tools
from claude_code.tools.search import ToolSearchTool, RemoteTriggerTool

# Internal/feature-gated tools
from claude_code.tools.internal import (
    TungstenTool,
    WebBrowserTool,
    PushNotificationTool,
    SubscribePRTool,
    CtxInspectTool,
    ListPeersTool,
    VerifyPlanExecutionTool,
)


def create_default_registry() -> ToolRegistry:
    """Create the default tool registry with all built-in tools.
    
    Uses lazy loading - tools are only instantiated when first accessed.
    This significantly improves startup time by deferring object creation.
    
    Returns:
        Configured ToolRegistry with all tools registered (lazy)
    """
    registry = ToolRegistry(lazy=True)
    
    # Builtin tools - lazy registration
    registry.register_lazy("bash", lambda: BashTool(), ["shell", "sh"])
    registry.register_lazy("read", lambda: ReadTool(), ["file_read", "read_file"])
    registry.register_lazy("write", lambda: WriteTool(), ["file_write", "write_file"])
    registry.register_lazy("edit", lambda: EditTool(), ["file_edit"])
    registry.register_lazy("glob", lambda: GlobTool(), ["glob_files"])
    registry.register_lazy("grep", lambda: GrepTool(), ["search", "find"])
    registry.register_lazy("notebook_edit", lambda: NotebookEditTool())
    
    # Utility tools - lazy registration
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
    
    # System tools - lazy registration
    registry.register_lazy("sleep", lambda: SleepTool())
    registry.register_lazy("powershell", lambda: PowerShellTool(), ["ps1"])
    registry.register_lazy("monitor", lambda: MonitorTool())
    registry.register_lazy("config", lambda: ConfigTool())
    
    # Workflow tools - lazy registration
    registry.register_lazy("verify", lambda: VerifyTool())
    registry.register_lazy("enter_plan_mode", lambda: EnterPlanModeTool())
    registry.register_lazy("exit_plan_mode", lambda: ExitPlanModeTool())
    registry.register_lazy("workflow", lambda: WorkflowTool())
    registry.register_lazy("task_create", lambda: TaskCreateTool())
    registry.register_lazy("task_get", lambda: TaskGetTool())
    registry.register_lazy("task_update", lambda: TaskUpdateTool())
    registry.register_lazy("task_list", lambda: TaskListTool())
    registry.register_lazy("repl", lambda: REPLTool())
    registry.register_lazy("review_artifact", lambda: ReviewArtifactTool())
    
    # Agent tools - lazy registration
    registry.register_lazy("agent", lambda: AgentTool())
    
    # MCP tools - lazy registration
    registry.register_lazy("mcp", lambda: MCPTool(), ["mcp_tool"])
    registry.register_lazy("list_mcp_resources", lambda: ListMcpResourcesTool())
    registry.register_lazy("read_mcp_resource", lambda: ReadMcpResourceTool())
    registry.register_lazy("mcp_auth", lambda: McpAuthTool())
    registry.register_lazy("list_mcp_tools", lambda: ListMcpToolsTool())
    registry.register_lazy("list_mcp_prompts", lambda: ListMcpPromptsTool())
    
    # Skills tools - lazy registration
    registry.register_lazy("skill", lambda: SkillTool())
    registry.register_lazy("list_skills", lambda: ListSkillsTool())
    registry.register_lazy("discover_skills", lambda: DiscoverSkillsTool())
    
    # Control tools - lazy registration
    registry.register_lazy("task_stop", lambda: TaskStopTool())
    registry.register_lazy("task_output", lambda: TaskOutputTool())
    # Note: task_list already registered above
    
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
    
    # Internal/feature-gated tools
    registry.register_lazy("tungsten", lambda: TungstenTool())
    registry.register_lazy("web_browser", lambda: WebBrowserTool())
    registry.register_lazy("push_notification", lambda: PushNotificationTool())
    registry.register_lazy("subscribe_pr", lambda: SubscribePRTool())
    registry.register_lazy("ctx_inspect", lambda: CtxInspectTool())
    registry.register_lazy("list_peers", lambda: ListPeersTool())
    registry.register_lazy("verify_plan_execution", lambda: VerifyPlanExecutionTool())
    
    return registry


__all__ = [
    # Base classes
    "Tool",
    "ToolResult", 
    "ToolContext",
    "ToolDefinition",
    "ToolCallback",
    "ToolInput",
    "ToolProgress",
    # Builtin tools
    "BashTool",
    "ReadTool",
    "WriteTool",
    "EditTool",
    "GlobTool",
    "GrepTool",
    "NotebookEditTool",
    # Utility tools
    "TodoWriteTool",
    "WebSearchTool",
    "WebFetchTool",
    "SendMessageTool",
    "SnipTool",
    "BriefTool",
    "SendUserFileTool",
    "SuggestBackgroundPRTool",
    "OverflowTestTool",
    "SyntheticOutputTool",
    # System tools
    "SleepTool",
    "PowerShellTool",
    "MonitorTool",
    "ConfigTool",
    # Workflow tools
    "VerifyTool",
    "EnterPlanModeTool",
    "ExitPlanModeTool",
    "WorkflowTool",
    "TaskCreateTool",
    "TaskGetTool",
    "TaskUpdateTool",
    "REPLTool",
    "ReviewArtifactTool",
    # Agent tools
    "AgentTool",
    # MCP tools
    "MCPTool",
    "ListMcpResourcesTool",
    "ReadMcpResourceTool",
    "McpAuthTool",
    # Skills tools
    "SkillTool",
    "ListSkillsTool",
    "DiscoverSkillsTool",
    # Control tools
    "TaskStopTool",
    "TaskOutputTool",
    "TaskListTool",
    # Registry
    "ToolRegistry",
    "create_default_registry",
]
