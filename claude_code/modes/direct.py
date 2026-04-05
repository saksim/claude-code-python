"""
Claude Code Python - Direct Modes

Provides various runtime modes for Claude Code.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class DirectModeReport:
    """Report for a direct mode operation.
    
    Attributes:
        mode: Mode name
        target: Target (URL, host, etc.)
        active: Whether the mode is active
    """
    mode: str
    target: str
    active: bool = True

    def as_text(self) -> str:
        """Convert to text format."""
        return f"mode={self.mode}\ntarget={self.target}\nactive={self.active}"

    def as_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return {
            "mode": self.mode,
            "target": self.target,
            "active": str(self.active),
        }


class DirectModes:
    """Direct modes for different runtime scenarios.
    
    Supports:
    - direct-connect: Direct connection to a remote
    - deep-link: Deep link connection
    - remote: Remote mode
    - ssh: SSH mode
    - teleport: Teleport mode
    """

    @staticmethod
    def run_direct_connect(target: str) -> DirectModeReport:
        """Run in direct-connect mode.
        
        Args:
            target: Connection target
            
        Returns:
            DirectModeReport
        """
        return DirectModeReport(mode="direct-connect", target=target, active=True)

    @staticmethod
    def run_deep_link(target: str) -> DirectModeReport:
        """Run in deep-link mode.
        
        Args:
            target: Link target
            
        Returns:
            DirectModeReport
        """
        return DirectModeReport(mode="deep-link", target=target, active=True)

    @staticmethod
    def run_remote(target: str) -> DirectModeReport:
        """Run in remote mode.
        
        Args:
            target: Remote target
            
        Returns:
            DirectModeReport
        """
        return DirectModeReport(mode="remote", target=target, active=True)

    @staticmethod
    def run_ssh(target: str) -> DirectModeReport:
        """Run in SSH mode.
        
        Args:
            target: SSH target (user@host)
            
        Returns:
            DirectModeReport
        """
        return DirectModeReport(mode="ssh", target=target, active=True)

    @staticmethod
    def run_teleport(target: str) -> DirectModeReport:
        """Run in teleport mode.
        
        Args:
            target: Teleport target
            
        Returns:
            DirectModeReport
        """
        return DirectModeReport(mode="teleport", target=target, active=True)

    @staticmethod
    def get_available_modes() -> list[str]:
        """Get list of available modes.
        
        Returns:
            List of mode names
        """
        return ["direct-connect", "deep-link", "remote", "ssh", "teleport"]

    @staticmethod
    def is_valid_mode(mode: str) -> bool:
        """Check if a mode is valid.
        
        Args:
            mode: Mode name
            
        Returns:
            True if valid, False otherwise
        """
        return mode in DirectModes.get_available_modes()


@dataclass(frozen=True, slots=True)
class RuntimeModeReport:
    """Detailed report for runtime mode operations.
    
    Attributes:
        mode: Runtime mode name
        connected: Whether connected
        detail: Detailed information
    """
    mode: str
    connected: bool
    detail: str

    def as_text(self) -> str:
        """Convert to text format."""
        return f"mode={self.mode}\nconnected={self.connected}\ndetail={self.detail}"

    def as_dict(self) -> dict[str, str]:
        """Convert to dictionary."""
        return {
            "mode": self.mode,
            "connected": str(self.connected),
            "detail": self.detail,
        }

    def as_markdown(self) -> str:
        """Convert to markdown format."""
        status = "Connected" if self.connected else "Disconnected"
        return f"- **{self.mode}** ({status}): {self.detail}"


def run_remote_runtime_mode(target: str) -> RuntimeModeReport:
    """Run remote runtime mode.
    
    Args:
        target: Remote target
        
    Returns:
        RuntimeModeReport
    """
    return RuntimeModeReport("remote", True, f"Remote runtime placeholder prepared for {target}")


def run_ssh_runtime_mode(target: str) -> RuntimeModeReport:
    """Run SSH runtime mode.
    
    Args:
        target: SSH target (user@host)
        
    Returns:
        RuntimeModeReport
    """
    return RuntimeModeReport("ssh", True, f"SSH proxy placeholder prepared for {target}")


def run_teleport_runtime_mode(target: str) -> RuntimeModeReport:
    """Run teleport runtime mode.
    
    Args:
        target: Teleport target
        
    Returns:
        RuntimeModeReport
    """
    return RuntimeModeReport("teleport", True, f"Teleport resume/create placeholder prepared for {target}")


__all__ = [
    "DirectModeReport",
    "DirectModes",
]