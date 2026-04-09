"""OpenAI-compatible LangChain client."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from ..config.settings import ModelConfig
from .base import BaseLLMClient, SchemaT


class OpenAICompatibleLLMClient(BaseLLMClient):
    """OpenAI-compatible chat client with structured output support."""

    def __init__(self, config: ModelConfig, api_key: str | None, api_base: str | None = None) -> None:
        self._client = ChatOpenAI(
            model=config.model_name,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            api_key=api_key,
            base_url=api_base or config.api_base,
        )

    def generate_text(self, *, system_prompt: str, user_prompt: str) -> str:
        result = self._client.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
        return str(result.content)

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

