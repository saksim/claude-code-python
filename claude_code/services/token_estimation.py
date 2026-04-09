"""
Token estimation service for Claude Code Python.

Provides accurate token counting for API calls and rough estimation
for quick calculations without API calls.

Following TOP Python Dev standards:
- Clear type hints
- Comprehensive docstrings
- Dataclass patterns (frozen/slots)
- Module-level constants
- Pydantic for complex validation
"""

from __future__ import annotations

import json
from typing import Any, Optional
from enum import Enum


class ProviderType(Enum):
    """API provider types."""
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    VERTEX = "vertex"
    GEMINI = "gemini"
    AZURE = "azure"


# Average characters per token for different content types
BYTES_PER_TOKEN_ENGLISH: int = 4
BYTES_PER_TOKEN_JSON: int = 2

# Thinking budget tokens for API counting
TOKEN_COUNT_THINKING_BUDGET: int = 1024
TOKEN_COUNT_MAX_TOKENS: int = 2048

# Image token estimation constants
IMAGE_MAX_TOKEN_SIZE: int = 2000  # Conservative estimate for resized images


def has_thinking_blocks(messages: list[dict[str, Any]]) -> bool:
    """Check if messages contain thinking blocks.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        True if any message contains thinking blocks
    """
    for message in messages:
        if message.get('role') == 'assistant':
            content = message.get('content', [])
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get('type') in ('thinking', 'redacted_thinking'):
                        return True
    return False


