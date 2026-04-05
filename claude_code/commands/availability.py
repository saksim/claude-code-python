"""
Claude Code Python - Command Availability Check
命令可用性检查系统
"""

from __future__ import annotations

from typing import Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class AvailabilityTarget(Enum):
    """可用性目标"""
    CLAUDE_AI = "claude-ai"      # Claude.ai 网页版
    CONSOLE = "console"         # Console API
    ALL = "all"


@dataclass
class AvailabilityRule:
    """可用性规则"""
    target: AvailabilityTarget
    condition: Callable[[], bool]
    reason: Optional[str] = None


class AvailabilityChecker:
    """
    命令可用性检查器
    根据订阅状态、API密钥等决定命令是否可用
    """
    
    def __init__(self):
        self._rules: dict[str, list[AvailabilityRule]] = {}
        self._cached_results: dict[str, bool] = {}
        self._cache_version: int = 0
    
    def register_rule(
        self,
        command_name: str,
        target: AvailabilityTarget,
        condition: Callable[[], bool],
        reason: str = None,
    ) -> None:
        """注册可用性规则"""
        if command_name not in self._rules:
            self._rules[command_name] = []
        
        self._rules[command_name].append(AvailabilityRule(
            target=target,
            condition=condition,
            reason=reason,
        ))
        
        self._invalidate_cache(command_name)
    
    def is_available(
        self,
        command_name: str,
        target: AvailabilityTarget = AvailabilityTarget.ALL,
    ) -> bool:
        """检查命令是否可用"""
        cache_key = f"{command_name}:{target.value}"
        
        if cache_key in self._cached_results:
            return self._cached_results[cache_key]
        
        rules = self._rules.get(command_name, [])
        
        if not rules:
            self._cached_results[cache_key] = True
            return True
        
        for rule in rules:
            if target != AvailabilityTarget.ALL and rule.target != target:
                continue
            
            try:
                if not rule.condition():
                    self._cached_results[cache_key] = False
                    return False
            except Exception:
                pass
        
        self._cached_results[cache_key] = True
        return True
    
    def check_or_raise(
        self,
        command_name: str,
        target: AvailabilityTarget = AvailabilityTarget.ALL,
    ) -> None:
        """检查可用性，不可用则抛出异常"""
        if not self.is_available(command_name, target):
            rule = self._rules.get(command_name, [None])[0]
            reason = rule.reason if rule else "Command not available"
            raise AvailabilityError(f"Command '{command_name}' is not available: {reason}")
    
    def filter_available(
        self,
        command_names: list[str],
        target: AvailabilityTarget = AvailabilityTarget.ALL,
    ) -> list[str]:
        """过滤出可用的命令"""
        return [n for n in command_names if self.is_available(n, target)]
    
    def get_availability_info(self, command_name: str) -> dict:
        """获取命令的可用性信息"""
        rules = self._rules.get(command_name, [])
        
        if not rules:
            return {"available": True, "reason": "No restrictions"}
        
        info = {"available": False, "reasons": []}
        
        for rule in rules:
            try:
                result = rule.condition()
                if result:
                    info["available"] = True
                    break
                if rule.reason:
                    info["reasons"].append(rule.reason)
            except Exception as e:
                info["reasons"].append(f"Check failed: {e}")
        
        return info
    
    def _invalidate_cache(self, command_name: str = None) -> None:
        """使缓存失效"""
        self._cache_version += 1
        if command_name:
            self._cached_results = {
                k: v for k, v in self._cached_results.items()
                if not k.startswith(command_name + ":")
            }
        else:
            self._cached_results.clear()


class AvailabilityError(Exception):
    """可用性检查错误"""
    pass


def is_claude_ai_subscriber() -> bool:
    """检查是否是 Claude.ai 订阅用户"""
    import os
    return bool(os.environ.get("CLAUDE_AI_SESSION"))


def is_direct_api_customer() -> bool:
    """检查是否是有 API 密钥的直接客户"""
    import os
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def create_default_checker() -> AvailabilityChecker:
    """创建默认的可用性检查器"""
    checker = AvailabilityChecker()
    
    checker.register_rule(
        "login",
        AvailabilityTarget.CLAUDE_AI,
        lambda: not is_claude_ai_subscriber(),
        "Already logged in via Claude.ai",
    )
    
    checker.register_rule(
        "logout",
        AvailabilityTarget.CLAUDE_AI,
        lambda: is_claude_ai_subscriber(),
        "Not logged in via Claude.ai",
    )
    
    checker.register_rule(
        "mcp",
        AvailabilityTarget.CONSOLE,
        lambda: is_direct_api_customer(),
        "Requires API key",
    )
    
    return checker


_default_checker: Optional[AvailabilityChecker] = None


def get_availability_checker() -> AvailabilityChecker:
    """获取默认的可用性检查器"""
    global _default_checker
    if _default_checker is None:
        _default_checker = create_default_checker()
    return _default_checker


def meets_availability_requirement(command_name: str) -> bool:
    """检查命令是否满足可用性要求"""
    return get_availability_checker().is_available(command_name)


__all__ = [
    "AvailabilityTarget",
    "AvailabilityRule",
    "AvailabilityChecker",
    "AvailabilityError",
    "is_claude_ai_subscriber",
    "is_direct_api_customer",
    "create_default_checker",
    "get_availability_checker",
    "meets_availability_requirement",
]
