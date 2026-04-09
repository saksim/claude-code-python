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
        provider_lower = provider.lower()
        
        if provider_lower == "anthropic":
            from claude_code.api.client import APIClient, APIClientConfig, APIProvider
            config = APIClientConfig(
                api_key=api_key,
                provider=APIProvider.ANTHROPIC,
                base_url=base_url,
            )
            return APIClient(config)
        
        elif provider_lower in ("openai", "ollama", "vllm", "deepseek"):
            default_urls = {
                "ollama": "http://localhost:11434/v1",
                "vllm": "http://localhost:8000/v1",
                "deepseek": "https://api.deepseek.com/v1",
            }
            resolved_url = base_url or default_urls.get(provider_lower, base_url)
            try:
                from claude_code.api.openai_adapter import OpenAIAdapter
                return OpenAIAdapter(
                    api_key=api_key or "dummy",
                    base_url=resolved_url or base_url,
                    model=model,
                )
            except ImportError:
                raise ImportError(
                    f"OpenAI-compatible provider '{provider}' requires the 'openai' package. "
                    f"Install with: pip install openai"
                )
        
        elif provider_lower == "azure":
            try:
                from claude_code.api.openai_adapter import OpenAIAdapter
                azure_endpoint = base_url or kwargs.get("azure_endpoint")
                api_version = kwargs.get("api_version", "2024-02-15-preview")
                return OpenAIAdapter(
                    api_key=api_key,
                    base_url=azure_endpoint,
                    model=model,
                    provider_type="azure",
                    api_version=api_version,
                )
            except ImportError:
                raise ImportError(
                    f"Azure OpenAI provider requires the 'openai' package. "
                    f"Install with: pip install openai"
                )
        
        elif provider_lower == "bedrock":
            from claude_code.api.client import APIClient, APIClientConfig, APIProvider
            config = APIClientConfig(
                api_key=api_key,
                provider=APIProvider.AWS_BEDROCK,
                aws_region=kwargs.get("aws_region", "us-east-1"),
            )
            return APIClient(config)
        
        elif provider_lower == "vertex":
            from claude_code.api.client import APIClient, APIClientConfig, APIProvider
            config = APIClientConfig(
                api_key=api_key,
                provider=APIProvider.GOOGLE_VERTEX,
                vertex_project=kwargs.get("vertex_project"),
                vertex_location=kwargs.get("vertex_location", "us-central1"),
            )
            return APIClient(config)
        
        else:
            known_providers = ["anthropic", "openai", "ollama", "vllm", "deepseek", "bedrock", "vertex", "azure"]
            raise ValueError(
                f"Unknown provider: '{provider}'. "
                f"Known providers: {', '.join(known_providers)}"
            )


# For backward compatibility
APIClientProtocol = BaseLLMAdapter


__all__ = [
    "BaseLLMAdapter",
    "APIClientProtocol",
    "ChatMessage",
    "ToolDefinition",
    "UsageInfo",
    "LLMClientFactory",
]