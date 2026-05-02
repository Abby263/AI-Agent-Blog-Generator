"""OpenAI-compatible LangChain client."""

from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..config.settings import ModelConfig
from .base import BaseLLMClient, SchemaT


class OpenAICompatibleLLMClient(BaseLLMClient):
    """OpenAI-compatible chat client with structured output and tool-calling support."""

    def __init__(self, config: ModelConfig, api_key: str | None, api_base: str | None = None) -> None:
        self._client = ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=api_key,
            base_url=api_base or config.api_base,
            request_timeout=120,   # 2-minute hard timeout per API call
            max_retries=2,         # fail fast rather than retry for 90+ minutes
        )

    def generate_text(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int | None = None,
    ) -> str:
        client = self._client if max_tokens is None else self._client.bind(max_tokens=max_tokens)
        result = client.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        return str(result.content)

    def as_chat_model(self) -> Any:
        """Expose the underlying LangChain chat model for DeepAgents."""

        return self._client

    def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[SchemaT],
    ) -> SchemaT:
        structured_client = self._client.with_structured_output(schema)
        return structured_client.invoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
