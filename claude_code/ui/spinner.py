"""
Spinner components for Claude Code Python.

Provides loading spinners for async operations.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- frozenset for constant sets
- Proper error handling
"""

from __future__ import annotations

import sys
import time
import asyncio
from typing import Optional, Callable, Any
from dataclasses import dataclass, field
from threading import Thread


# Module-level constants using frozenset for immutability
_SPINNER_FRAMES: tuple[str, ...] = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
_DOTS_FRAMES: tuple[str, ...] = (".  ", ".. ", "...")
_ARROW_FRAMES: tuple[str, ...] = ("←", "↰", "↑", "↗", "→", "↘", "↓", "↙")

# Default constants
_DEFAULT_SPINNER_INTERVAL: float = 0.1
_DEFAULT_DOTS_INTERVAL: float = 0.3


@dataclass(frozen=True, slots=True)
class SpinnerConfig:
    """Configuration for a spinner.
    
    Using frozen=True, slots=True for immutability and memory efficiency.
    
    Attributes:
        frames: Tuple of animation frames (characters)
        interval: Time between frame updates in seconds
        color: Color name for the spinner
    """
    frames: tuple[str, ...] = field(default_factory=lambda: _SPINNER_FRAMES)
    interval: float = _DEFAULT_SPINNER_INTERVAL
    color: str = "cyan"


class Spinner:
    """A terminal spinner.
    
    Animates a spinning character while an operation is in progress.
    Uses a background thread to update the display without blocking.
    
    Attributes:
        message: Text to display with the spinner
        config: Spinner configuration
    
    Example:
        >>> with Spinner("Loading data") as spinner:
        ...     await do_some_work()
    """
    
    def __init__(
        self,
        message: str = "Loading",
        config: Optional[SpinnerConfig] = None,
    ):
        self.message = message
        self.config = config or SpinnerConfig()
        self._running = False
        self._thread: Optional[Thread] = None
        self._frame_index = 0
    
    def start(self) -> None:
        """Start the spinner.
        
        Creates and starts a daemon thread for the animation.
        """
        if self._running:
            return
        
        self._running = True
        self._thread = Thread(target=self._spin, daemon=True)
        self._thread.start()
    
    def stop(self, final_message: Optional[str] = None) -> None:
        """Stop the spinner.
        
        Args:
            final_message: Optional message to display on stop
        """
        self._running = False
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        
        if final_message:
            print(f"\r{final_message}")
        else:
            print("\r" + " " * (len(self.message) + 12), end="\r")
    
    def _spin(self) -> None:
        """Run the spinner animation (executed in thread)."""
        while self._running:
            frame = self.config.frames[self._frame_index]
            output = f"\r{frame} {self.message}"
            sys.stdout.write(output)
            sys.stdout.flush()
            
            self._frame_index = (self._frame_index + 1) % len(self.config.frames)
            time.sleep(self.config.interval)
        
        sys.stdout.write("\r" + " " * (len(self.message) + 12))
        sys.stdout.write("\r")
        sys.stdout.flush()
    
    def __enter__(self) -> "Spinner":
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.stop()


class ProgressSpinner:
    """A progress spinner with percentage.
    
    Shows progress as a percentage with a spinning indicator.
    Useful for tracking operations with known progress.
    
    Attributes:
        total: Maximum progress value
        current: Current progress value
        message: Text to display with the spinner
    
    Example:
        >>> spinner = ProgressSpinner(100, "Processing")
        >>> spinner.start()
        >>> for i in range(100):
        ...     spinner.update(i)
        ... spinner.stop()
    """
    
    def __init__(
        self,
        total: int,
        message: str = "Processing",
        config: Optional[SpinnerConfig] = None,
    ):
        self.total = total
        self._current = 0
        self.message = message
        self.config = config or SpinnerConfig()
        self._running = False
        self._thread: Optional[Thread] = None
    
    @property
    def current(self) -> int:
        """Get current progress value."""
        return self._current
    
    @current.setter
    def current(self, value: int) -> None:
        """Set current progress value."""
        self._current = value
    
    @property
    def progress(self) -> float:
        """Get current progress as a percentage.
        
        Returns:
            Progress percentage (0-100).
        """
        if self.total == 0:
            return 0
        return (self._current / self.total) * 100
    
    def update(self, current: int) -> None:
        """Update the progress.
        
        Args:
            current: New progress value (clamped to total).
        """
        self._current = min(current, self.total)
    
    def increment(self, amount: int = 1) -> None:
        """Increment the progress.
        
        Args:
            amount: Amount to increment by
        """
        self._current = min(self._current + amount, self.total)
    
    def start(self) -> None:
        """Start the progress spinner."""
        if self._running:
            return
        
        self._running = True
        self._thread = Thread(target=self._spin, daemon=True)
        self._thread.start()
    
    def stop(self, final_message: Optional[str] = None) -> None:
        """Stop the progress spinner.
        
        Args:
            final_message: Optional message to display on stop
        """
        self._running = False
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        
        if final_message:
            print(f"\r{final_message}")
        else:
            print()
    
    def _spin(self) -> None:
        """Run the progress spinner animation."""
        import itertools
        
        for i in itertools.cycle(range(len(self.config.frames))):
            if not self._running:
                break
            
            frame = self.config.frames[i]
            percent = self.progress
            bar_width = 20
            filled = int(bar_width * self._current / max(self.total, 1))
            bar = "█" * filled + "░" * (bar_width - filled)
            
            output = f"\r{frame} {self.message} [{bar}] {percent:.1f}% ({self._current}/{self.total})"
            sys.stdout.write(output)
            sys.stdout.flush()
            
            time.sleep(self.config.interval)
        
        sys.stdout.write("\r" + " " * 80)
        sys.stdout.write("\r")
        sys.stdout.flush()
    
    def __enter__(self) -> "ProgressSpinner":
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.stop()


class LoadingDots:
    """Simple loading dots animation.
    
    Shows animated dots while waiting. Useful for continuous
    background operations where progress is unknown.
    
    Attributes:
        message: Text to display with the dots
    
    Example:
        >>> with LoadingDots("Loading") as dots:
        ...     await process()
    """
    
    def __init__(self, message: str = "Loading"):
        self.message = message
        self._running = False
        self._thread: Optional[Thread] = None
    
    def start(self) -> None:
        """Start the loading dots animation."""
        if self._running:
            return
        
        self._running = True
        self._thread = Thread(target=self._animate, daemon=True)
        self._thread.start()
    
    def stop(self) -> None:
        """Stop the loading dots animation."""
        self._running = False
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.1)
        
        print("\r" + " " * 50, end="\r")
    
    def _animate(self) -> None:
        """Run the dots animation."""
        index = 0
        while self._running:
            dots = _DOTS_FRAMES[index % len(_DOTS_FRAMES)]
            output = f"\r{self.message}{dots}"
            sys.stdout.write(output)
            sys.stdout.flush()
            
            index += 1
            time.sleep(_DEFAULT_DOTS_INTERVAL)
    
    def __enter__(self) -> "LoadingDots":
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.stop()


async def with_spinner(
    coro: Any,
    message: str = "Processing",
) -> Any:
    """Execute a coroutine with a spinner.
    
    Args:
        coro: Coroutine to execute
        message: Message to display with the spinner
        
    Returns:
        Result from the coroutine.
        
    Example:
        >>> result = await with_spinner(fetch_data(), "Loading data")
    """
    spinner = Spinner(message)
    spinner.start()
    
    try:
        result = await coro
        return result
    finally:
        spinner.stop()
