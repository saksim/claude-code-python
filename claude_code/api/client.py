"""
Claude Code Python - Core API Client
Handles communication with Anthropic API and other providers.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns for configuration
- Multiple provider support (Anthropic, AWS Bedrock, Google Vertex, Azure)
- Async/await patterns
"""

from __future__ import annotations

import os
import json
import asyncio
from typing import AsyncGenerator, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import Message, TextBlock, ToolUseBlock, ContentBlock


class APIProvider(Enum):
    """API provider types.
    
    Attributes:
        ANTHROPIC: Anthropic's Claude API
        OPENAI: OpenAI-compatible Chat Completions API
        AWS_BEDROCK: AWS Bedrock (via Amazon Nova, Anthropic models)
        GOOGLE_VERTEX: Google Vertex AI (via Gemini, Claude)
        AZURE: Azure OpenAI compatible API
    """
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    AWS_BEDROCK = "bedrock"
    GOOGLE_VERTEX = "vertex"
    AZURE = "azure"


@dataclass(frozen=True, slots=True)
class APIClientConfig:
    """Configuration for API client.
    
    Using frozen=True, slots=True for immutability and memory efficiency.
    
    Attributes:
        api_key: API key for authentication
        provider: API provider to use
        base_url: Optional custom base URL
        max_retries: Maximum number of retries
        timeout: Request timeout in seconds
        aws_region: AWS region for Bedrock
        aws_profile: AWS profile for Bedrock
        vertex_project: Google Cloud project for Vertex
        vertex_location: Google Cloud location for Vertex
        azure_endpoint: Azure OpenAI endpoint
        azure_api_version: Azure API version
    """
    api_key: Optional[str] = None
    provider: APIProvider = APIProvider.ANTHROPIC
    base_url: Optional[str] = None
    max_retries: int = 3
    timeout: float = 120.0
    
    # Provider-specific settings
    aws_region: Optional[str] = None
    aws_profile: Optional[str] = None
    vertex_project: Optional[str] = None
    vertex_location: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_api_version: str = "2024-01-01"


@dataclass(frozen=True, slots=True)
class MessageParam:
    """A message in the conversation.
    
    Using frozen=True, slots=True for immutability.
    
    Attributes:
        role: Message role (user, assistant, system)
        content: Message content (text or list of content blocks)
    """
    role: str
    content: str | list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class ToolParam:
    """A tool definition for the API.
    
    Attributes:
        name: Tool name
        description: Tool description
        input_schema: JSON schema for tool input
    """
    name: str
    description: str
    input_schema: dict[str, Any]


@dataclass
class QueryOptions:
    """Options for a query request.
    
    Attributes:
        model: Model identifier
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature (0-1)
        tools: List of available tools
        system: System prompt
        thinking: Thinking configuration (type, budget_tokens)
        metadata: Optional metadata for the request
    """
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 8192
    temperature: Optional[float] = None
    tools: list[ToolParam] = field(default_factory=list)
    system: Optional[str] = None
    thinking: Optional[dict[str, Any]] = None
    metadata: Optional[dict[str, Any]] = None


@dataclass(frozen=True, slots=True)
class StreamEvent:
    """An event from the streaming response.
    
    Attributes:
        type: Event type (content_block_delta, message_start, etc.)
        content: Optional content data
        usage: Optional token usage data
        error: Optional error message
    """
    type: str
    content: Optional[dict[str, Any]] = None
    usage: Optional[dict[str, Any]] = None
    error: Optional[str] = None


