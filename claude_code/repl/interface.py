import warnings
warnings.warn(f"{__name__} is deprecated and will be removed in a future version.", DeprecationWarning, stacklevel=2)
"""REPL module."""

from claude_code.repl import REPL, REPLConfig, PipeMode

__all__ = [
    "REPL",
    "REPLConfig",
    "PipeMode",
]
