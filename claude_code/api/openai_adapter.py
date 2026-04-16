"""OpenAI-compatible adapter compatibility layer.

This module is kept for backward compatibility. Implementation now delegates
to the unified ``APIClientAdapter`` in ``claude_code.api.protocols``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from claude_code.api.protocols import APIClientAdapter


@dataclass
class OpenAIConfig:
    """Configuration for OpenAI-compatible providers."""
    api_key: str
    base_url: Optional[str] = None
    model: str = "gpt-4"
    api_version: Optional[str] = None
    provider_type: str = "openai"


class OpenAIAdapter(APIClientAdapter):
    """Backward-compatible OpenAI adapter backed by ``APIClientAdapter``."""

    def __init__(
        self,
        api_key: str = "dummy",
        base_url: Optional[str] = None,
        model: str = "gpt-4",
        provider_type: str = "openai",
        api_version: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(
            provider=provider_type,
            api_key=api_key,
            base_url=base_url,
            model=model,
            api_version=api_version,
            **kwargs,
        )


__all__ = ["OpenAIAdapter", "OpenAIConfig"]
