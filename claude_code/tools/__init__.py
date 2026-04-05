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
from claude_code.tools.cron import ScheduleCronTool, CronListTool, CronDeleteTool

# Team tools
from claude_code.tools.team import TeamCreateTool, TeamDeleteTool, TeamAddMemberTool, TeamListTool

# Terminal tools
from claude_code.tools.terminal import TerminalCaptureTool

# Search tools
from claude_code.tools.search import ToolSearchTool, RemoteTriggerTool


class ToolRegistry:
    """Registry for all available tools.
    
    Manages tool registration, retrieval, and aliasing.
    
    Attributes:
        _tools: Dictionary mapping tool names to Tool instances
        _aliases: Dictionary mapping aliases to tool names
    """
    
    def __init__(self) -> None:
        """Initialize empty tool registry."""
        self._tools: dict[str, Tool] = {}
        self._aliases: dict[str, str] = {}
    
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
    
    def get(self, name: str) -> Optional[Tool]:
        """Get a tool by name or alias.
        
        Args:
            name: Tool name or alias
            
        Returns:
            Tool instance or None if not found
        """
        if name in self._tools:
            return self._tools[name]
        
        if name in self._aliases:
            return self._tools.get(self._aliases[name])
        
        return None
    
    def list_all(self) -> list[Tool]:
        """List all registered tools.
        
        Returns:
            List of all Tool instances
        """
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
        return list(self._tools.keys())


def create_default_registry() -> ToolRegistry:
    """Create the default tool registry with all built-in tools.
    
    Returns:
        Configured ToolRegistry with all tools registered
    """
    registry = ToolRegistry()
    
    # Builtin tools
    registry.register(BashTool())
    registry.register(ReadTool())
    registry.register(WriteTool())
    registry.register(EditTool())
    registry.register(GlobTool())
    registry.register(GrepTool())
    registry.register(NotebookEditTool())
    
    # Utility tools
    registry.register(TodoWriteTool())
    registry.register(WebSearchTool())
    registry.register(WebFetchTool())
    registry.register(SendMessageTool())
    registry.register(SnipTool())
    registry.register(BriefTool())
    
    # System tools
    registry.register(SleepTool())
    registry.register(PowerShellTool())
    registry.register(MonitorTool())
    registry.register(ConfigTool())
    
    # Workflow tools
    registry.register(VerifyTool())
    registry.register(EnterPlanModeTool())
    registry.register(ExitPlanModeTool())
    registry.register(WorkflowTool())
    registry.register(TaskCreateTool())
    registry.register(TaskGetTool())
    registry.register(TaskUpdateTool())
    registry.register(REPLTool())
    registry.register(ReviewArtifactTool())
    
    # Agent tools
    registry.register(AgentTool())
    
    # MCP tools
    registry.register(ListMcpResourcesTool())
    registry.register(ReadMcpResourceTool())
    registry.register(McpAuthTool())
    registry.register(ListMcpToolsTool())
    registry.register(ListMcpPromptsTool())
    
    # Skills tools
    registry.register(SkillTool())
    registry.register(ListSkillsTool())
    registry.register(DiscoverSkillsTool())
    
    # Control tools
    registry.register(TaskStopTool())
    registry.register(TaskOutputTool())
    registry.register(TaskListTool())
    
    # Browser tools (if playwright available)
    try:
        registry.register(BrowserTool())
    except Exception:
        pass
    
    # Analysis tools
    registry.register(AnalyzeTool())
    
    # Ask question tools
    registry.register(AskUserQuestionTool())
    
    # Worktree tools
    registry.register(EnterWorktreeTool())
    registry.register(ExitWorktreeTool())
    registry.register(ListWorktreesTool())
    
    # Cron tools
    registry.register(ScheduleCronTool())
    registry.register(CronListTool())
    registry.register(CronDeleteTool())
    
    # Team tools
    registry.register(TeamCreateTool())
    registry.register(TeamDeleteTool())
    registry.register(TeamListTool())
    
    # Terminal tools
    try:
        registry.register(TerminalCaptureTool())
    except Exception:
        pass
    
    # Search tools
    registry.register(ToolSearchTool())
    registry.register(RemoteTriggerTool())
    
    return registry


# Re-export everything for convenience
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
