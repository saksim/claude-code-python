"""
Claude Code Python - Cost Command
Show session costs.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from claude_code.commands.base import Command

if TYPE_CHECKING:
    from claude_code.repl import REPL


class CostCommand(Command):
    """Show session token costs and pricing.
    
    Displays a table with input/output tokens and estimated cost.
    """
    
    name: str = "cost"
    aliases: list[str] = []
    help_text: str = "Show session cost"
    
    async def execute(self, repl: REPL, args: str) -> bool:
        """Execute the cost command.
        
        Args:
            repl: The REPL instance.
            args: Command arguments (unused).
            
        Returns:
            True to continue running the REPL.
        """
        from rich.table import Table
        
        stats: dict[str, Any] = repl.engine.get_statistics()
        cost = stats.get("total_cost_usd", 0)
        
        table = Table(title="Session Costs")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Input Tokens", str(stats.get("total_input_tokens", 0)))
        table.add_row("Output Tokens", str(stats.get("total_output_tokens", 0)))
        table.add_row("Estimated Cost", f"${cost:.4f}")
        
        repl.console.print(table)
        return True
