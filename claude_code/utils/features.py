"""
Claude Code Python - Feature Discovery Helper
帮助用户发现和启用功能.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class FeatureInfo:
    """Feature information for discovery."""
    name: str
    tool_name: str
    description: str
    env_var: str
    enabled: bool


class FeatureDiscovery:
    """Feature discovery and management."""
    
    FEATURES: list[FeatureInfo] = [
        FeatureInfo(
            name="Web Browser Automation",
            tool_name="web_browser",
            description="Enable web browsing with navigation, click, screenshot support",
            env_var="WEB_BROWSER_TOOL",
            enabled=False,
        ),
        FeatureInfo(
            name="Push Notifications",
            tool_name="push_notification",
            description="Send push notifications to user devices",
            env_var="KAIROS",
            enabled=False,
        ),
        FeatureInfo(
            name="GitHub PR Subscriptions",
            tool_name="subscribe_pr",
            description="Subscribe to GitHub pull request updates via webhooks",
            env_var="KAIROS_GITHUB_WEBHOOKS",
            enabled=False,
        ),
        FeatureInfo(
            name="Context Inspection",
            tool_name="ctx_inspect",
            description="Debug and inspect context collapse state and token usage",
            env_var="CONTEXT_COLLAPSE",
            enabled=False,
        ),
        FeatureInfo(
            name="Peer Process List",
            tool_name="list_peers",
            description="List connected peer processes (for multi-agent coordination)",
            env_var="UDS_INBOX",
            enabled=False,
        ),
        FeatureInfo(
            name="Plan Execution Verification",
            tool_name="verify_plan_execution",
            description="Verify that a plan was executed correctly",
            env_var="CLAUDE_CODE_VERIFY_PLAN",
            enabled=False,
        ),
        FeatureInfo(
            name="Terminal Capture Panel",
            tool_name="terminal_capture",
            description="Capture and display terminal output in UI panel",
            env_var="TERMINAL_PANEL",
            enabled=False,
        ),
        FeatureInfo(
            name="Overflow Test Tool",
            tool_name="overflow_test",
            description="Testing tool for overflow conditions",
            env_var="OVERFLOW_TEST_TOOL",
            enabled=False,
        ),
        FeatureInfo(
            name="History Snip",
            tool_name="snip",
            description="Snip and include historical conversation context",
            env_var="HISTORY_SNIP",
            enabled=False,
        ),
        FeatureInfo(
            name="Remote Trigger",
            tool_name="remote_trigger",
            description="Trigger agents from external sources",
            env_var="AGENT_TRIGGERS_REMOTE",
            enabled=False,
        ),
        FeatureInfo(
            name="Monitor Tool",
            tool_name="monitor",
            description="System monitoring and metrics",
            env_var="MONITOR_TOOL",
            enabled=False,
        ),
        FeatureInfo(
            name="Workflow Scripts",
            tool_name="workflow",
            description="Execute custom workflow scripts",
            env_var="WORKFLOW_SCRIPTS",
            enabled=False,
        ),
    ]
    
    @classmethod
    def list_all(cls) -> list[FeatureInfo]:
        """List all available features with their status.
        
        Returns:
            List of FeatureInfo with current enabled status
        """
        import os
        
        result = []
        for feature in cls.FEATURES:
            enabled = os.environ.get(feature.env_var, "0") in ("1", "true", "True")
            result.append(FeatureInfo(
                name=feature.name,
                tool_name=feature.tool_name,
                description=feature.description,
                env_var=feature.env_var,
                enabled=enabled,
            ))
        return result
    
    @classmethod
    def list_enabled(cls) -> list[FeatureInfo]:
        """List only enabled features.
        
        Returns:
            List of enabled FeatureInfo
        """
        return [f for f in cls.list_all() if f.enabled]
    
    @classmethod
    def list_disabled(cls) -> list[FeatureInfo]:
        """List only disabled features.
        
        Returns:
            List of disabled FeatureInfo
        """
        return [f for f in cls.list_all() if not f.enabled]
    
    @classmethod
    def enable(cls, env_var: str) -> bool:
        """Enable a feature by environment variable name.
        
        Args:
            env_var: Environment variable name (e.g., "KAIROS")
            
        Returns:
            True if successful
        """
        import os
        os.environ[env_var] = "1"
        return True
    
    @classmethod
    def disable(cls, env_var: str) -> bool:
        """Disable a feature by environment variable name.
        
        Args:
            env_var: Environment variable name (e.g., "KAIROS")
            
        Returns:
            True if successful
        """
        import os
        os.environ[env_var] = "0"
        return True
    
    @classmethod
    def print_help(cls) -> None:
        """Print available features and how to enable them."""
        import os
        
        enabled = cls.list_enabled()
        disabled = cls.list_disabled()
        
        print("=" * 60)
        print("Claude Code Python - Available Features")
        print("=" * 60)
        
        if enabled:
            print(f"\n[ENABLED] ({len(enabled)} features)")
            for f in enabled:
                print(f"  + {f.name}")
                print(f"    Tool: {f.tool_name}")
                print(f"    Env:  {f.env_var}=1")
                print()
        
        if disabled:
            print(f"\n[DISABLED] ({len(disabled)} features)")
            for f in disabled:
                print(f"  - {f.name}")
                print(f"    Tool: {f.tool_name}")
                print(f"    Description: {f.description}")
                print(f"    Enable with: export {f.env_var}=1")
                print()
        
        print("-" * 60)
        print("Usage:")
        print("  from claude_code.utils import FeatureDiscovery")
        print("  FeatureDiscovery.print_help()")
        print("  FeatureDiscovery.enable('KAIROS')")
        print("-" * 60)


__all__ = ["FeatureDiscovery", "FeatureInfo"]