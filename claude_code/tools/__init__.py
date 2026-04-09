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
from claude_code.tools.registry import ToolRegistry, create_default_registry
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
    TaskControlListTool,
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
    TaskControlListTool,
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

# create_default_registry is now defined in registry.py and re-exported here
# to maintain backward compatibility for: from claude_code.tools import create_default_registry


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
    "TaskControlListTool",
    # Registry
    "ToolRegistry",
    "create_default_registry",
]