def strip_tool_search_fields(
    messages: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """Strip tool search-specific fields from messages.
    
    Removes 'caller' from tool_use blocks and 'tool_reference' from 
    tool_result content. These fields are only valid with the tool 
    search beta and will cause errors otherwise.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        Messages with tool search fields stripped
    """
    def is_tool_reference_block(block: dict[str, Any]) -> bool:
        return isinstance(block, dict) and block.get('type') == 'tool_reference'
    
    result = []
    for message in messages:
        msg = dict(message)
        content = msg.get('content')
        
        if not isinstance(content, list):
            result.append(msg)
            continue
        
        normalized_content = []
        for block in content:
            if not isinstance(block, dict):
                normalized_content.append(block)
                continue
            
            block_type = block.get('type')
            
            # Strip 'caller' from tool_use blocks
            if block_type == 'tool_use':
                normalized_content.append({
                    'type': 'tool_use',
                    'id': block.get('id'),
                    'name': block.get('name'),
                    'input': block.get('input'),
                })
            
            # Strip tool_reference from tool_result
            elif block_type == 'tool_result':
                result_content = block.get('content')
                if isinstance(result_content, list):
                    filtered = [c for c in result_content if not is_tool_reference_block(c)]
                    if not filtered:
                        normalized_content.append({
                            **block,
                            'content': [{'type': 'text', 'text': '[tool references]'}],
                        })
                    elif len(filtered) != len(result_content):
                        normalized_content.append({
                            **block,
                            'content': filtered,
                        })
                    else:
                        normalized_content.append(block)
                else:
                    normalized_content.append(block)
            else:
                normalized_content.append(block)
        
        msg['content'] = normalized_content
        result.append(msg)
    
    return result


def bytes_per_token_for_file_type(file_extension: str) -> int:
    """Returns an estimated bytes-per-token ratio for a given file extension.
    
    Dense JSON has many single-character tokens ({, }, :, ,, ")
    which makes the real ratio closer to 2 rather than the default 4.
    
    Args:
        file_extension: File extension (e.g., "py", "json")
        
    Returns:
        Estimated bytes per token
    """
    if file_extension.lower() in ('json', 'jsonl', 'jsonc'):
        return BYTES_PER_TOKEN_JSON
    return BYTES_PER_TOKEN_ENGLISH


class TokenEstimator:
    """Token estimation service.
    
    Supports both API-based counting (accurate but requires API call)
    and rough estimation (fast but approximate).
    
    Attributes:
        api_client: Optional API client for accurate counting
    
    Example:
        >>> estimator = TokenEstimator()
        >>> tokens = estimator.rough_estimate("Hello, world!")
        >>> print(f"Estimated: {tokens} tokens")
    """
    
    def __init__(self, api_client: Optional[Any] = None):
        self._api_client = api_client
        self._provider: ProviderType = ProviderType.ANTHROPIC
    
    @property
    def api_client(self) -> Optional[Any]:
        """Get the API client for accurate counting."""
        return self._api_client
    
    @api_client.setter
    def api_client(self, client: Optional[Any]) -> None:
        """Set the API client for accurate counting."""
        self._api_client = client
    
    @property
    def provider(self) -> ProviderType:
        """Get the API provider type."""
        return self._provider
    
    @provider.setter
    def provider(self, provider: ProviderType) -> None:
        """Set the API provider type."""
        self._provider = provider
    
    def rough_estimate(self, content: str) -> int:
        """Rough token estimation using character count.
        
        Uses 4 chars/token for English text, 2 chars/token for JSON.
        Uses round() for better accuracy on short texts.

        Args:
            content: Text content to estimate
            
        Returns:
            Estimated token count.
        """
        if not content:
            return 0
        
        if content.strip().startswith(('{', '[')):
            try:
                json.loads(content)
                return round(len(content) / BYTES_PER_TOKEN_JSON)
            except json.JSONDecodeError:
                pass
        
        return round(len(content) / BYTES_PER_TOKEN_ENGLISH)
    
    def estimate_for_file(self, content: str, file_extension: str) -> int:
        """Estimate tokens for a file based on its extension.
        
        Args:
            content: File content to estimate
            file_extension: File extension (e.g., "py", "json")
            
        Returns:
            Estimated token count.
        """
        if not content:
            return 0
        
        bytes_per_token = bytes_per_token_for_file_type(file_extension)
        return round(len(content) / bytes_per_token)
    
    def estimate_for_messages(self, messages: list[dict[str, Any]]) -> int:
        """Estimate total tokens for a list of messages.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Total estimated token count.
        """
        total = 0
        for msg in messages:
            total += self.estimate_message_tokens(msg)
        return total
    
    def estimate_message_tokens(self, message: dict[str, Any]) -> int:
        """Estimate tokens for a single message.
        
        Args:
            message: Message dictionary
            
        Returns:
            Estimated token count for the message.
        """
        content = message.get('content', '')
        msg_type = message.get('type', message.get('role', 'unknown'))
        
        if isinstance(content, str):
            return self.rough_estimate(content)
        elif isinstance(content, list):
            total = 0
            for block in content:
                total += self.estimate_content_block(block)
            return total
        
        return self.rough_estimate(str(content))
    
    def estimate_content_block(self, block: dict[str, Any]) -> int:
        """Estimate tokens for a content block.
        
        Supports: text, image, document, tool_result, tool_use, thinking, redacted_thinking.
        
        Args:
            block: Content block dictionary
            
        Returns:
            Estimated token count for the block.
        """
        if not isinstance(block, dict):
            return self.rough_estimate(str(block))
        
        block_type = block.get('type', '')
        
        if block_type == 'text':
            return self.rough_estimate(block.get('text', ''))
        
        elif block_type == 'image':
            return IMAGE_MAX_TOKEN_SIZE
        
        elif block_type == 'document':
            return IMAGE_MAX_TOKEN_SIZE
        
        elif block_type == 'tool_result':
            inner = block.get('content', '')
            if isinstance(inner, str):
                return self.rough_estimate(inner)
            elif isinstance(inner, list):
                return sum(self.estimate_content_block(c) for c in inner)
            return 0
        
        elif block_type == 'tool_use':
            name = block.get('name', '')
            inp = block.get('input', {})
            inp_str = json.dumps(inp) if isinstance(inp, dict) else str(inp)
            return self.rough_estimate(name + inp_str)
        
        elif block_type == 'thinking':
            return self.rough_estimate(block.get('thinking', ''))
        
        elif block_type == 'redacted_thinking':
            return self.rough_estimate(block.get('data', ''))
        
        else:
            return self.rough_estimate(json.dumps(block))
    
    async def count_tokens_with_api(
        self,
        content: str,
        model: str = "claude-sonnet-4-20250514",
    ) -> Optional[int]:
        """Count tokens using the API (accurate but requires API call).
        
        Falls back to rough estimation if API call fails.
        
        Args:
            content: Text content to count
            model: Model to use for counting
            
        Returns:
            Token count or None if counting fails.
        """
        if not self._api_client:
            return self.rough_estimate(content)
        
        # Gemini uses rough estimation
        if self._provider == ProviderType.GEMINI:
            return self.estimate_for_messages([{'role': 'user', 'content': content}])
        
        try:
            result = await self._api_client.count_tokens(content, model=model)
            return result
        except Exception:
            return self.rough_estimate(content)
    
    async def count_messages_tokens(
        self,
        messages: list[dict[str, Any]],
        tools: Optional[list[dict[str, Any]]] = None,
        model: str = "claude-sonnet-4-20250514",
        enable_thinking: bool = False,
    ) -> Optional[int]:
        """Count tokens for messages using the API.
        
        Falls back to rough estimation if API call fails.
        
        Args:
            messages: List of message dictionaries
            tools: Optional list of tool definitions
            model: Model to use for counting
            enable_thinking: Enable thinking in API call
            
        Returns:
            Token count or None if counting fails.
        """
        if not self._api_client:
            return self.estimate_for_messages(messages)
        
        # Gemini uses rough estimation
        if self._provider == ProviderType.GEMINI:
            return self.estimate_for_messages(messages) + (
                self.rough_estimate(json.dumps(tools)) if tools else 0
            )
        
        try:
            # Strip tool search fields if needed
            processed_messages = strip_tool_search_fields(messages)
            
            result = await self._api_client.count_messages_tokens(
                processed_messages,
                tools or [],
                model=model,
                thinking={'type': 'enabled', 'budget_tokens': TOKEN_COUNT_THINKING_BUDGET} if enable_thinking else None,
            )
            return result
        except Exception:
            return self.estimate_for_messages(messages)


# Global singleton instance
_estimator: Optional[TokenEstimator] = None


def get_token_estimator() -> TokenEstimator:
    """Get the global token estimator instance.
    
    Returns:
        The global TokenEstimator singleton.
    """
    global _estimator
    if _estimator is None:
        _estimator = TokenEstimator()
    return _estimator


def set_token_estimator(estimator: TokenEstimator) -> None:
    """Set the global token estimator instance.
    
    Args:
        estimator: TokenEstimator instance to use globally.
    """
    global _estimator
    _estimator = estimator


def set_provider(provider: ProviderType) -> None:
    """Set the API provider type.
    
    Args:
        provider: ProviderType to use.
    """
    get_token_estimator().provider = provider


def rough_token_count(content: str) -> int:
    """Quick rough token estimation.
    
    Args:
        content: Text content to estimate
        
    Returns:
        Estimated token count.
    """
    return get_token_estimator().rough_estimate(content)


def estimate_message_tokens(message: dict[str, Any]) -> int:
    """Estimate tokens for a message.
    
    Args:
        message: Message dictionary
        
    Returns:
        Estimated token count.
    """
    return get_token_estimator().estimate_message_tokens(message)


__all__ = [
    "ProviderType",
    "TOKEN_COUNT_THINKING_BUDGET",
    "TOKEN_COUNT_MAX_TOKENS",
    "IMAGE_MAX_TOKEN_SIZE",
    "has_thinking_blocks",
    "strip_tool_search_fields",
    "bytes_per_token_for_file_type",
    "TokenEstimator",
    "get_token_estimator",
    "set_token_estimator",
    "set_provider",
    "rough_token_count",
    "estimate_message_tokens",
]