class APIClientError(Exception):
    """Base exception for API errors.
    
    Attributes:
        message: Error message
        status: Optional HTTP status code
    
    Example:
        >>> try:
        ...     await client.create_message(messages, options)
        ... except APIClientError as e:
        ...     print(f"API error: {e.message}, status: {e.status}")
    """
    def __init__(self, message: str, status: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status = status


class RateLimitError(APIClientError):
    """Rate limit exceeded."""
    pass


class AuthenticationError(APIClientError):
    """Authentication failed."""
    pass


class ContextLengthError(APIClientError):
    """Context too long."""
    pass


class APIRetryableError(APIClientError):
    """Error that can be retried."""
    pass


class APIClient:
    """
    Core API client for Claude Code.
    Supports multiple providers: Anthropic, AWS Bedrock, Google Vertex, Azure.
    
    Features:
    - Connection reuse via persistent client
    - Retry with exponential backoff and jitter
    - Streaming and non-streaming API calls
    """
    
    def __init__(self, config: APIClientConfig, retry_config: RetryConfig | None = None):
        self.config = config
        self._client: Optional[AsyncAnthropic] = None
        self._retry_config = retry_config or RetryConfig()
        self._setup_client()
    
    def _setup_client(self):
        """Initialize the API client based on provider."""
        if self.config.provider == APIProvider.ANTHROPIC:
            self._client = AsyncAnthropic(
                api_key=self.config.api_key or os.getenv("ANTHROPIC_API_KEY"),
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
        elif self.config.provider == APIProvider.OPENAI:
            self._setup_openai()
        elif self.config.provider == APIProvider.AWS_BEDROCK:
            self._setup_bedrock()
        elif self.config.provider == APIProvider.GOOGLE_VERTEX:
            self._setup_vertex()
        elif self.config.provider == APIProvider.AZURE:
            raise NotImplementedError(
                "Azure provider is temporarily unavailable in this build. "
                "Please use anthropic/bedrock/vertex until azure adapter is fully wired."
            )
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")
    
    def _setup_bedrock(self):
        """Setup AWS Bedrock client."""
        try:
            import boto3
            from anthropic import AsyncAnthropicBedrock
            
            # Use AWS credentials from environment or profile
            region = self.config.aws_region or os.getenv("AWS_REGION", "us-east-1")
            
            self._client = AsyncAnthropicBedrock(
                aws_region=region,
                aws_profile=self.config.aws_profile,
            )
        except ImportError:
            raise ImportError("boto3 required for AWS Bedrock. Install with: pip install boto3")
    
    def _setup_openai(self):
        """Setup OpenAI-compatible client."""
        try:
            from openai import AsyncOpenAI
            
            self._client = AsyncOpenAI(
                api_key=self.config.api_key or os.getenv("OPENAI_API_KEY") or "dummy",
                base_url=self.config.base_url or os.getenv("OPENAI_BASE_URL"),
                timeout=self.config.timeout,
            )
        except ImportError:
            raise ImportError("openai required for OpenAI provider. Install with: pip install openai")
    
    def _setup_vertex(self):
        """Setup Google Vertex AI client."""
        try:
            import google.auth
            import google.auth.transport.requests as requests
            
            credentials, project = google.auth.default()
            
            self._client = AsyncAnthropic(
                api_key=None,  # Auth handled by Google credentials
                base_url=f"https://{self.config.vertex_location or 'us-central1'}-aiplatform.googleapis.com/v1beta1/projects/{self.config.vertex_project or project}/locations/{self.config.vertex_location or 'us-central1'}/publishers/anthropic/models",
            )
        except ImportError:
            raise ImportError("google-auth required for Vertex. Install with: pip install google-auth")
    
    def _setup_azure(self):
        """Setup Azure OpenAI client."""
        try:
            from openai import AsyncAzureOpenAI
            
            self._client = AsyncAzureOpenAI(
                api_key=self.config.api_key or os.getenv("AZURE_OPENAI_API_KEY"),
                azure_endpoint=self.config.azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT"),
                api_version=self.config.azure_api_version,
            )
        except ImportError:
            raise ImportError("openai required for Azure. Install with: pip install openai")
    
    async def create_message(
        self,
        messages: list[MessageParam],
        options: QueryOptions,
    ) -> Message:
        """
        Create a non-streaming message request.
        
        Args:
            messages: List of conversation messages
            options: Query options including model, tools, etc.
            
        Returns:
            API response message
        """
        if not self._client:
            raise APIClientError("API client not initialized")
        
        if self.config.provider == APIProvider.OPENAI:
            return await self._create_message_openai(messages, options)
        
        # Convert messages to API format
        api_messages = self._format_messages(messages)
        
        # Build request params
        params = {
            "model": options.model,
            "max_tokens": options.max_tokens,
            "messages": api_messages,
        }
        
        if options.temperature is not None:
            params["temperature"] = options.temperature
        
        if options.system:
            params["system"] = options.system
        
        if options.tools:
            params["tools"] = [self._format_tool(t) for t in options.tools]
        
        if options.thinking:
            params["thinking"] = options.thinking
        
        if options.metadata:
            params["metadata"] = options.metadata
        
        try:
            async def _call():
                return await self._client.messages.create(**params)
            
            response = await with_retry(_call, self._retry_config)
            return response
        except Exception as e:
            raise self._handle_error(e)
    
    async def _create_message_openai(
        self,
        messages: list[MessageParam],
        options: QueryOptions,
    ) -> Message:
        """Create a non-streaming message request via OpenAI-compatible API."""
        api_messages = self._format_openai_messages(messages, options.system)
        
        params: dict[str, Any] = {
            "model": options.model,
            "messages": api_messages,
            "max_tokens": options.max_tokens,
        }
        if options.temperature is not None:
            params["temperature"] = options.temperature
        if options.tools:
            params["tools"] = [self._format_openai_tool(t) for t in options.tools]
            params["tool_choice"] = "auto"
        
        try:
            response = await self._client.chat.completions.create(**params)
            choice = response.choices[0].message
            content_blocks: list[dict[str, Any]] = []
            
            if choice.content:
                content_blocks.append({"type": "text", "text": choice.content})
            
            tool_calls = getattr(choice, "tool_calls", None) or []
            for tool_call in tool_calls:
                args_str = getattr(tool_call.function, "arguments", "") or "{}"
                try:
                    parsed_input = json.loads(args_str)
                except Exception:
                    parsed_input = {"_raw": args_str}
                content_blocks.append({
                    "type": "tool_use",
                    "id": getattr(tool_call, "id", ""),
                    "name": getattr(tool_call.function, "name", ""),
                    "input": parsed_input,
                })
            
            class _Response:
                def __init__(self, content, usage):
                    self.content = content
                    self.usage = usage
            
            usage_obj = getattr(response, "usage", None)
            usage = {
                "input_tokens": getattr(usage_obj, "prompt_tokens", 0) if usage_obj else 0,
                "output_tokens": getattr(usage_obj, "completion_tokens", 0) if usage_obj else 0,
            }
            return _Response(content_blocks, usage)
        except Exception as e:
            raise self._handle_error(e)
    
    async def create_message_streaming(
        self,
        messages: list[MessageParam],
        options: QueryOptions,
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Create a streaming message request.
        
        Args:
            messages: List of conversation messages
            options: Query options including model, tools, etc.
            
        Yields:
            Stream events as they arrive
        """
        if not self._client:
            raise APIClientError("API client not initialized")
        
        if self.config.provider == APIProvider.OPENAI:
            try:
                response = await self._create_message_openai(messages, options)
                yield StreamEvent(
                    type="message",
                    content={"content": response.content},
                    usage=response.usage,
                )
            except Exception as e:
                yield StreamEvent(type="error", error=str(e))
            return
        
        api_messages = self._format_messages(messages)
        
        params = {
            "model": options.model,
            "max_tokens": options.max_tokens,
            "messages": api_messages,
            "stream": True,
        }
        
        if options.temperature is not None:
            params["temperature"] = options.temperature
        
        if options.system:
            params["system"] = options.system
        
        if options.tools:
            params["tools"] = [self._format_tool(t) for t in options.tools]
        
        if options.thinking:
            params["thinking"] = options.thinking
        
        try:
            async with self._client.messages.stream(**params) as stream:
                async for text_event in stream.text_stream:
                    yield StreamEvent(type="text", content={"text": text_event})
                
                message = await stream.get_final_message()
                yield StreamEvent(
                    type="message",
                    content={"content": message.content},
                    usage={
                        "input_tokens": message.usage.input_tokens,
                        "output_tokens": message.usage.output_tokens,
                    }
                )
        except Exception as e:
            yield StreamEvent(type="error", error=str(e))
    
    def _format_messages(self, messages: list[MessageParam]) -> list[dict]:
        """Convert MessageParam to API format.
        
        Optimized to avoid redundant isinstance check — both str
        and list content use the same dict structure.
        """
        return [{"role": msg.role, "content": msg.content} for msg in messages]
    
    def _format_openai_messages(
        self,
        messages: list[MessageParam],
        system: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Convert internal message format to OpenAI chat format."""
        openai_messages: list[dict[str, Any]] = []
        if system:
            openai_messages.append({"role": "system", "content": system})
        
        for msg in messages:
            content = msg.content
            if isinstance(content, str):
                openai_messages.append({"role": msg.role, "content": content})
                continue
            
            if not isinstance(content, list):
                openai_messages.append({"role": msg.role, "content": str(content)})
                continue
            
            text_parts: list[str] = []
            tool_calls: list[dict[str, Any]] = []
            emitted_tool_result = False
            for block in content:
                if not isinstance(block, dict):
                    text_parts.append(str(block))
                    continue
                block_type = block.get("type")
                if block_type == "text":
                    text_parts.append(str(block.get("text", "")))
                elif block_type == "tool_use":
                    tool_calls.append({
                        "id": block.get("id", ""),
                        "type": "function",
                        "function": {
                            "name": block.get("name", ""),
                            "arguments": json.dumps(block.get("input", {}), ensure_ascii=False),
                        },
                    })
                elif block_type == "tool_result":
                    emitted_tool_result = True
                    openai_messages.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id", ""),
                        "content": str(block.get("content", "")),
                    })
            
            if tool_calls and msg.role == "assistant":
                openai_messages.append({
                    "role": "assistant",
                    "content": "".join(text_parts) if text_parts else None,
                    "tool_calls": tool_calls,
                })
            else:
                if text_parts or not emitted_tool_result:
                    openai_messages.append({
                        "role": msg.role,
                        "content": "".join(text_parts),
                    })
        
        return openai_messages
    
    def _format_openai_tool(self, tool: ToolParam) -> dict[str, Any]:
        """Format a tool for OpenAI Chat Completions."""
        return {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
            },
        }
    
    def _format_tool(self, tool: ToolParam) -> dict:
        """Format a tool for the API."""
        return {
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_schema,
        }
    
    def _handle_error(self, error: Exception) -> APIClientError:
        """Convert exceptions to API errors."""
        error_str = str(error)
        
        if "401" in error_str or "authentication" in error_str.lower():
            return AuthenticationError(f"Authentication failed: {error_str}")
        
        if "429" in error_str or "rate_limit" in error_str.lower():
            return RateLimitError(f"Rate limit exceeded: {error_str}")
        
        if "context_length" in error_str.lower() or "400" in error_str:
            return ContextLengthError(f"Context too long: {error_str}")
        
        if any(x in error_str.lower() for x in ["500", "502", "503", "504"]):
            return APIRetryableError(f"Retryable error: {error_str}")
        
        return APIClientError(f"API error: {error_str}")


