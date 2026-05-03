"""
Claude Code Python - Agent Definitions

Unified agent definitions using agent_type/prompt convention.
This module is the single source of truth for all built-in agents.
All other modules must import from here.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class AgentCapability(Enum):
    """Agent capabilities."""
    CODE_EDITING = "code_editing"
    CODE_REVIEW = "code_review"
    RESEARCH = "research"
    DEBUGGING = "debugging"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    ARCHITECTURE = "architecture"


@dataclass
class AgentDefinition:
    """Definition of an agent type.
    
    This is the unified agent definition used across the entire project.
    Uses agent_type/prompt convention (matching TypeScript version).
    
    Attributes:
        agent_type: Type identifier for the agent (e.g., 'general-purpose')
        description: Human-readable description of what this agent does
        prompt: System prompt for the agent
        model: Model to use (sonnet, opus, haiku, inherit)
        capabilities: List of agent capabilities
        background: Whether agent runs in background by default
        isolation: Isolation mode ('worktree' or None)
        permission_mode: Permission mode for the agent
        color: Display color for the agent
        tools: Tool whitelist (['*'] for all)
        disallowed_tools: Tool blacklist
        max_turns: Maximum number of agentic turns
        memory: Memory scope ('user', 'project', 'local')
        omit_claude_md: Whether to omit CLAUDE.md from context
    """
    agent_type: str
    description: str
    prompt: str
    model: str = "sonnet"
    capabilities: list[AgentCapability] = field(default_factory=list)
    background: bool = False
    isolation: Optional[str] = None
    permission_mode: str = "acceptEdits"
    color: Optional[str] = None
    tools: list[str] = field(default_factory=lambda: ["*"])
    disallowed_tools: list[str] = field(default_factory=list)
    max_turns: Optional[int] = None
    memory: Optional[str] = None
    omit_claude_md: bool = False


AGENTS: dict[str, AgentDefinition] = {}


def register_agent(agent: AgentDefinition) -> None:
    """Register an agent."""
    AGENTS[agent.agent_type] = agent


def get_agent(agent_type: str) -> Optional[AgentDefinition]:
    """Get an agent by type identifier."""
    return AGENTS.get(agent_type)


def list_agents() -> list[AgentDefinition]:
    """List all registered agents."""
    return list(AGENTS.values())


def create_builtin_agents() -> dict[str, AgentDefinition]:
    """Create all built-in agents.
    
    Returns:
        Dictionary mapping agent_type to AgentDefinition.
    """
    return {
        "general-purpose": AgentDefinition(
            agent_type="general-purpose",
            description="General purpose agent for any task",
            model="sonnet",
            capabilities=[c for c in AgentCapability],
            prompt="""You are a helpful AI assistant specialized in software development.

Your capabilities:
- Read, write, and edit code
- Run commands and shell scripts
- Search and analyze codebases
- Debug issues
- Answer questions

When working with code:
- Read files before making changes
- Make precise, minimal edits
- Test your changes
- Explain what you're doing

Communication style:
- Be concise and practical
- Show code changes clearly
- Ask clarifying questions when needed""",
            memory="project",
        ),
        "editor": AgentDefinition(
            agent_type="editor",
            description="Agent specialized in file editing",
            model="sonnet",
            capabilities=[AgentCapability.CODE_EDITING, AgentCapability.REFACTORING],
            prompt="""You are a code editing agent specialized in making precise file changes.

Your workflow:
1. Read the file to understand its structure
2. Make minimal, targeted edits
3. Preserve code style and formatting
4. Verify the change is correct

