"""
Claude Code Python - API Client Protocols

Defines API client interfaces and provider factory.
Supports Anthropic, OpenAI-compatible (Ollama/vLLM/DeepSeek),
AWS Bedrock, Google Vertex, and Azure OpenAI backends.

Following TOP Python Dev standards:
- Protocol for abstract interface
- Dependency injection pattern
- Adapter base class for multi-backend support
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Any, Optional
from dataclasses import dataclass

from claude_code.api.client import (
    APIClient,
    APIClientConfig,
    APIProvider,
    MessageParam,
    QueryOptions,
    ToolParam,
)


@dataclass(frozen=True, slots=True)
class ChatMessage:
    """Chat message for API communication."""
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Tool definition for API."""
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass(frozen=True, slots=True)
class UsageInfo:
    """Token usage information."""
    input_tokens: int
    output_tokens: int
    total_tokens: int


class BaseLLMAdapter(ABC):
    """Base class for LLM provider adapters.
    
    All provider-specific adapters must inherit from this class
    and implement the abstract methods. This ensures a consistent
    interface regardless of the underlying LLM provider.
    
    Subclasses:
        - AnthropicAdapter (built-in, in api/client.py)
        - OpenAIAdapter (requires `openai` package)
        - BedrockAdapter (requires `boto3` package)
        - VertexAdapter (requires `google-auth` package)
        - AzureAdapter (requires `openai` package)
    
    Example:
        >>> class MyAdapter(BaseLLMAdapter):
        ...     async def chat(self, messages, **kwargs):
        ...         ...
        ...     async def chat_once(self, messages, **kwargs):
        ...         ...
        ...     async def close(self):
        ...         ...
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        **kwargs,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._model = model
        self._extra_config = kwargs
    
    @property
    @abstractmethod
    def provider(self) -> str:
        """Return the provider name (e.g., 'anthropic', 'openai')."""
        ...
    
    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        tools: Optional[list[ToolDefinition]] = None,
        max_tokens: int = 8192,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Send a streaming chat request.
        
        Args:
            messages: Conversation messages
            model: Model name override
            tools: Tool definitions
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            system: System prompt
            
        Yields:
            Streaming response chunks
        """
        ...
    
    @abstractmethod
    async def chat_once(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        tools: Optional[list[ToolDefinition]] = None,
        max_tokens: int = 8192,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
    ) -> tuple[str, UsageInfo]:
        """Send a non-streaming chat request.
        
        Args:
            messages: Conversation messages
            model: Model name override
            tools: Tool definitions
            max_tokens: Maximum output tokens
            temperature: Sampling temperature
            system: System prompt
            
        Returns:
            Tuple of (response_content, usage_info)
        """
        ...
    
    async def close(self) -> None:
        """Close the client connection. Override if cleanup needed."""
        pass


