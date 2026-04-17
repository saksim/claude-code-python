"""Claude Code Python - Tools package exports.

Tool class exports are resolved lazily to reduce startup overhead.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from claude_code.tools.base import (
    Tool,
    ToolCallback,
    ToolContext,
    ToolDefinition,
    ToolInput,
    ToolProgress,
    ToolResult,
)
from claude_code.tools.registry import ToolRegistry, create_default_registry

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # Builtin
    "BashTool": ("claude_code.tools.builtin", "BashTool"),
    "ReadTool": ("claude_code.tools.builtin", "ReadTool"),
    "WriteTool": ("claude_code.tools.builtin", "WriteTool"),
    "EditTool": ("claude_code.tools.builtin", "EditTool"),
    "GlobTool": ("claude_code.tools.builtin", "GlobTool"),
    "GrepTool": ("claude_code.tools.builtin", "GrepTool"),
    "NotebookEditTool": ("claude_code.tools.builtin", "NotebookEditTool"),
    # Utility
    "TodoWriteTool": ("claude_code.tools.utility", "TodoWriteTool"),
    "WebSearchTool": ("claude_code.tools.utility", "WebSearchTool"),
    "WebFetchTool": ("claude_code.tools.utility", "WebFetchTool"),
    "SendMessageTool": ("claude_code.tools.utility", "SendMessageTool"),
    "SnipTool": ("claude_code.tools.utility", "SnipTool"),
    "BriefTool": ("claude_code.tools.utility", "BriefTool"),
    "SendUserFileTool": ("claude_code.tools.utility", "SendUserFileTool"),
    "SuggestBackgroundPRTool": ("claude_code.tools.utility", "SuggestBackgroundPRTool"),
    "OverflowTestTool": ("claude_code.tools.utility", "OverflowTestTool"),
    "SyntheticOutputTool": ("claude_code.tools.utility", "SyntheticOutputTool"),
    # System
    "SleepTool": ("claude_code.tools.system", "SleepTool"),
    "PowerShellTool": ("claude_code.tools.system", "PowerShellTool"),
    "MonitorTool": ("claude_code.tools.system", "MonitorTool"),
    "ConfigTool": ("claude_code.tools.system", "ConfigTool"),
    # Workflow
    "VerifyTool": ("claude_code.tools.workflow", "VerifyTool"),
    "EnterPlanModeTool": ("claude_code.tools.workflow", "EnterPlanModeTool"),
    "ExitPlanModeTool": ("claude_code.tools.workflow", "ExitPlanModeTool"),
    "WorkflowTool": ("claude_code.tools.workflow", "WorkflowTool"),
    "TaskCreateTool": ("claude_code.tools.workflow", "TaskCreateTool"),
    "TaskGetTool": ("claude_code.tools.workflow", "TaskGetTool"),
    "TaskListTool": ("claude_code.tools.workflow", "TaskListTool"),
    "TaskUpdateTool": ("claude_code.tools.workflow", "TaskUpdateTool"),
    "REPLTool": ("claude_code.tools.workflow", "REPLTool"),
    "ReviewArtifactTool": ("claude_code.tools.workflow", "ReviewArtifactTool"),
    # Agent
    "AgentTool": ("claude_code.tools.agent", "AgentTool"),
    # MCP
    "MCPTool": ("claude_code.tools.mcp", "MCPTool"),
    "ListMcpResourcesTool": ("claude_code.tools.mcp", "ListMcpResourcesTool"),
    "ReadMcpResourceTool": ("claude_code.tools.mcp", "ReadMcpResourceTool"),
    "McpAuthTool": ("claude_code.tools.mcp", "McpAuthTool"),
    "ListMcpToolsTool": ("claude_code.tools.mcp", "ListMcpToolsTool"),
    "ListMcpPromptsTool": ("claude_code.tools.mcp", "ListMcpPromptsTool"),
    # Skills
    "SkillTool": ("claude_code.tools.skills", "SkillTool"),
    "ListSkillsTool": ("claude_code.tools.skills", "ListSkillsTool"),
    "DiscoverSkillsTool": ("claude_code.tools.skills", "DiscoverSkillsTool"),
    # Control
    "TaskStopTool": ("claude_code.tools.control", "TaskStopTool"),
    "TaskOutputTool": ("claude_code.tools.control", "TaskOutputTool"),
    "TaskControlListTool": ("claude_code.tools.control", "TaskControlListTool"),
    # LSP
    "LSPClient": ("claude_code.tools.lsp", "LSPClient"),
    "LSPServerManager": ("claude_code.tools.lsp", "LSPServerManager"),
    "get_lsp_manager": ("claude_code.tools.lsp", "get_lsp_manager"),
    "LSPTool": ("claude_code.tools.analysis.lsp", "LSPTool"),
    # Browser
    "BrowserTool": ("claude_code.tools.browser", "BrowserTool"),
    "BrowserConfig": ("claude_code.tools.browser", "BrowserConfig"),
    "create_browser_tool": ("claude_code.tools.browser", "create_browser_tool"),
    # Analysis
    "AnalyzeTool": ("claude_code.tools.analysis.tool", "AnalyzeTool"),
    "CodeAnalyzer": ("claude_code.tools.analysis", "CodeAnalyzer"),
    "ComplexityAnalyzer": ("claude_code.tools.analysis", "ComplexityAnalyzer"),
    # Ask question
    "AskUserQuestionTool": ("claude_code.tools.ask_question", "AskUserQuestionTool"),
    "AskFollowUpQuestionTool": ("claude_code.tools.ask_question", "AskFollowUpQuestionTool"),
    # Worktree
    "EnterWorktreeTool": ("claude_code.tools.worktree", "EnterWorktreeTool"),
    "ExitWorktreeTool": ("claude_code.tools.worktree", "ExitWorktreeTool"),
    "ListWorktreesTool": ("claude_code.tools.worktree", "ListWorktreesTool"),
    # Cron
    "ScheduleCronTool": ("claude_code.tools.cron", "ScheduleCronTool"),
    "CronListTool": ("claude_code.tools.cron", "CronListTool"),
    "CronDeleteTool": ("claude_code.tools.cron", "CronDeleteTool"),
    "CronCreateTool": ("claude_code.tools.cron", "CronCreateTool"),
    # Team
    "TeamCreateTool": ("claude_code.tools.team", "TeamCreateTool"),
    "TeamDeleteTool": ("claude_code.tools.team", "TeamDeleteTool"),
    "TeamAddMemberTool": ("claude_code.tools.team", "TeamAddMemberTool"),
    "TeamListTool": ("claude_code.tools.team", "TeamListTool"),
    # Terminal
    "TerminalCaptureTool": ("claude_code.tools.terminal", "TerminalCaptureTool"),
    # Search
    "ToolSearchTool": ("claude_code.tools.search", "ToolSearchTool"),
    "RemoteTriggerTool": ("claude_code.tools.search", "RemoteTriggerTool"),
    # Internal
    "TungstenTool": ("claude_code.tools.internal", "TungstenTool"),
    "WebBrowserTool": ("claude_code.tools.internal", "WebBrowserTool"),
    "PushNotificationTool": ("claude_code.tools.internal", "PushNotificationTool"),
    "SubscribePRTool": ("claude_code.tools.internal", "SubscribePRTool"),
    "CtxInspectTool": ("claude_code.tools.internal", "CtxInspectTool"),
    "ListPeersTool": ("claude_code.tools.internal", "ListPeersTool"),
    "VerifyPlanExecutionTool": ("claude_code.tools.internal", "VerifyPlanExecutionTool"),
}

__all__ = [
    "Tool",
    "ToolResult",
    "ToolContext",
    "ToolDefinition",
    "ToolCallback",
    "ToolInput",
    "ToolProgress",
    "ToolRegistry",
    "create_default_registry",
    *_LAZY_EXPORTS.keys(),
]


def __getattr__(name: str) -> Any:
    if name not in _LAZY_EXPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _LAZY_EXPORTS[name]
    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
