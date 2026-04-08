"""
Claude Code Python - Feature Configuration
集中配置所有功能开关.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class FeatureConfig:
    """Feature configuration for a single feature."""
    name: str
    env_var: str
    description: str
    enabled: bool = False


class Features:
    """集中功能配置管理器.
    
    用户可以通过以下方式启用功能：
    
    1. 配置文件 (config/features.json 或 .claude/features.json):
       {"enabled": ["KAIROS", "WEB_BROWSER_TOOL"]}
    
    2. 环境变量 (自动识别):
       export KAIROS=1
       export WEB_BROWSER_TOOL=1
    
    3. 编程方式:
       from claude_code.config import Features
       Features.enable("KAIROS")
       Features.enable_all()  # 启用所有实验性功能
    
    Example:
        >>> from claude_code.config import Features
        >>> Features.enable("KAIROS")  # 启用推送通知
        >>> Features.enable_all()       # 启用所有功能
    """
    
    # 类变量：所有可用功能定义
    ALL_FEATURES: dict[str, "FeatureConfig"] = {
        "WEB_BROWSER_TOOL": FeatureConfig(
            name="Web Browser Automation",
            env_var="WEB_BROWSER_TOOL",
            description="Enable web browsing with navigation, click, screenshot support"
        ),
        "KAIROS": FeatureConfig(
            name="Push Notifications",
            env_var="KAIROS",
            description="Send push notifications to user devices"
        ),
        "KAIROS_GITHUB_WEBHOOKS": FeatureConfig(
            name="GitHub PR Subscriptions",
            env_var="KAIROS_GITHUB_WEBHOOKS",
            description="Subscribe to GitHub pull request updates via webhooks"
        ),
        "CONTEXT_COLLAPSE": FeatureConfig(
            name="Context Inspection",
            env_var="CONTEXT_COLLAPSE",
            description="Debug and inspect context collapse state and token usage"
        ),
        "UDS_INBOX": FeatureConfig(
            name="Peer Process List",
            env_var="UDS_INBOX",
            description="List connected peer processes (for multi-agent coordination)"
        ),
        "CLAUDE_CODE_VERIFY_PLAN": FeatureConfig(
            name="Plan Execution Verification",
            env_var="CLAUDE_CODE_VERIFY_PLAN",
            description="Verify that a plan was executed correctly"
        ),
        "TERMINAL_PANEL": FeatureConfig(
            name="Terminal Capture Panel",
            env_var="TERMINAL_PANEL",
            description="Capture and display terminal output in UI panel"
        ),
        "OVERFLOW_TEST_TOOL": FeatureConfig(
            name="Overflow Test Tool",
            env_var="OVERFLOW_TEST_TOOL",
            description="Testing tool for overflow conditions"
        ),
        "HISTORY_SNIP": FeatureConfig(
            name="History Snip",
            env_var="HISTORY_SNIP",
            description="Snip and include historical conversation context"
        ),
        "AGENT_TRIGGERS_REMOTE": FeatureConfig(
            name="Remote Trigger",
            env_var="AGENT_TRIGGERS_REMOTE",
            description="Trigger agents from external sources"
        ),
        "MONITOR_TOOL": FeatureConfig(
            name="Monitor Tool",
            env_var="MONITOR_TOOL",
            description="System monitoring and metrics"
        ),
        "WORKFLOW_SCRIPTS": FeatureConfig(
            name="Workflow Scripts",
            env_var="WORKFLOW_SCRIPTS",
            description="Execute custom workflow scripts"
        ),
    }
    
    # 实验性功能列表（需要显式启用）
    EXPERIMENTAL_FEATURES = [
        "WEB_BROWSER_TOOL",
        "KAIROS",
        "KAIROS_GITHUB_WEBHOOKS",
        "CONTEXT_COLLAPSE",
        "UDS_INBOX",
        "CLAUDE_CODE_VERIFY_PLAN",
        "TERMINAL_PANEL",
        "OVERFLOW_TEST_TOOL",
        "HISTORY_SNIP",
        "AGENT_TRIGGERS_REMOTE",
        "MONITOR_TOOL",
        "WORKFLOW_SCRIPTS",
    ]
    
    # Singleton instance
    _instance: "Features | None" = None
    
    def __new__(cls) -> "Features":
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._enabled_features = set()
            cls._instance._initialized = False
        return cls._instance
    
    def __post_init__(self) -> None:
        """Initialize from environment and config."""
        if self._initialized:
            return
        
        self._load_from_env()
        self._load_from_config()
        self._initialized = True
    
    def _load_from_env(self) -> None:
        """Load enabled features from environment variables."""
        for feat_env in self.EXPERIMENTAL_FEATURES:
            if os.environ.get(feat_env, "0") in ("1", "true", "True"):
                self._enabled_features.add(feat_env)
    
    def _load_config_file(self) -> Optional[list[str]]:
        """Load config from JSON file."""
        import json
        from pathlib import Path
        
        config_paths = [
            Path.cwd() / ".claude" / "features.json",
            Path.cwd() / "config" / "features.json",
            Path.home() / ".claude" / "features.json",
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path) as f:
                        data = json.load(f)
                        return data.get("enabled", [])
                except Exception:
                    pass
        return None
    
    def _load_from_config(self) -> None:
        """Load enabled features from config file."""
        enabled_list = self._load_config_file()
        if enabled_list:
            for feat in enabled_list:
                if feat in self.ALL_FEATURES:
                    self._enabled_features.add(feat)
    
    def is_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled.
        
        Args:
            feature: Feature name (e.g., "KAIROS", "WEB_BROWSER_TOOL")
            
        Returns:
            True if feature is enabled
        """
        if feature == "DEFAULT":
            return True
        return feature in self._enabled_features
    
    def enable(self, feature: str) -> None:
        """Enable a specific feature.
        
        Args:
            feature: Feature name (e.g., "KAIROS")
        """
        if feature in self.ALL_FEATURES:
            self._enabled_features.add(feature)
            os.environ[feature] = "1"
    
    def disable(self, feature: str) -> None:
        """Disable a specific feature.
        
        Args:
            feature: Feature name (e.g., "KAIROS")
        """
        if feature in self._enabled_features:
            self._enabled_features.discard(feature)
            os.environ[feature] = "0"
    
    def enable_all(self) -> None:
        """启用所有实验性功能."""
        for feat in self.EXPERIMENTAL_FEATURES:
            self.enable(feat)
    
    def disable_all(self) -> None:
        """禁用所有实验性功能."""
        for feat in self.EXPERIMENTAL_FEATURES:
            self.disable(feat)
    
    def list_enabled(self) -> list[str]:
        """列出所有已启用的功能."""
        return list(self._enabled_features)
    
    def list_disabled(self) -> list[str]:
        """列出所有已禁用的功能."""
        return [f for f in self.EXPERIMENTAL_FEATURES if f not in self._enabled_features]
    
    def get_enabled_tools(self) -> list[str]:
        """获取已启用功能对应的工具名称."""
        tool_map = {
            "WEB_BROWSER_TOOL": "web_browser",
            "KAIROS": "push_notification",
            "KAIROS_GITHUB_WEBHOOKS": "subscribe_pr",
            "CONTEXT_COLLAPSE": "ctx_inspect",
            "UDS_INBOX": "list_peers",
            "CLAUDE_CODE_VERIFY_PLAN": "verify_plan_execution",
            "TERMINAL_PANEL": "terminal_capture",
            "OVERFLOW_TEST_TOOL": "overflow_test",
            "HISTORY_SNIP": "snip",
            "AGENT_TRIGGERS_REMOTE": "remote_trigger",
            "MONITOR_TOOL": "monitor",
            "WORKFLOW_SCRIPTS": "workflow",
        }
        return [tool_map[f] for f in self._enabled_features if f in tool_map]
    
    @property
    def enabled_tools(self) -> list[str]:
        """便捷属性：获取已启用工具列表."""
        return self.get_enabled_tools()


# 全局实例
features = Features()


__all__ = ["Features", "features", "FeatureConfig"]