class APIClientAdapter(BaseLLMAdapter):
    """Adapter that exposes ``APIClient`` behind the LLM adapter interface."""
    
    def __init__(
        self,
        provider: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        **kwargs,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url, model=model, **kwargs)
        self._provider = provider.lower()
        self._client = APIClient(self._build_client_config(self._provider, kwargs))
    
    @property
    def provider(self) -> str:
        return self._provider
    
    def _build_client_config(self, provider: str, kwargs: dict[str, Any]) -> APIClientConfig:
        if provider == "anthropic":
            return APIClientConfig(
                api_key=self._api_key,
                provider=APIProvider.ANTHROPIC,
                base_url=self._base_url,
            )
        if provider in ("openai", "ollama", "vllm", "deepseek"):
            default_urls = {
                "ollama": "http://localhost:11434/v1",
                "vllm": "http://localhost:8000/v1",
                "deepseek": "https://api.deepseek.com/v1",
            }
            resolved_base_url = self._base_url or default_urls.get(provider)
            return APIClientConfig(
                api_key=self._api_key or "dummy",
                provider=APIProvider.OPENAI,
                base_url=resolved_base_url,
            )
        if provider == "bedrock":
            return APIClientConfig(
                api_key=self._api_key,
                provider=APIProvider.AWS_BEDROCK,
                aws_region=kwargs.get("aws_region", "us-east-1"),
                aws_profile=kwargs.get("aws_profile"),
            )
        if provider == "vertex":
            return APIClientConfig(
                api_key=self._api_key,
                provider=APIProvider.GOOGLE_VERTEX,
                vertex_project=kwargs.get("vertex_project"),
                vertex_location=kwargs.get("vertex_location", "us-central1"),
            )
        if provider == "azure":
            return APIClientConfig(
                api_key=self._api_key,
                provider=APIProvider.AZURE,
                base_url=self._base_url,
                azure_endpoint=kwargs.get("azure_endpoint") or self._base_url,
                azure_api_version=kwargs.get("api_version", "2024-02-15-preview"),
            )
        
        known = ["anthropic", "openai", "ollama", "vllm", "deepseek", "bedrock", "vertex", "azure"]
        raise ValueError(f"Unknown provider: '{provider}'. Known providers: {', '.join(known)}")
    
    @staticmethod
    def _to_message_params(messages: list[ChatMessage]) -> list[MessageParam]:
        return [MessageParam(role=m.role, content=m.content) for m in messages]
    
    @staticmethod
    def _to_tool_params(tools: Optional[list[ToolDefinition]]) -> list[ToolParam]:
        return [
            ToolParam(name=t.name, description=t.description, input_schema=t.input_schema)
            for t in (tools or [])
        ]
    
    @staticmethod
    def _extract_text_from_content(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                elif hasattr(block, "type") and getattr(block, "type", None) == "text":
                    parts.append(str(getattr(block, "text", "")))
                elif hasattr(block, "text"):
                    parts.append(str(getattr(block, "text", "")))
            return "".join(parts)
        return str(content)
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        tools: Optional[list[ToolDefinition]] = None,
        max_tokens: int = 8192,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        options = QueryOptions(
            model=model or self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=self._to_tool_params(tools),
            system=system,
        )
        async for event in self._client.create_message_streaming(self._to_message_params(messages), options):
            if event.type == "text" and event.content:
                yield str(event.content.get("text", ""))
            elif event.type == "message" and event.content:
                content = event.content.get("content")
                text = self._extract_text_from_content(content)
                if text:
                    yield text
            elif event.type == "error":
                raise RuntimeError(event.error or "unknown streaming error")
    
    async def chat_once(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        tools: Optional[list[ToolDefinition]] = None,
        max_tokens: int = 8192,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
    ) -> tuple[str, UsageInfo]:
        options = QueryOptions(
            model=model or self._model,
            max_tokens=max_tokens,
            temperature=temperature,
            tools=self._to_tool_params(tools),
            system=system,
        )
        response = await self._client.create_message(self._to_message_params(messages), options)
        text = self._extract_text_from_content(getattr(response, "content", ""))
        usage_raw = getattr(response, "usage", None)
        if isinstance(usage_raw, dict):
            input_tokens = int(usage_raw.get("input_tokens", 0))
            output_tokens = int(usage_raw.get("output_tokens", 0))
        else:
            input_tokens = int(getattr(usage_raw, "input_tokens", 0) or 0)
            output_tokens = int(getattr(usage_raw, "output_tokens", 0) or 0)
        usage = UsageInfo(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )
        return text, usage


class LLMClientFactory:
    """LLM client factory.
    
    Creates the appropriate API client based on provider configuration.
    Supports graceful degradation when optional packages are missing.
    
    Example:
        >>> factory = LLMClientFactory()
        >>> # Anthropic (always available)
        >>> client = factory.create(provider="anthropic", api_key="sk-...")
        >>> # OpenAI-compatible (requires openai package)
        >>> client = factory.create(provider="openai", base_url="http://localhost:11434")
    """
    
    @classmethod
    def create(
        cls,
        provider: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        **kwargs,
    ) -> BaseLLMAdapter:
        """Create an API client instance.
        
        Args:
            provider: Provider name (anthropic, openai, ollama, vllm, deepseek, bedrock, vertex, azure)
            api_key: API key
            base_url: Base URL (for OpenAI-compatible APIs)
            model: Default model
            **kwargs: Additional provider-specific configuration
            
        Returns:
            BaseLLMAdapter instance
            
        Raises:
            ValueError: Unknown provider
            ImportError: Required package not installed
        """
        return APIClientAdapter(
            provider=provider.lower(),
            api_key=api_key,
            base_url=base_url,
            model=model,
            **kwargs,
        )


# For backward compatibility
APIClientProtocol = BaseLLMAdapter


__all__ = [
    "BaseLLMAdapter",
    "APIClientAdapter",
    "APIClientProtocol",
    "ChatMessage",
    "ToolDefinition",
    "UsageInfo",
    "LLMClientFactory",
]
