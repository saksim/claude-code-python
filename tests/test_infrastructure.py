"""
Claude Code Python - Unit Tests for Core Modules

Tests for DI Container, EventBus, and other infrastructure components.
"""

import asyncio
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDIContainer:
    """Tests for ServiceContainer."""

    def test_register_and_get(self):
        """Test registering and retrieving a service."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("di", "claude_code/di/container.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        container = module.ServiceContainer()

        class TestService:
            def __init__(self):
                self.value = 42

        container.register_instance(TestService, TestService())
        service = container.get(TestService)

        assert service.value == 42

    def test_register_factory(self):
        """Test registering a factory."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("di", "claude_code/di/container.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        container = module.ServiceContainer()

        def create_service():
            return {"data": "test"}

        container.register_factory(dict, create_service)
        service = container.get(dict)

        assert service == {"data": "test"}

    def test_service_not_found(self):
        """Test getting unregistered service raises error."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("di", "claude_code/di/container.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        container = module.ServiceContainer()

        with pytest.raises(module.ServiceNotFoundError):
            container.get(dict)


class TestEventBus:
    """Tests for EventBus."""

    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self):
        """Test publishing and subscribing to events."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("event_bus", "claude_code/services/event_bus.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        event_bus = module.EventBus()
        await event_bus.start()

        received = []

        async def handler(event):
            received.append(event)

        event_bus.subscribe("test.event", handler)

        event = module.Event(type="test.event", payload={"data": "value"})
        await event_bus.publish(event)

        await asyncio.sleep(0.1)

        await event_bus.stop()

        assert len(received) == 1
        assert received[0].type == "test.event"
        assert received[0].payload == {"data": "value"}

    @pytest.mark.asyncio
    async def test_stats(self):
        """Test event bus statistics."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("event_bus", "claude_code/services/event_bus.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        event_bus = module.EventBus()
        await event_bus.start()

        event = module.Event(type="test.event", payload={})
        await event_bus.publish(event)

        await asyncio.sleep(0.1)

        stats = event_bus.get_stats()

        await event_bus.stop()

        assert stats["published"] == 1


class TestRetryPolicy:
    """Tests for Retry Policy."""

    @pytest.mark.asyncio
    async def test_retry_success(self):
        """Test retry succeeds on first attempt."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("retry", "claude_code/services/retry_policy.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        call_count = 0

        async def success_func():
            nonlocal call_count
            call_count += 1
            return "success"

        config = module.RetryConfig(max_attempts=3)
        result = await module.retry_async(success_func, config)

        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_with_backoff(self):
        """Test retry with exponential backoff."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("retry", "claude_code/services/retry_policy.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        call_count = 0

        async def fail_twice():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        config = module.RetryConfig(max_attempts=3, initial_delay=0.01)
        result = await module.retry_async(fail_twice, config)

        assert result == "success"
        assert call_count == 3


class TestRequestContext:
    """Tests for Request Context."""

    def test_generate_ids(self):
        """Test generating request and correlation IDs."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("rc", "claude_code/utils/request_context.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        request_id = module.generate_request_id()
        correlation_id = module.generate_correlation_id()

        assert request_id is not None
        assert correlation_id is not None
        assert len(request_id) > 0
        assert len(correlation_id) > 0

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test RequestContextManager context."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("rc", "claude_code/utils/request_context.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        async with module.RequestContextManager() as ctx:
            request_id = module.get_request_id()
            assert request_id is not None

            ctx.set("key", "value")
            assert ctx.get("key") == "value"


class TestHealthCheck:
    """Tests for Health Check."""

    @pytest.mark.asyncio
    async def test_liveness_check(self):
        """Test liveness check."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("health", "claude_code/services/health.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = await module.liveness_check()

        assert result["alive"] is True
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_registry_health_check(self):
        """Test health check registry."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("health", "claude_code/services/health.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        registry = module.HealthCheckRegistry()

        class TestCheck(module.HealthCheck):
            name = "test"

            async def check(self):
                return module.HealthCheckResult(
                    name=self.name,
                    status=module.HealthStatus.HEALTHY,
                )

        registry.register(TestCheck())
        results = await registry.check_all()

        assert len(results) == 1
        assert results[0].name == "test"


class TestCircuitBreaker:
    """Tests for Circuit Breaker."""

    @pytest.mark.asyncio
    async def test_circuit_state_changes(self):
        """Test circuit breaker state transitions."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("cb", "claude_code/services/circuit_breaker.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        cb = module.CircuitBreaker(
            "test",
            module.CircuitBreakerConfig(failure_threshold=2),
        )

        assert cb.state == module.CircuitState.CLOSED
        assert cb.is_available

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self):
        """Test circuit opens after threshold failures."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("cb", "claude_code/services/circuit_breaker.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        cb = module.CircuitBreaker(
            "test",
            module.CircuitBreakerConfig(failure_threshold=2),
        )

        async def failing_func():
            raise Exception("Failure")

        for _ in range(2):
            try:
                await cb.call(failing_func)
            except Exception:
                pass

        assert cb.state == module.CircuitState.OPEN
        assert not cb.is_available


class TestCacheService:
    """Tests for Cache Service."""

    @pytest.mark.asyncio
    async def test_cache_set_get(self):
        """Test cache set and get."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("cache", "claude_code/services/cache_service.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        cache = module.CacheService()

        await cache.set("key1", "value1")
        result = await cache.get("key1")

        assert result == "value1"

    @pytest.mark.asyncio
    async def test_cache_expiry(self):
        """Test cache expiration."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("cache", "claude_code/services/cache_service.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        cache = module.CacheService(module.CacheConfig(default_ttl=0.1))

        await cache.set("key1", "value1")
        assert await cache.get("key1") == "value1"

        await asyncio.sleep(0.15)

        assert await cache.get("key1") is None


class TestBashTool:
    """Tests for Async BashTool."""

    @pytest.mark.asyncio
    async def test_bash_echo(self):
        """Test bash echo command."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("bash", "claude_code/tools/builtin/bash.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        BashTool = module.BashTool

        class MockContext:
            working_directory = "/tmp"
            environment = {}

        tool = BashTool()
        result = await tool.execute(
            {"command": "echo hello"},
            MockContext()
        )

        assert result is not None
        assert "hello" in result.content.lower() or not result.is_error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])