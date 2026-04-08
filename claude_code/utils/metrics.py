"""
Claude Code Python - Performance Monitoring
工具性能监控和指标收集.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Decorator pattern
"""

from __future__ import annotations

import time
import logging
import functools
from dataclasses import dataclass, field
from typing import Any, Callable, TypeVar
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class MetricType(Enum):
    """Metric types."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass(frozen=True, slots=True)
class MetricPoint:
    """Single metric data point."""
    name: str
    value: float
    timestamp: float
    tags: dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """指标收集器.
    
    收集并聚合工具执行指标.
    
    Example:
        >>> collector = MetricsCollector()
        >>> collector.increment('tool_calls', tags={'tool': 'bash'})
        >>> collector.record_time('tool_duration', 0.5, tags={'tool': 'bash'})
        >>> print(collector.get_stats())
    """
    
    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._counters: dict[str, dict[tuple, int]] = defaultdict(lambda: defaultdict(int))
        self._timers: dict[str, list[float]] = defaultdict(list)
        self._gauges: dict[str, float] = {}
        self._start_time = time.time()
    
    def increment(self, name: str, value: int = 1, tags: dict[str, str] | None = None) -> None:
        """增加计数器.
        
        Args:
            name: 指标名称
            value: 增量值
            tags: 标签字典
        """
        tag_key = self._make_tag_key(tags)
        self._counters[name][tag_key] += value
    
    def record_time(self, name: str, seconds: float, tags: dict[str, str] | None = None) -> None:
        """记录时间 (秒).
        
        Args:
            name: 指标名称
            seconds: 执行时间 (秒)
            tags: 标签字典
        """
        self._timers[name].append(seconds)
    
    def set_gauge(self, name: str, value: float, tags: dict[str, str] | None = None) -> None:
        """设置仪表值.
        
        Args:
            name: 指标名称
            value: 仪表值
            tags: 标签字典
        """
        tag_key = self._make_tag_key(tags)
        self._gauges[f"{name}:{tag_key}"] = value
    
    def _make_tag_key(self, tags: dict[str, str] | None) -> tuple:
        """将标签转换为可哈希的键."""
        if not tags:
            return ()
        return tuple(sorted(tags.items()))
    
    def get_counter(self, name: str, tags: dict[str, str] | None = None) -> int:
        """获取计数器值."""
        tag_key = self._make_tag_key(tags)
        return self._counters[name].get(tag_key, 0)
    
    def get_timer_stats(self, name: str) -> dict[str, float]:
        """获取计时器统计信息."""
        times = self._timers.get(name, [])
        if not times:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        
        sorted_times = sorted(times)
        n = len(sorted_times)
        
        return {
            "count": n,
            "min": sorted_times[0],
            "max": sorted_times[-1],
            "avg": sum(times) / n,
            "p50": sorted_times[n // 2],
            "p95": sorted_times[int(n * 0.95)],
            "p99": sorted_times[int(n * 0.99)],
        }
    
    def get_summary(self) -> dict[str, Any]:
        """获取所有指标摘要."""
        uptime = time.time() - self._start_time
        
        return {
            "uptime_seconds": uptime,
            "counters": {
                name: dict(counts)
                for name, counts in self._counters.items()
            },
            "timers": {
                name: self.get_timer_stats(name)
                for name in self._timers
            },
            "gauges": dict(self._gauges),
        }
    
    def reset(self) -> None:
        """重置所有指标."""
        self._counters.clear()
        self._timers.clear()
        self._gauges.clear()
        self._start_time = time.time()


# 全局指标收集器
_metrics_collector = MetricsCollector()


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器."""
    return _metrics_collector


# 性能监控装饰器
SLOW_THRESHOLD_SECONDS = 5.0


