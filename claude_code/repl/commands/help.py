"""
Claude Code Python - Help Command
Show help information.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from claude_code.commands.base import Command

if TYPE_CHECKING:
    from claude_code.repl import REPL


class HelpCommand(Command):
    """Show help information for Claude Code commands.
    
    Displays a table of available commands with their descriptions.
    Aliases: h, ?
    """
    
    name: str = "help"
    aliases: list[str] = ["h", "?"]
    help_text: str = "Show help information"
    
    async def execute(self, repl: REPL, args: str) -> bool:
        """Execute the help command.
        
        Args:
            repl: The REPL instance.
            args: Command arguments (unused).
            
        Returns:
            True to continue running the REPL.
        """
        help_text = """
# Claude Code Commands

## Basic Commands
| Command | Description |
|---------|-------------|
| `/help` | Show this help |
| `/clear` | Clear conversation |
| `/exit` | Exit Claude Code |
| `/quit` | Exit Claude Code |

## Session
| Command | Description |
|---------|-------------|
| `/session` | Show session info |
| `/cost` | Show costs |
| `/stats` | Show statistics |
| `/compact` | Compact conversation |

## Project
| Command | Description |
|---------|-------------|
| `/init` | Initialize CLAUDE.md |
| `/config` | Show/set config |
| `/diff` | Show git diff |
| `/status` | Show git status |
| `/doctor` | Run health check |

## Tools
| Command | Description |
|---------|-------------|
| `/tasks` | Show tasks |
| `/permissions` | Manage permissions |
| `/hooks` | List hooks |
| `/skills` | Manage skills |
| `/mcp` | Manage MCP servers |
        """
        repl.console.print(help_text)
        return True
