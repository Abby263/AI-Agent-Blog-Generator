"""Factory for LLM clients."""

from __future__ import annotations

from ..config.settings import AppSettings, ModelConfig
from .base import BaseLLMClient
from .openai_compatible import OpenAICompatibleLLMClient


def build_llm_client(config: ModelConfig, settings: AppSettings) -> BaseLLMClient:
    """Construct the configured LLM client."""

    if config.provider != "openai":
        raise ValueError(f"Unsupported model provider: {config.provider}")
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is required for live model execution")
    return OpenAICompatibleLLMClient(
        config=config,
        api_key=settings.openai_api_key,
        api_base=settings.openai_base_url,
    )

