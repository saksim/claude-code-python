"""
Claude Code Python - Cost and Stats Commands

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from claude_code.commands.base import Command, CommandContext, CommandResult, CommandType
from claude_code.services.cost_tracker import CostTracker


class CostCommand(Command):
    """Show conversation token costs and pricing.
    
    Displays input/output token counts and estimated cost
    based on the current model's pricing.
    """
    
    def __init__(self) -> None:
        """Initialize the cost command."""
        super().__init__(
            name="cost",
            description="Show conversation costs",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the cost command.
        
        Args:
            args: Command arguments (unused for cost command).
            context: The command execution context.
            
        Returns:
            CommandResult with cost information.
        """
        try:
            tracker = CostTracker()
            stats = tracker.get_stats()
            
            lines: list[str] = ["# Conversation Cost\n"]
            lines.append(f"Total Input Tokens: {stats.get('input_tokens', 0):,}")
            lines.append(f"Total Output Tokens: {stats.get('output_tokens', 0):,}")
            lines.append(f"Total Tokens: {stats.get('total_tokens', 0):,}")
            lines.append(f"\nEstimated Cost: ${stats.get('cost', 0):.4f}")
            
            return CommandResult(content="\n".join(lines))
        except Exception as e:
            return CommandResult(content=f"Cost tracking not available: {e}")


class StatsCommand(Command):
    """Show conversation statistics.
    
    Displays session information including message count,
    tool calls, tokens, and estimated cost.
    """
    
    def __init__(self) -> None:
        """Initialize the stats command."""
        super().__init__(
            name="stats",
            description="Show conversation statistics",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the stats command.
        
        Args:
            args: Command arguments (unused for stats command).
            context: The command execution context.
            
        Returns:
            CommandResult with session statistics.
        """
        lines: list[str] = ["# Session Statistics\n"]
        
        if context.session:
            lines.append(f"Session ID: {context.session.get('id', 'N/A')}")
            lines.append(f"Messages: {context.session.get('message_count', 0)}")
            lines.append(f"Tool Calls: {context.session.get('tool_call_count', 0)}")
        
        from claude_code.services.cost_tracker import CostTracker
        tracker = CostTracker()
        stats = tracker.get_stats()
        
        lines.append(f"\nTokens: {stats.get('total_tokens', 0):,}")
        lines.append(f"Cost: ${stats.get('cost', 0):.4f}")
        
        return CommandResult(content="\n".join(lines))


class UsageCommand(Command):
    """Show detailed usage report.
    
    Displays comprehensive usage information including
    token breakdown, cost estimates, and model configuration.
    """
    
    def __init__(self) -> None:
        """Initialize the usage command."""
        super().__init__(
            name="usage",
            description="Show detailed usage",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the usage command.
        
        Args:
            args: Command arguments (unused for usage command).
            context: The command execution context.
            
        Returns:
            CommandResult with detailed usage report.
        """
        from claude_code.services.cost_tracker import CostTracker
        from claude_code.services.token_estimation import TokenEstimator
        
        tracker = CostTracker()
        estimator = TokenEstimator()
        
        stats = tracker.get_stats()
        
        lines: list[str] = ["# Usage Report\n"]
        
        lines.append("\n## Tokens")
        lines.append(f"Input: {stats.get('input_tokens', 0):,}")
        lines.append(f"Output: {stats.get('output_tokens', 0):,}")
        lines.append(f"Total: {stats.get('total_tokens', 0):,}")
        
        lines.append("\n## Cost")
        lines.append(f"Estimated: ${stats.get('cost', 0):.4f}")
        
        lines.append("\n## Model")
        from claude_code.config import get_config
        config = get_config()
        lines.append(f"Model: {config.model}")
        
        return CommandResult(content="\n".join(lines))


class ExtraUsageCommand(Command):
    """Show extra usage information from cloud services.
    
    Provides extended usage metrics and billing information
    from cloud provider services.
    """
    
    def __init__(self) -> None:
        """Initialize the extra usage command."""
        super().__init__(
            name="extra-usage",
            description="Show extra usage information",
            command_type=CommandType.LOCAL,
        )
    
    async def execute(self, args: str, context: CommandContext) -> CommandResult:
        """Execute the extra usage command.
        
        Args:
            args: Command arguments (unused for extra usage command).
            context: The command execution context.
            
        Returns:
            CommandResult with extra usage information.
        """
        return CommandResult(content="""# Extra Usage

No additional usage data available.

This command shows extended usage metrics from cloud services.""")


def create_cost_command() -> CostCommand:
    return CostCommand()

def create_stats_command() -> StatsCommand:
    return StatsCommand()

def create_usage_command() -> UsageCommand:
    return UsageCommand()


__all__ = [
    "CostCommand", "StatsCommand", "UsageCommand", "ExtraUsageCommand",
    "create_cost_command", "create_stats_command", "create_usage_command",
]
