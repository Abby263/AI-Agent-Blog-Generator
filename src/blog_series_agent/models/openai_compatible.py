"""OpenAI-compatible LangChain client."""

from __future__ import annotations

import logging
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from ..config.settings import ModelConfig
from .base import BaseLLMClient, SchemaT

logger = logging.getLogger(__name__)


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

    def generate_with_tools(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        tools: list[Any],
        max_iterations: int = 6,
    ) -> str:
        """
        ReAct tool-calling loop — identical in spirit to how Claude Code uses
        Bash/Grep/Read tools.

        Each iteration:
          1. The model inspects the conversation (including prior tool results)
             and either (a) calls one or more tools, or (b) produces a final answer.
          2. If the model calls tools, we execute each one and feed the result
             back as a ToolMessage.
          3. We repeat up to *max_iterations* times, then return whatever the
             model last said.
        """
        if not tools:
            return self.generate_text(system_prompt=system_prompt, user_prompt=user_prompt)

        llm_with_tools = self._client.bind_tools(tools)
        messages: list[Any] = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        for iteration in range(max_iterations):
            response = llm_with_tools.invoke(messages)
            messages.append(response)

            tool_calls = getattr(response, "tool_calls", None) or []
            if not tool_calls:
                # Model produced a final answer — we're done.
                logger.debug("generate_with_tools: finished after %d iterations", iteration + 1)
                return str(response.content)

            # Execute every tool the model requested in this round.
            for call in tool_calls:
                tool_name = call["name"]
                tool_args = call["args"]
                tool_call_id = call["id"]

                matched = next((t for t in tools if t.name == tool_name), None)
                if matched is None:
                    result_content = f"[Error: unknown tool '{tool_name}']"
                else:
                    try:
                        result_content = matched.invoke(tool_args)
                        logger.debug(
                            "generate_with_tools: tool=%s args=%r → %d chars",
                            tool_name,
                            tool_args,
                            len(str(result_content)),
                        )
                    except Exception as exc:  # noqa: BLE001
                        result_content = f"[Tool error: {exc}]"
                        logger.warning("generate_with_tools: tool=%s failed: %s", tool_name, exc)

                messages.append(
                    ToolMessage(content=str(result_content), tool_call_id=tool_call_id)
                )

        # Exhausted iterations — return the last model message content.
        logger.warning("generate_with_tools: hit max_iterations=%d, returning last response", max_iterations)
        last = next(
            (m for m in reversed(messages) if hasattr(m, "content") and not isinstance(m, ToolMessage)),
            None,
        )
        return str(last.content) if last else ""
