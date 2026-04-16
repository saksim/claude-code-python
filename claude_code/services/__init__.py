"""
Claude Code Python - Services

Core services for API communication, rate limiting, analytics, and MCP support.
"""

from claude_code.services.token_estimation import (
    TokenEstimator,
    get_token_estimator,
    set_token_estimator,
    rough_token_count,
    estimate_message_tokens,
)

from claude_code.services.rate_limiter import (
    RateLimiter,
    TokenBucketRateLimiter,
    RateLimitConfig,
    RateLimitError,
    RateLimitMode,
    get_rate_limiter,
    set_rate_limiter,
    with_rate_limit,
)

from claude_code.services.analytics import (
    AnalyticsService,
    AnalyticsEvent,
    SessionStats,
    EventType,
    get_analytics,
    set_analytics,
    track_event,
    log_event,
)

from claude_code.services.mcp.client import (
    MCPClient,
    MCPManager,
    MCPTool,
    MCPResource,
    MCPConnectionConfig,
    MCPConnectionState,
    MCPTransportType,
    MCPProtocol,
    get_mcp_manager,
    set_mcp_manager,
)

from claude_code.services.cache_service import (
    CacheService,
    CacheEntry,
    CacheConfig,
    CacheStrategy,
    cached,
    get_cache,
)

from claude_code.services.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerManager,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitState,
    get_circuit_breaker_manager,
)

from claude_code.services.retry_policy import (
    RetryConfig,
    RetryStrategy,
    RetryExhaustedError,
    retry_async,
    retry_sync,
    with_retry,
    RETRY_QUICK,
    RETRY_DEFAULT,
    RETRY_AGGRESSIVE,
)

from claude_code.services.telemetry_service import (
    TelemetryService,
    TelemetryEvent,
    EventType as TelemetryEventType,
    get_telemetry,
)

from claude_code.services.encryption_service import (
    SessionEncryption,
    EncryptedData,
    SessionStorage,
    get_encryption,
)

from claude_code.services.memory_service import (
    SessionMemory,
    MemoryEntry,
    MemoryNamespace,
    get_memory,
    get_namespace,
)

from claude_code.services.cost_tracker import (
    CostTracker,
    CostEntry,
    CostStats,
    get_cost_tracker,
)

from claude_code.services.history_manager import (
    HistoryManager,
    HistoryEntry,
    get_history_manager,
)

from claude_code.services.hooks_manager import (
    HooksManager,
    Hook,
    HookEvent,
    HookResult,
    get_hooks_manager,
)

from claude_code.services.permissions_manager import (
    PermissionsManager,
    PermissionMode,
    PermissionResult,
    PermissionRule,
    PermissionRequest,
    get_permissions_manager,
)

from claude_code.services.health import (
    HealthCheck,
    HealthCheckResult,
    HealthStatus,
    HealthCheckRegistry,
    get_health_check_registry,
    health_check,
    liveness_check,
    readiness_check,
)

from claude_code.services.shutdown import (
    ShutdownManager,
    ShutdownConfig,
    ShutdownPhase,
    ShutdownApplication,
    get_shutdown_manager,
)

# Backward-compatible alias for older imports.
Application = ShutdownApplication

from claude_code.services.event_bus import (
    EventBus,
    Event,
    EventPriority,
    EventHandler,
    get_event_bus,
    set_event_bus,
    on_event,
    on_all_events,
    ToolEvents,
    APIEvents,
    SystemEvents,
)

from claude_code.services.websocket import (
    WebSocketServer,
    WebSocketClient,
    WebSocketMessage,
    WebSocketState,
    get_websocket_server,
    start_websocket_server,
)

__all__ = [
    # Token estimation
    "TokenEstimator",
    "RateLimiter",
    "TokenBucketRateLimiter",
    "RateLimitConfig",
    "RateLimitError",
    "RateLimitMode",
    "get_token_estimator",
    "set_token_estimator",
    "rough_token_count",
    "estimate_message_tokens",
    "get_rate_limiter",
    "set_rate_limiter",
    "with_rate_limit",
    
    # Analytics
    "AnalyticsService",
    "AnalyticsEvent",
    "SessionStats",
    "EventType",
    "get_analytics",
    "set_analytics",
    "track_event",
    "log_event",
    
    # MCP
    "MCPClient",
    "MCPManager",
    "MCPTool",
    "MCPResource",
    "MCPConnectionConfig",
    "MCPConnectionState",
    "MCPTransportType",
    "MCPProtocol",
    "get_mcp_manager",
    "set_mcp_manager",
    
    # Cache
    "CacheService",
    "CacheEntry",
    "CacheConfig",
    "CacheStrategy",
    "cached",
    "get_cache",
    
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerManager",
    "CircuitBreakerConfig",
    "CircuitBreakerOpenError",
    "CircuitState",
    "get_circuit_breaker_manager",
    
    # Telemetry
    "TelemetryService",
    "TelemetryEvent",
    "TelemetryEventType",
    "get_telemetry",
    
    # Encryption
    "SessionEncryption",
    "EncryptedData",
    "SessionStorage",
    "get_encryption",
    
    # Memory
    "SessionMemory",
    "MemoryEntry",
    "MemoryNamespace",
    "get_memory",
    "get_namespace",
    
    # Cost tracking
    "CostTracker",
    "CostEntry",
    "CostStats",
    "get_cost_tracker",
    
    # History
    "HistoryManager",
    "HistoryEntry",
    "get_history_manager",
    
    # Hooks
    "HooksManager",
    "Hook",
    "HookEvent",
    "HookResult",
    "get_hooks_manager",
    
    # Permissions
    "PermissionsManager",
    "PermissionMode",
    "PermissionResult",
    "PermissionRule",
    "PermissionRequest",
    "get_permissions_manager",
    
    # Retry Policy
    "RetryConfig",
    "RetryStrategy",
    "RetryExhaustedError",
    "retry_async",
    "retry_sync",
    "with_retry",
    "RETRY_QUICK",
    "RETRY_DEFAULT",
    "RETRY_AGGRESSIVE",
    
    # Health Check
    "HealthCheck",
    "HealthCheckResult",
    "HealthStatus",
    "HealthCheckRegistry",
    "get_health_check_registry",
    "health_check",
    "liveness_check",
    "readiness_check",
    
    # Shutdown
    "ShutdownManager",
    "ShutdownConfig",
    "ShutdownPhase",
    "ShutdownApplication",
    "Application",
    "get_shutdown_manager",
    
    # Event Bus
    "EventBus",
    "Event",
    "EventPriority",
    "EventHandler",
    "get_event_bus",
    "set_event_bus",
    "on_event",
    "on_all_events",
    "ToolEvents",
    "APIEvents",
    "SystemEvents",
    
    # WebSocket
    "WebSocketServer",
    "WebSocketClient",
    "WebSocketMessage",
    "WebSocketState",
    "get_websocket_server",
    "start_websocket_server",
]
