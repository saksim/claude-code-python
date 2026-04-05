"""
State store for Claude Code Python.

A simple observable store for state management.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns
"""

from __future__ import annotations

from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from copy import deepcopy


@dataclass(frozen=True, slots=True)
class StateChange:
    """Represents a change in state.
    
    Attributes:
        field: Name of the field that changed.
        old_value: Previous value of the field.
        new_value: New value of the field.
    """
    field: str
    old_value: Any
    new_value: Any


@dataclass
class AppStateData:
    """Application state data class.
    
    Attributes:
        model: Model identifier.
        verbose: Enable verbose output.
        color: Enable color output.
        session_id: Current session identifier.
        conversation_id: Current conversation identifier.
        permission_mode: Permission mode setting.
        effort: Effort level (low/medium/high).
        cwd: Current working directory.
        messages: List of conversation messages.
        stats: Statistics dictionary.
    """
    model: str = "claude-sonnet-4-20250514"
    verbose: bool = False
    color: bool = True
    
    session_id: str = ""
    conversation_id: str = ""
    
    permission_mode: str = "default"
    
    effort: str = "medium"
    
    cwd: str = ""
    
    messages: list[Any] = field(default_factory=list)
    
    stats: dict[str, Any] = field(default_factory=lambda: {
        "total_tokens": 0,
        "total_cost": 0.0,
        "tool_calls": 0,
    })


class Store:
    """Observable state store.
    
    Provides get/set state with notification on changes.
    Implements the observer pattern for state updates.
    """
    
    def __init__(self, initial_state: dict[str, Any] | None = None) -> None:
        """Initialize the store.
        
        Args:
            initial_state: Optional initial state dictionary.
        """
        self._state: dict[str, Any] = initial_state or {}
        self._observers: list[Callable[[StateChange], None]] = []
        self._version: int = 0
    
    def get_state(self) -> dict[str, Any]:
        """Get a deep copy of the current state.
        
        Returns:
            Dictionary containing current state.
        """
        return deepcopy(self._state)
    
    def get_field(self, key: str, default: Any = None) -> Any:
        """Get a specific field from state.
        
        Args:
            key: The state key to retrieve.
            default: Default value if key not found.
            
        Returns:
            The field value or default.
        """
        return self._state.get(key, default)
    
    def set_state(self, updates: dict[str, Any]) -> None:
        """Update state with a dictionary of changes.
        
        Notifies all observers of changed fields.
        
        Args:
            updates: Dictionary of field updates.
        """
        for key, new_value in updates.items():
            old_value = self._state.get(key)
            
            if old_value != new_value:
                self._state[key] = deepcopy(new_value)
                self._version += 1
                
                change = StateChange(
                    field=key,
                    old_value=old_value,
                    new_value=new_value,
                )
                
                for observer in self._observers:
                    observer(change)
    
    def set_field(self, key: str, value: Any) -> None:
        """Set a single field in state.
        
        Args:
            key: The state key to set.
            value: Value to set.
        """
        self.set_state({key: value})
    
    def subscribe(self, observer: Callable[[StateChange], None]) -> Callable[[], None]:
        """Subscribe to state changes.
        
        Args:
            observer: Callback function to receive state changes.
            
        Returns:
            Unsubscribe function.
        """
        self._observers.append(observer)
        
        def unsubscribe() -> None:
            if observer in self._observers:
                self._observers.remove(observer)
        
        return unsubscribe
    
    @property
    def version(self) -> int:
        """Get current store version.
        
        Returns:
            Version number that increments on each state change.
        """
        return self._version


class SelectorStore(Store):
    """Store with selector support.
    
    Allows selecting slices of state with memoization.
    """
    
    def __init__(self, initial_state: dict[str, Any] | None = None) -> None:
        """Initialize selector store.
        
        Args:
            initial_state: Optional initial state dictionary.
        """
        super().__init__(initial_state)
        self._selectors: dict[str, Callable[[dict[str, Any]], Any]] = {}
        self._selector_cache: dict[str, tuple[Any, int]] = {}
    
    def select(
        self,
        selector: Callable[[dict[str, Any]], Any],
        key: str | None = None,
    ) -> Any:
        """Select a slice of state with memoization.
        
        Args:
            selector: Function to extract slice from state.
            key: Optional cache key for the selector.
            
        Returns:
            Selected value, memoized until state changes.
        """
        cache_key = key or str(hash(selector))
        
        state = self.get_state()
        value = selector(state)
        
        if cache_key in self._selector_cache:
            cached_value, cached_version = self._selector_cache[cache_key]
            if cached_version == self._version:
                return cached_value
        
        self._selector_cache[cache_key] = (value, self._version)
        
        return value
    
    def invalidate_selectors(self) -> None:
        """Invalidate all selector caches."""
        self._selector_cache.clear()


def create_store(initial_state: dict[str, Any] | None = None) -> SelectorStore:
    """Create a new store with optional initial state.
    
    Args:
        initial_state: Optional initial state dictionary.
        
    Returns:
        A new SelectorStore instance.
    """
    return SelectorStore(initial_state)


_store: SelectorStore | None = None


def get_store() -> SelectorStore:
    """Get the global store instance.
    
    Returns:
        The global SelectorStore singleton.
    """
    global _store
    if _store is None:
        _store = create_store()
    return _store


def set_store(store: SelectorStore) -> None:
    """Set the global store instance.
    
    Args:
        store: The SelectorStore to use globally.
    """
    global _store
    _store = store
