"""OpenRouter adapter implementing the LLMClient protocol.

Reads OPENROUTER_API_KEY from the environment via .env
"""
from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

import config  # noqa: F401

DEFAULT_MODEL = os.getenv("AGENT_MODEL", "openrouter/free").strip()


class OpenRouterClient:
    def __init__(self, model_name: str | None = None) -> None:
        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY is not set. Add it to .env"
            )
        self._model = ChatOpenAI(
            model=model_name or DEFAULT_MODEL,
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            temperature=0,
        )

    def complete(self, system: str, user: str) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage
        response = self._model.invoke(
            [SystemMessage(content=system), HumanMessage(content=user)]
        )
        return str(response.content)