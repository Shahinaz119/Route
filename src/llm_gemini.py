"""Gemini adapter that implements the LLMClient protocol.

Reads GOOGLE_API_KEY and AGENT_MODEL from the environment, which config.py fills from .env.
"""
from __future__ import annotations

import os

import config  # noqa: F401  loads .env before the environment is read
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

DEFAULT_MODEL = "google_genai:gemini-3.8-flash"


class GeminiClient:
    def __init__(self, model_name: str | None = None) -> None:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                f"GOOGLE_API_KEY is not set. Add it to {config.ENV_FILE} or set it in the terminal."
            )

        raw_name = model_name or os.getenv("AGENT_MODEL", DEFAULT_MODEL)
        # Accept both "google_genai:gemini-..." and plain "gemini-...".
        name = raw_name.split(":", 1)[-1].strip()

        # temperature=0 keeps extraction and tagging as repeatable as possible.
        self._model = ChatGoogleGenerativeAI(model=name, temperature=0, google_api_key=api_key)

    def complete(self, system: str, user: str) -> str:
        response = self._model.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        content = response.content
        if isinstance(content, list):
            return "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in content)
        return str(content)