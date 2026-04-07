"""
Claude Code Python - API Client Protocols
定义 API 客户端接口，支持多后端实现.

Following TOP Python Dev standards:
- Protocol 抽象接口
- 依赖注入模式
- 多后端支持
"""

from __future__ import annotations

from typing import AsyncGenerator, Protocol, Any, Optional
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


class APIClientProtocol(Protocol):
    """API 客户端协议 (Protocol).
    
    定义 API 客户端必须实现的接口，支持:
    - Anthropic API
    - OpenAI 兼容 API (Ollama, vLLM, etc.)
    - 自定义 LLM 后端
    
    Example:
        >>> # 使用 Protocol 进行依赖注入
        >>> class QueryEngine:
        ...     def __init__(self, api_client: APIClientProtocol):
        ...         self._client = api_client
        ...
        >>> # 支持多种实现
        >>> engine = QueryEngine(AnthropicAPIClient(...))
        >>> engine = QueryEngine(OpenAIAPIClient(...))
        >>> engine = QueryEngine(LocalLLMClient(...))
    """
    
    @property
    def provider(self) -> str:
        """返回 API 提供商名称."""
        ...
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str,
        tools: Optional[list[ToolDefinition]] = None,
        max_tokens: int = 8192,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """发送聊天请求 (流式).
        
        Args:
            messages: 消息列表
            model: 模型名称
            tools: 工具定义列表
            max_tokens: 最大 token 数
            temperature: 温度参数
            system: 系统提示
            
        Yields:
            流式响应内容片段
        """
        ...
    
    async def chat_once(
        self,
        messages: list[ChatMessage],
        model: str,
        tools: Optional[list[ToolDefinition]] = None,
        max_tokens: int = 8192,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
    ) -> tuple[str, UsageInfo]:
        """发送聊天请求 (非流式).
        
        Args:
            messages: 消息列表
            model: 模型名称
            tools: 工具定义列表
            max_tokens: 最大 token 数
            temperature: 温度参数
            system: 系统提示
            
        Returns:
            (响应内容, 使用量信息)
        """
        ...
    
    async def close(self) -> None:
        """关闭客户端连接."""
        ...


class LLMClientFactory:
    """LLM 客户端工厂.
    
    根据配置创建合适的 API 客户端.
    
    Example:
        >>> factory = LLMClientFactory()
        >>> client = factory.create(
        ...     provider="anthropic",
        ...     api_key="sk-..."
        ... )
        >>> # 或创建 OpenAI 兼容客户端
        >>> client = factory.create(
        ...     provider="openai",
        ...     base_url="http://localhost:11434"
        ... )
    """
    
    PROVIDERS = {
        "anthropic": "claude_code.api.anthropic_client",
        "openai": "claude_code.api.openai_client",
        "azure": "claude_code.api.azure_client",
        "bedrock": "claude_code.api.bedrock_client",
        "vertex": "claude_code.api.vertex_client",
    }
    
    @classmethod
    def create(
        cls,
        provider: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: str = "claude-sonnet-4-20250514",
        **kwargs,
    ) -> APIClientProtocol:
        """创建 API 客户端实例.
        
        Args:
            provider: 提供商名称 (anthropic, openai, azure, etc.)
            api_key: API 密钥
            base_url: 基础 URL (用于 OpenAI 兼容 API)
            model: 默认模型
            **kwargs: 其他提供商特定配置
            
        Returns:
            APIClientProtocol 实现实例
        """
        provider = provider.lower()
        
        if provider == "anthropic":
            from claude_code.api.client import APIClient, APIClientConfig, APIProvider
            config = APIClientConfig(
                api_key=api_key,
                provider=APIProvider.ANTHROPIC,
                base_url=base_url,
            )
            return APIClient(config)
        
        elif provider == "openai" or provider == "ollama" or provider == "vllm":
            # 尝试导入 OpenAI 兼容客户端
            try:
                from claude_code.api.openai_client import OpenAIClient
                return OpenAIClient(
                    api_key=api_key or "dummy",
                    base_url=base_url or "http://localhost:11434",
                    model=model,
                )
            except ImportError:
                raise ImportError(
                    f"OpenAI-compatible client not available. "
                    f"Install with: pip install openai"
                )
        
        elif provider == "azure":
            from claude_code.api.client import APIClient, APIClientConfig, APIProvider
            config = APIClientConfig(
                api_key=api_key,
                provider=APIProvider.AZURE,
                base_url=base_url,
                azure_endpoint=base_url,
                **kwargs,
            )
            return APIClient(config)
        
        elif provider == "bedrock":
            from claude_code.api.client import APIClient, APIClientConfig, APIProvider
            config = APIClientConfig(
                api_key=api_key,
                provider=APIProvider.AWS_BEDROCK,
                aws_region=kwargs.get("aws_region", "us-east-1"),
                **kwargs,
            )
            return APIClient(config)
        
        else:
            raise ValueError(f"Unknown provider: {provider}")


__all__ = [
    "APIClientProtocol",
    "ChatMessage",
    "ToolDefinition",
    "UsageInfo",
    "LLMClientFactory",
]