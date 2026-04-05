"""
Claude Code Python - Unit Tests

Tests for core functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from claude_code.tools import (
    Tool,
    ToolDefinition,
    ToolContext,
    ToolResult,
    ToolRegistry,
    BashTool,
    ReadTool,
    GlobTool,
    GrepTool,
)
from claude_code.state.app_state import AppState, PermissionMode, EffortLevel
from claude_code.services import (
    TokenEstimator,
    RateLimiter,
    CacheService,
    TelemetryService,
    TelemetryEventType as EventType,
)
from claude_code.utils.errors import ClaudeCodeError, RateLimitError as RLError


class TestToolDefinition:
    """Tests for ToolDefinition."""
    
    def test_tool_definition_creation(self):
        """Test creating a tool definition."""
        tool_def = ToolDefinition(
            name="test-tool",
            description="A test tool",
            input_schema={"type": "object"}
        )
        
        assert tool_def.name == "test-tool"
        assert tool_def.description == "A test tool"
        assert tool_def.input_schema["type"] == "object"
    
    def test_tool_definition_defaults(self):
        """Test default values."""
        tool_def = ToolDefinition(
            name="test",
            description="desc",
            input_schema={}
        )
        
        assert tool_def.aliases == []
        assert tool_def.max_result_size_chars == 100000
        assert tool_def.is_read_only is False


class TestToolContext:
    """Tests for ToolContext."""
    
    def test_tool_context_creation(self):
        """Test creating a tool context."""
        ctx = ToolContext(
            working_directory="/tmp",
            environment={"TEST": "value"}
        )
        
        assert ctx.working_directory == "/tmp"
        assert ctx.get_env("TEST") == "value"
    
    def test_tool_context_env_fallback(self):
        """Test environment variable fallback."""
        ctx = ToolContext(working_directory="/tmp")
        
        with patch.dict(os.environ, {"PATH": "/usr/bin"}):
            assert ctx.get_env("PATH") == "/usr/bin"
    
    def test_tool_context_abort(self):
        """Test abort signal."""
        abort_event = asyncio.Event()
        ctx = ToolContext(
            working_directory="/tmp",
            abort_signal=abort_event
        )
        
        assert ctx.should_abort() is False
        abort_event.set()
        assert ctx.should_abort() is True


class TestToolRegistry:
    """Tests for ToolRegistry."""
    
    def test_registry_register_and_get(self):
        """Test registering and retrieving tools."""
        registry = ToolRegistry()
        tool = BashTool()
        registry.register(tool)
        
        assert registry.get("bash") is not None
    
    def test_registry_list_all(self):
        """Test listing all tools."""
        registry = ToolRegistry()
        registry.register(BashTool())
        registry.register(ReadTool())
        
        tools = registry.list_all()
        assert len(tools) >= 2
    
    def test_registry_aliases(self):
        """Test tool aliases."""
        registry = ToolRegistry()
        registry.register(BashTool())
        
        result = registry.get("bash")
        assert result is not None
    
    def test_registry_not_found(self):
        """Test getting non-existent tool."""
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None


class TestAppState:
    """Tests for AppState."""
    
    def test_app_state_defaults(self):
        """Test default state values."""
        state = AppState()
        
        assert state.main_loop_model == "claude-sonnet-4-20250514"
        assert state.effort_value == "medium"
        assert state.tool_permission_context is not None
    
    def test_app_state_with_values(self):
        """Test creating state with values."""
        state = AppState(
            main_loop_model="claude-sonnet-4-20250514",
            verbose=True
        )
        
        assert state.main_loop_model == "claude-sonnet-4-20250514"
        assert state.verbose is True


class TestTokenEstimator:
    """Tests for TokenEstimator."""
    
    def test_rough_token_count(self):
        """Test rough token counting."""
        from claude_code.services import rough_token_count
        
        text = "Hello, world!"
        tokens = rough_token_count(text)
        
        assert tokens > 0
        assert isinstance(tokens, int)
    
    def test_estimate_message_tokens(self):
        """Test message token estimation."""
        from claude_code.services import estimate_message_tokens
        
        message = {"role": "user", "content": "Hello"}
        
        tokens = estimate_message_tokens(message)
        assert tokens > 0


class TestCacheService:
    """Tests for CacheService."""
    
    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        cache = CacheService(max_size=100)
        
        await cache.set("key1", "value1")
        result = await cache.get("key1")
        
        assert result == "value1"
    
    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """Test cache miss."""
        cache = CacheService()
        
        result = await cache.get("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_expiry(self):
        """Test cache expiration."""
        import time
        
        cache = CacheService(default_ttl=0.1)
        
        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"
        
        await asyncio.sleep(0.15)
        
        result = await cache.get("key1")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """Test deleting cache entries."""
        cache = CacheService()
        
        await cache.set("key1", "value1")
        assert await cache.delete("key1") is True
        assert await cache.get("key1") is None
    
    @pytest.mark.asyncio
    async def test_cache_clear(self):
        """Test clearing cache."""
        cache = CacheService()
        
        await cache.set("key1", "value1")
        await cache.set("key2", "value2")
        await cache.clear()
        
        assert await cache.get("key1") is None
        assert await cache.get("key2") is None
    
    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """Test cache statistics."""
        cache = CacheService(max_size=50)
        
        await cache.set("key1", "value1")
        await cache.get("key1")
        await cache.get("key1")
        
        stats = await cache.get_stats()
        
        assert stats["size"] == 1


class TestTelemetryService:
    """Tests for TelemetryService."""
    
    @pytest.mark.asyncio
    async def test_track_event(self):
        """Test tracking events."""
        telemetry = TelemetryService(enabled=True)
        
        await telemetry.track_event(
            EventType.QUERY,
            {"model": "test", "tokens": 100}
        )
        
        events = await telemetry.get_events()
        assert len(events) >= 1
    
    @pytest.mark.asyncio
    async def test_track_query(self):
        """Test tracking query events."""
        telemetry = TelemetryService()
        
        await telemetry.track_query(
            model="sonnet",
            input_tokens=100,
            output_tokens=50,
            duration_ms=1000
        )
        
        events = await telemetry.get_events()
        assert len(events) >= 1
    
    @pytest.mark.asyncio
    async def test_track_error(self):
        """Test tracking errors."""
        telemetry = TelemetryService()
        
        await telemetry.track_error(
            error_type="TestError",
            error_message="Test error message"
        )
        
        events = await telemetry.get_events()
        assert len(events) >= 1
    
    @pytest.mark.asyncio
    async def test_telemetry_stats(self):
        """Test telemetry statistics."""
        telemetry = TelemetryService()
        
        await telemetry.track_query(model="test", input_tokens=1, output_tokens=1, duration_ms=1)
        await telemetry.track_error(error_type="err", error_message="msg")
        
        stats = await telemetry.get_stats()
        
        assert "total_events" in stats


class TestBashTool:
    """Tests for BashTool."""
    
    def test_bash_tool_definition(self):
        """Test BashTool definition."""
        tool = BashTool()
        definition = tool.get_definition()
        
        assert definition.name == "bash"
        assert "command" in str(definition.input_schema)
    
    @pytest.mark.asyncio
    async def test_bash_execution(self):
        """Test bash command execution."""
        tool = BashTool()
        context = ToolContext(working_directory="/tmp")
        
        result = await tool.execute(
            {"command": "echo Hello"},
            context
        )
        
        assert result is not None
        assert isinstance(result, ToolResult)


class TestGlobTool:
    """Tests for GlobTool."""
    
    def test_glob_tool_definition(self):
        """Test GlobTool definition."""
        tool = GlobTool()
        definition = tool.get_definition()
        
        assert definition.name == "glob"
    
    @pytest.mark.asyncio
    async def test_glob_execution(self):
        """Test glob pattern matching."""
        tool = GlobTool()
        context = ToolContext(working_directory=os.path.dirname(os.path.abspath(__file__)))
        
        result = await tool.execute(
            {"pattern": "test_*.py"},
            context
        )
        
        assert result is not None


class TestGrepTool:
    """Tests for GrepTool."""
    
    def test_grep_tool_definition(self):
        """Test GrepTool definition."""
        tool = GrepTool()
        definition = tool.get_definition()
        
        assert definition.name == "grep"


class TestErrorHandling:
    """Tests for error handling."""
    
    def test_claude_error(self):
        """Test ClaudeCodeError."""
        error = ClaudeCodeError("Test error", code="TEST_ERROR")
        
        assert str(error) == "Test error"
        assert error.code == "TEST_ERROR"
    
    def test_rate_limit_error(self):
        """Test RateLimitError."""
        error = RLError("Rate limited")
        
        assert "Rate limited" in str(error)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])