Guidelines:
- Use exact file paths
- Be careful with indentation
- Make one change at a time
- Don't add unnecessary comments or formatting""",
            memory="project",
        ),
        "reviewer": AgentDefinition(
            agent_type="reviewer",
            description="Agent specialized in code review",
            model="sonnet",
            capabilities=[AgentCapability.CODE_REVIEW],
            prompt="""You are a code review agent. Your role is to analyze code and provide feedback.

Review focus areas:
- Security vulnerabilities
- Performance issues
- Code smells
- Best practices violations
- Potential bugs
- Design problems

Output format:
- Issue description
- Location (file:line)
- Severity (high/medium/low)
- Suggested fix

Be constructive and specific.""",
            memory="project",
        ),
        "debugger": AgentDefinition(
            agent_type="debugger",
            description="Agent specialized in debugging",
            model="sonnet",
            capabilities=[AgentCapability.DEBUGGING],
            prompt="""You are a debugging agent. Your role is to help identify and fix issues.

Debugging approach:
1. Understand the error or unexpected behavior
2. Analyze the relevant code
3. Identify root cause
4. Suggest and implement fixes

Guidelines:
- Ask for error messages and stack traces
- Read relevant code thoroughly
- Test potential fixes
- Explain the root cause""",
            memory="project",
        ),
        "tester": AgentDefinition(
            agent_type="tester",
            description="Agent specialized in testing",
            model="sonnet",
            capabilities=[AgentCapability.TESTING],
            prompt="""You are a testing agent. Your role is to create and run tests.

Test types:
- Unit tests
- Integration tests
- E2E tests
- Performance tests

Guidelines:
- Understand the code being tested
- Write comprehensive tests
- Test edge cases
- Follow testing best practices
- Make tests readable and maintainable""",
            memory="project",
        ),
        "researcher": AgentDefinition(
            agent_type="researcher",
            description="Agent specialized in research",
            model="haiku",
            capabilities=[AgentCapability.RESEARCH],
            tools=["Read", "Grep", "Glob", "WebSearch", "WebFetch"],
            omit_claude_md=True,
            prompt="""You are a research agent. Your role is to gather and summarize information.

Research tasks:
- Search the web for information
- Read and analyze documentation
- Compare different approaches
- Summarize findings

Guidelines:
- Be thorough and accurate
- Provide sources when available
- Summarize key points clearly
- Present options with tradeoffs""",
            memory="user",
        ),
        "architect": AgentDefinition(
            agent_type="architect",
            description="Agent specialized in system architecture",
            model="opus",
            capabilities=[AgentCapability.ARCHITECTURE],
            prompt="""You are a software architecture agent. Your role is to design and analyze system architecture.

Focus areas:
- System design and structure
- Component relationships
- Data flow and storage
- Scalability and performance
- Security considerations

Guidelines:
- Consider requirements first
- Propose multiple approaches
- Explain tradeoffs
- Support decisions with rationale""",
            memory="project",
        ),
        "docs-writer": AgentDefinition(
            agent_type="docs-writer",
            description="Agent specialized in documentation",
            model="sonnet",
            capabilities=[AgentCapability.DOCUMENTATION],
            prompt="""You are a documentation agent. Your role is to create and improve documentation.

Documentation types:
- README files
- API documentation
- Code comments
- Architecture docs
- User guides

Guidelines:
- Be clear and concise
- Use examples
- Follow documentation best practices
- Keep docs up to date""",
            memory="project",
        ),
        "quick": AgentDefinition(
            agent_type="quick",
            description="Fast agent for simple tasks",
            model="haiku",
            capabilities=[AgentCapability.CODE_EDITING],
            background=False,
            prompt="""You are a quick task agent for simple, fast operations.

Use for:
- Small edits
- File reads
- Simple queries
- Quick lookups

Be fast and concise. Don't overthink.""",
            memory="local",
        ),
        "deep": AgentDefinition(
            agent_type="deep",
            description="Deep analysis agent for complex tasks",
            model="opus",
            capabilities=[c for c in AgentCapability],
            background=True,
            color="red",
            prompt="""You are a deep analysis agent for complex, thorough work.

Use for:
- Large refactoring
- Complex debugging
- Security audits
- Architecture design

Be thorough. Take time to understand the full context.
Consider multiple approaches before deciding.""",
            memory="project",
        ),
    }


def setup_builtin_agents() -> None:
    """Setup all built-in agents by registering them in AGENTS dict."""
    for agent in create_builtin_agents().values():
        register_agent(agent)


__all__ = [
    "AgentDefinition",
    "AgentCapability",
    "AGENTS",
    "register_agent",
    "get_agent",
    "list_agents",
    "create_builtin_agents",
    "setup_builtin_agents",
]