class RetryConfig:
    """Configuration for API retry behavior.
    
    Attributes:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        max_delay: Maximum delay between retries
        exponential_base: Base for exponential backoff
        retryable_status_codes: HTTP status codes that trigger retry
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_status_codes: set[int] | None = None,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_status_codes = retryable_status_codes or {429, 500, 502, 503, 504}
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given retry attempt with optional jitter.
        
        Args:
            attempt: Zero-based retry attempt number
            
        Returns:
            Delay in seconds
        """
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay,
        )
        if self.jitter:
            import random
            delay *= (0.5 + random.random())
        return delay


async def with_retry(
    coro,
    config: RetryConfig,
    should_retry: callable = None,
) -> Any:
    """
    Execute a coroutine with retry logic and exponential backoff.
    
    Args:
        coro: Coroutine factory to execute (called repeatedly)
        config: Retry configuration
        should_retry: Optional function to determine if error is retryable
        
    Returns:
        Result of the coroutine
    """
    last_error = None
    
    for attempt in range(config.max_retries + 1):
        try:
            return await coro()
        except Exception as e:
            last_error = e
            
            if attempt == config.max_retries:
                break
            
            if should_retry and not should_retry(e):
                break
            
            if isinstance(e, APIClientError):
                if e.status and e.status not in config.retryable_status_codes:
                    break
            
            await asyncio.sleep(config.get_delay(attempt))
    
    raise last_error