def measure_tool_performance(func: Callable[..., T]) -> Callable[..., T]:
    """工具性能监控装饰器.
    
    自动记录:
    - 执行时间
    - 调用次数
    - 错误次数
    - 慢查询警告
    
    Example:
        >>> class MyTool(Tool):
        ...     @measure_tool_performance
        ...     async def execute(self, input_data, context):
        ...         # 工具逻辑
    """
    @functools.wraps(func)
    async def wrapper(self: Any, input_data: Any, context: Any, *args: Any, **kwargs: Any) -> T:
        tool_name = getattr(self, 'name', func.__name__)
        start_time = time.perf_counter()
        
        try:
            result = await func(self, input_data, context, *args, **kwargs)
            
            # 记录成功
            elapsed = time.perf_counter() - start_time
            _metrics_collector.increment('tool_calls', tags={'tool': tool_name, 'status': 'success'})
            _metrics_collector.record_time('tool_duration', elapsed, tags={'tool': tool_name})
            
            # 慢查询警告
            if elapsed > SLOW_THRESHOLD_SECONDS:
                logger.warning(
                    f"Slow tool execution: {tool_name} took {elapsed:.2f}s",
                    extra={'tool': tool_name, 'duration': elapsed}
                )
            
            return result
            
        except Exception as e:
            # 记录错误
            elapsed = time.perf_counter() - start_time
            _metrics_collector.increment('tool_calls', tags={'tool': tool_name, 'status': 'error'})
            _metrics_collector.increment('tool_errors', tags={'tool': tool_name, 'error_type': type(e).__name__})
            _metrics_collector.record_time('tool_duration', elapsed, tags={'tool': tool_name})
            
            raise
    
    return wrapper


def measure_async(func: Callable[..., T]) -> Callable[..., T]:
    """通用异步函数性能监控."""
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        start = time.perf_counter()
        try:
            result = await func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            _metrics_collector.record_time('async_duration', elapsed, tags={'function': func.__name__})
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            _metrics_collector.increment('async_errors', tags={'function': func.__name__})
            raise
    
    return wrapper


def measure_sync(func: Callable[..., T]) -> Callable[..., T]:
    """通用同步函数性能监控."""
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            _metrics_collector.record_time('sync_duration', elapsed, tags={'function': func.__name__})
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start
            _metrics_collector.increment('sync_errors', tags={'function': func.__name__})
            raise
    
    return wrapper


class PerformanceMonitor:
    """性能监控上下文管理器.
    
    Example:
        >>> with PerformanceMonitor('operation_name') as monitor:
        ...     # 执行操作
        ...     pass
        >>> print(monitor.elapsed)
    """
    
    def __init__(self, operation: str, tags: dict[str, str] | None = None) -> None:
        """初始化性能监控器.
        
        Args:
            operation: 操作名称
            tags: 标签字典
        """
        self.operation = operation
        self.tags = tags or {}
        self.start_time: float = 0
        self.elapsed: float = 0
        self.error: Exception | None = None
    
    def __enter__(self) -> "PerformanceMonitor":
        self.start_time = time.perf_counter()
        return self
    
    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb: Any) -> None:
        self.elapsed = time.perf_counter() - self.start_time
        
        if exc_type is not None:
            # Operation failed
            _metrics_collector.increment(
                'operation_calls',
                tags={**self.tags, 'operation': self.operation, 'status': 'error'}
            )
            self.error = exc_val
        else:
            # Operation succeeded
            _metrics_collector.increment(
                'operation_calls',
                tags={**self.tags, 'operation': self.operation, 'status': 'success'}
            )
            
            # Check for slow operations
            if self.elapsed > SLOW_THRESHOLD_SECONDS:
                logger.warning(
                    f"Slow operation: {self.operation} took {self.elapsed:.2f}s"
                )
        
        _metrics_collector.record_time(
            'operation_duration',
            self.elapsed,
            tags={**self.tags, 'operation': self.operation}
        )


__all__ = [
    "MetricsCollector",
    "get_metrics_collector",
    "MetricType",
    "MetricPoint",
    "measure_tool_performance",
    "measure_async",
    "measure_sync",
    "PerformanceMonitor",
    "SLOW_THRESHOLD_SECONDS",
]