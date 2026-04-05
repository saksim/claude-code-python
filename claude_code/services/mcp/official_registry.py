"""
MCP Official Registry for Claude Code Python.

Fetches and caches the official MCP server registry from Anthropic's API.
This allows users to discover and connect to official MCP servers.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Frozen dataclasses for immutability
"""

from __future__ import annotations

import os
from typing import Any, Optional
from dataclasses import dataclass, field


OFFICIAL_REGISTRY_URL = "https://api.anthropic.com/mcp-registry/v0/servers"
REGISTRY_PARAMS = "?version=latest&visibility=commercial"


@dataclass(frozen=True, slots=True)
class MCPOfficialServer:
    """Represents an official MCP server from the registry.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        name: Server name identifier
        description: Human-readable description
        url: Server URL
    """
    name: str
    description: str
    url: str


class MCPOfficialRegistry:
    """Fetches and caches the official MCP server registry.
    
    This class provides access to the official MCP servers published
    by Anthropic. The registry is fetched on first access and cached
    for subsequent queries.
    
    Attributes:
        _servers: Cached set of official server URLs
        _all_servers: Cached list of server details
    
    Example:
        >>> registry = MCPOfficialRegistry()
        >>> await registry.prefetch()
        >>> if registry.is_official("https://api.anthropic.com/mcp-server"):
        ...     print("Official MCP server!")
    """
    
    def __init__(self) -> None:
        """Initialize the registry."""
        self._servers: Optional[set[str]] = None
        self._all_servers: list[MCPOfficialServer] = []
    
    @staticmethod
    def _normalize_url(url: str) -> Optional[str]:
        """Normalize URL by removing query string and trailing slash.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL string or None if invalid
        """
        try:
            from urllib.parse import urlparse, urlunparse
            
            parsed = urlparse(url)
            # Clear query string and trailing slash
            normalized = parsed._replace(query="", path=parsed.path.rstrip("/"))
            return urlunparse(normalized)
        except Exception:
            return None
    
    async def prefetch(self) -> None:
        """Prefetch the official MCP registry.
        
        Fetches the registry from Anthropic's API and caches the results.
        This is a fire-and-forget operation - errors are silently ignored.
        """
        # Check if non-essential traffic is disabled
        if os.environ.get("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC"):
            return
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{OFFICIAL_REGISTRY_URL}{REGISTRY_PARAMS}",
                    headers={
                        "Accept": "application/json",
                    }
                )
                response.raise_for_status()
                
                data = response.json()
                
                urls: set[str] = set()
                servers: list[MCPOfficialServer] = []
                
                for entry in data.get("servers", []):
                    server_data = entry.get("server", {})
                    name = entry.get("name", "unknown")
                    description = entry.get("description", "")
                    
                    for remote in server_data.get("remotes", []):
                        url = remote.get("url", "")
                        if not url:
                            continue
                        
                        normalized = self._normalize_url(url)
                        if normalized:
                            urls.add(normalized)
                            servers.append(MCPOfficialServer(
                                name=name,
                                description=description,
                                url=url,
                            ))
                
                self._servers = urls
                self._all_servers = servers
                
        except Exception:
            # Fire-and-forget - silently ignore errors
            pass
    
    def is_official(self, url: str) -> bool:
        """Check if a URL is an official MCP server.
        
        Args:
            url: URL to check (will be normalized)
            
        Returns:
            True if URL is in the official registry, False otherwise
        """
        if self._servers is None:
            return False
        
        normalized = self._normalize_url(url)
        if normalized is None:
            return False
        
        return normalized in self._servers
    
    @property
    def servers(self) -> list[MCPOfficialServer]:
        """Get list of all official MCP servers.
        
        Returns:
            List of MCPOfficialServer objects
        """
        return self._all_servers
    
    def reset(self) -> None:
        """Reset the registry for testing purposes."""
        self._servers = None
        self._all_servers = []


# Global registry instance
_registry: Optional[MCPOfficialRegistry] = None


def get_official_registry() -> MCPOfficialRegistry:
    """Get the global official MCP registry instance.
    
    Returns:
        MCPOfficialRegistry singleton instance
    """
    global _registry
    if _registry is None:
        _registry = MCPOfficialRegistry()
    return _registry


def set_official_registry(registry: MCPOfficialRegistry) -> None:
    """Set the global official MCP registry instance.
    
    Args:
        registry: New registry instance to use
    """
    global _registry
    _registry = registry


__all__ = [
    "MCPOfficialServer",
    "MCPOfficialRegistry",
    "get_official_registry",
    "set_official_registry",
]