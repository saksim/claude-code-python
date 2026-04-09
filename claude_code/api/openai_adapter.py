"""
Claude Code Python - OpenAI-Compatible Adapter

Adapter for OpenAI-compatible LLM providers (OpenAI, Ollama, vLLM, DeepSeek, etc.)
Converts between Anthropic API format and OpenAI Chat Completions format.

Requires: pip install openai
"""

from __future__ import annotations

from typing import AsyncGenerator, Optional
from dataclasses import dataclass

from claude_code.api.protocols import (
    BaseLLMAdapter,
    ChatMessage,
    ToolDefinition,
    UsageInfo,
)


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI-compatible providers."""
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-4"
    api_version: Optional[str] = None
    provider_type: str = "openai"


class OpenAIAdapter(BaseLLMAdapter):
    """Adapter for OpenAI-compatible LLM providers.
    
    Supports OpenAI, Ollama, vLLM, DeepSeek, and Azure OpenAI endpoints.
    Converts between Anthropic message format and OpenAI format.
    
    Example:
        >>> adapter = OpenAIAdapter(
        ...     api_key="sk-...",
        ...     base_url="http://localhost:11434/v1",
        ...     model="llama3",
        ... )
        >>> async for chunk in adapter.chat(messages):
        ...     print(chunk, end="")
    """
    
    def __init__(
        self,
        api_key: str = "dummy",
        base_url: Optional[str] = None,
        model: str = "gpt-4",
        provider_type: str = "openai",
        api_version: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(api_key=api_key, base_url=base_url, model=model, **kwargs)
        self._provider_type = provider_type
        self._api_version = api_version
        self._client = None
    
    @property
    def provider(self) -> str:
        return self._provider_type
    
    def _get_client(self):
        """Lazily create the OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
            except ImportError:
                raise ImportError(
                    "OpenAI package is required for OpenAI-compatible providers. "
                    "Install with: pip install openai"
                )
            
            kwargs = {
                "api_key": self._api_key,
            }
            if self._base_url:
                kwargs["base_url"] = self._base_url
            if self._provider_type == "azure" and self._api_version:
                kwargs["default_headers"] = {
                    "api-key": self._api_key,
                }
                kwargs["api_version"] = self._api_version
            
            self._client = AsyncOpenAI(**kwargs)
        return self._client
    
    @staticmethod
    def _convert_messages(messages: list[ChatMessage], system: Optional[str] = None) -> list[dict]:
        """Convert Anthropic-format messages to OpenAI format."""
        openai_messages = []
        
        if system:
            openai_messages.append({"role": "system", "content": system})
        
        for msg in messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content,
            })
        
        return openai_messages
    
    @staticmethod
    def _convert_tools(tools: Optional[list[ToolDefinition]] = None) -> Optional[list[dict]]:
        """Convert Anthropic-format tools to OpenAI format."""
        if not tools:
            return None
        
        openai_tools = []
        for tool in tools:
            openai_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                }
            })
        return openai_tools
    
    @staticmethod
    def _convert_model(model: str) -> str:
        """Convert Anthropic model name to a suitable OpenAI-equivalent."""
        model_mapping = {
            "claude-sonnet-4-20250514": "gpt-4",
            "claude-opus-4-20250514": "gpt-4-turbo",
            "claude-haiku-4-20250514": "gpt-3.5-turbo",
            "sonnet": "gpt-4",
            "opus": "gpt-4-turbo",
            "haiku": "gpt-3.5-turbo",
        }
        return model_mapping.get(model, model)
    
    async def chat(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        tools: Optional[list[ToolDefinition]] = None,
        max_tokens: int = 8192,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion using OpenAI API."""
        client = self._get_client()
        openai_messages = self._convert_messages(messages, system)
        resolved_model = self._convert_model(model or self._model)
        openai_tools = self._convert_tools(tools)
        
        kwargs = {
            "model": resolved_model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        if openai_tools:
            kwargs["tools"] = openai_tools
        
        response = await client.chat.completions.create(**kwargs)
        
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def chat_once(
        self,
        messages: list[ChatMessage],
        model: Optional[str] = None,
        tools: Optional[list[ToolDefinition]] = None,
        max_tokens: int = 8192,
        temperature: Optional[float] = None,
        system: Optional[str] = None,
    ) -> tuple[str, UsageInfo]:
        """Non-streaming chat completion using OpenAI API."""
        client = self._get_client()
        openai_messages = self._convert_messages(messages, system)
        resolved_model = self._convert_model(model or self._model)
        openai_tools = self._convert_tools(tools)
        
        kwargs = {
            "model": resolved_model,
            "messages": openai_messages,
            "max_tokens": max_tokens,
        }
        if temperature is not None:
            kwargs["temperature"] = temperature
        if openai_tools:
            kwargs["tools"] = openai_tools
        
        response = await client.chat.completions.create(**kwargs)
        
        content = response.choices[0].message.content or ""
        usage = UsageInfo(
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
            total_tokens=response.usage.total_tokens if response.usage else 0,
        )
        
        return content, usage
    
    async def close(self) -> None:
        """Close the OpenAI client."""
        if self._client:
            await self._client.close()
            self._client = None


__all__ = ["OpenAIAdapter", "OpenAIConfig"]