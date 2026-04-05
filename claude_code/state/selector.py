"""
Claude Code Python - Selector Store
State selector with memoization (inspired by Redux selectors).

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from dataclasses import dataclass, field


# Type alias for state dictionary
StateDict = dict[str, Any]
SelectorFunc = Callable[[StateDict], Any]
ObserverFunc = Callable[[StateDict, StateDict], None]


@dataclass(frozen=True, slots=True)
class SelectorCache:
    """Cache entry for a selector result.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        value: Cached selector result
        version: State version when cached
        timestamp: ISO timestamp when cached
    """
    value: Any
    version: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SelectorStore:
    """Memoized state store - inspired by Redux selector pattern.
    
    Provides efficient state management with selector memoization
    to avoid unnecessary recomputations.
    
    Attributes:
        _state: Current state dictionary
        _version: State version number for cache invalidation
        _selector_cache: Cache of selector results
        _observers: List of state change observers
    
    Example:
        >>> store = SelectorStore({"count": 0})
        >>> double_count = store.select(lambda s: s["count"] * 2)
        >>> print(double_count)  # 0
    """
    
    def __init__(self, initial_state: Optional[StateDict] = None) -> None:
        """Initialize selector store.
        
        Args:
            initial_state: Optional initial state dictionary
        """
        self._state: StateDict = initial_state or {}
        self._version: int = 0
        self._selector_cache: dict[str, SelectorCache] = {}
        self._observers: list[ObserverFunc] = []
    
    def get_state(self) -> StateDict:
        """Get complete state copy.
        
        Returns:
            Copy of the current state dictionary
        """
        return self._state.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a single state value.
        
        Args:
            key: State key to retrieve
            default: Default value if key not found
            
        Returns:
            State value or default
        """
        return self._state.get(key, default)
    
    def set_state(self, updates: StateDict) -> None:
        """Update state and notify observers.
        
        Uses shallow comparison to only notify on actual changes.
        
        Args:
            updates: Dictionary of state updates
        """
        old_state = self._state.copy()
        changed_keys: list[str] = []
        
        for key, new_value in updates.items():
            old_value = self._state.get(key)
            if old_value != new_value:
                self._state[key] = new_value
                changed_keys.append(key)
        
        if changed_keys:
            self._version += 1
            self._selector_cache.clear()
            
            new_state = self._state.copy()
            for observer in self._observers:
                try:
                    observer(old_state, new_state)
                except Exception:
                    pass
    
    def select(
        self,
        selector: SelectorFunc,
        key: Optional[str] = None,
    ) -> Any:
        """Memoized state selector.
        
        Returns cached value if state hasn't changed.
        
        Args:
            selector: Function to compute value from state
            key: Optional cache key for the selector
            
        Returns:
            Selector result (cached or newly computed)
        """
        cache_key = key or str(hash(selector))
        
        if cache_key in self._selector_cache:
            cached = self._selector_cache[cache_key]
            if cached.version == self._version:
                return cached.value
        
        value = selector(self._state)
        self._selector_cache[cache_key] = SelectorCache(
            value=value,
            version=self._version,
        )
        
        return value
    
    def subscribe(self, observer: ObserverFunc) -> Callable[[], None]:
        """Subscribe to state changes.
        
        Args:
            observer: Callback function receiving (old_state, new_state)
            
        Returns:
            Unsubscribe function
        """
        self._observers.append(observer)
        
        def unsubscribe() -> None:
            if observer in self._observers:
                self._observers.remove(observer)
        
        return unsubscribe
    
    def invalidate_cache(self, key: Optional[str] = None) -> None:
        """Invalidate selector cache.
        
        Args:
            key: Specific cache key to invalidate, or None for all
        """
        if key:
            self._selector_cache.pop(key, None)
        else:
            self._selector_cache.clear()
    
    def get_version(self) -> int:
        """Get current state version.
        
        Returns:
            State version number
        """
        return self._version


class DerivedState:
    """Derived state computed from base state.
    
    Automatically recomputes when base state changes.
    
    Attributes:
        _store: Base selector store
        _compute: Computation function
        _derived: Cached derived state
        _version: Derived state version
    """
    
    def __init__(
        self,
        store: SelectorStore,
        compute: Callable[[StateDict], StateDict],
    ) -> None:
        """Initialize derived state.
        
        Args:
            store: Base selector store to derive from
            compute: Function to compute derived state
        """
        self._store = store
        self._compute = compute
        self._derived: StateDict = {}
        self._version = 0
        
        self._subscription = store.subscribe(self._on_change)
        self._recompute()
    
    def _on_change(self, old_state: StateDict, new_state: StateDict) -> None:
        """Handle state changes by recomputing derived state."""
        self._recompute()
    
    def _recompute(self) -> None:
        """Recompute derived state from base state."""
        state = self._store.get_state()
        computed = self._compute(state)
        
        changed = False
        for key, value in computed.items():
            if self._derived.get(key) != value:
                changed = True
                self._derived[key] = value
        
        if changed:
            self._version += 1
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a derived state value.
        
        Args:
            key: State key to retrieve
            default: Default value if not found
            
        Returns:
            Derived state value or default
        """
        return self._derived.get(key, default)
    
    def get_all(self) -> StateDict:
        """Get all derived state.
        
        Returns:
            Copy of derived state dictionary
        """
        return self._derived.copy()
    
    def close(self) -> None:
        """Close and cleanup derived state."""
        self._subscription()


def create_selector_store(initial: Optional[StateDict] = None) -> SelectorStore:
    """Create a selector store.
    
    Args:
        initial: Optional initial state
        
    Returns:
        New SelectorStore instance
    """
    return SelectorStore(initial)


__all__ = [
    "SelectorStore",
    "SelectorCache",
    "DerivedState",
    "create_selector_store",
    "StateDict",
    "SelectorFunc",
    "ObserverFunc",
]
